"""
🧪 Unit Tests - TruthGPT Cloud Storage & Subscription Schema Enhancements
Validates:
1. High-speed orjson acceleration in AtomicJsonStorage & JsonFileStorageBackend
2. Transactional ACID SQLite persistence with SqliteStorageBackend
3. Pydantic v2 canonical schemas for user accounts, quotas, and subscriptions database
"""

import os
import json
import time

from truthgpt_cloud.storage.atomic import AtomicJsonStorage, _HAS_ORJSON
from truthgpt_cloud.storage.json_storage import JsonFileStorageBackend
from truthgpt_cloud.storage.sqlite_storage import SqliteStorageBackend
from truthgpt_cloud.core.schemas import (
    UserSubscriptionSchema,
    validate_subscription_db,
)
from truthgpt_cloud.billing.models import UserSubscription, UsageRecord
from truthgpt_cloud.core.tiers import CloudTier


class TestOrjsonStorageAcceleration:
    """Validate orjson acceleration and atomic file operations."""

    def test_01_has_orjson_active(self):
        assert _HAS_ORJSON is True

    def test_02_atomic_json_storage_roundtrip(self, tmp_path):
        target_file = tmp_path / "test_subs.json"
        storage = AtomicJsonStorage(str(target_file))

        # Initial load on missing file returns empty dict
        assert storage.load() == {}

        sample_data = {
            "usr_demo_1": {
                "user_id": "usr_demo_1",
                "email": "demo1@truthgpt.ai",
                "tier": "pro",
                "api_keys": ["tgpt_cloud_live_demo123"],
                "usage": {"total_tokens_consumed": 15000}
            },
            "usr_demo_2": {
                "user_id": "usr_demo_2",
                "email": "demo2@truthgpt.ai",
                "tier": "ultra",
                "api_keys": ["tgpt_cloud_live_demo456"],
                "usage": {"total_tokens_consumed": 98000}
            }
        }

        # Save data
        saved = storage.save(sample_data)
        assert saved is True
        assert target_file.exists()

        # Load back
        loaded = storage.load()
        assert loaded == sample_data
        assert loaded["usr_demo_1"]["email"] == "demo1@truthgpt.ai"

    def test_03_json_file_storage_backend_with_orjson(self, tmp_path):
        target_file = tmp_path / "backend_subs.json"
        backend = JsonFileStorageBackend(str(target_file), debounce_ms=50)

        # Set records
        backend.set("users", "usr_100", {"name": "Alice", "tokens": 500})
        backend.set("users", "usr_200", {"name": "Bob", "tokens": 1200})

        assert backend.get("users", "usr_100") == {"name": "Alice", "tokens": 500}
        assert backend.get("users", "usr_200") == {"name": "Bob", "tokens": 1200}
        assert backend.get("users", "usr_nonexistent") is None

        # Wait for debounce flush (poll up to 500ms)
        for _ in range(20):
            if target_file.exists():
                break
            time.sleep(0.025)
        assert target_file.exists()

        # Check deletion
        deleted = backend.delete("users", "usr_100")
        assert deleted is True
        assert backend.get("users", "usr_100") is None


class TestSqliteStorageBackend:
    """Validate ACID transactional persistence with SqliteStorageBackend."""

    def test_01_sqlite_crud_operations(self, tmp_path):
        db_file = tmp_path / "cloud_test.db"
        storage = SqliteStorageBackend(str(db_file))

        # Test set and get
        storage.set("users", "usr_01", {"email": "user1@truthgpt.ai", "tier": "free"})
        storage.set("users", "usr_02", {"email": "user2@truthgpt.ai", "tier": "pro"})

        rec1 = storage.get("users", "usr_01")
        assert rec1 is not None
        assert rec1["email"] == "user1@truthgpt.ai"
        assert rec1["tier"] == "free"

        # Update record
        storage.set("users", "usr_01", {"email": "user1_updated@truthgpt.ai", "tier": "ultra"})
        rec1_up = storage.get("users", "usr_01")
        assert rec1_up["tier"] == "ultra"

        # Get all
        all_users = storage.get_all("users")
        assert len(all_users) == 2
        assert "usr_01" in all_users
        assert "usr_02" in all_users

        # Delete
        del_res = storage.delete("users", "usr_02")
        assert del_res is True
        assert storage.get("users", "usr_02") is None
        assert len(storage.get_all("users")) == 1

    def test_02_sqlite_set_all_and_snapshot(self, tmp_path):
        db_file = tmp_path / "cloud_snapshot.db"
        storage = SqliteStorageBackend(str(db_file))

        batch = {
            f"usr_{i}": {"name": f"User {i}", "quota": i * 1000}
            for i in range(25)
        }
        storage.set_all("subscribers", batch)
        assert len(storage.get_all("subscribers")) == 25

        # Create snapshot
        snap = storage.create_snapshot()
        assert os.path.exists(snap)
        assert os.path.getsize(snap) > 0

    def test_03_sqlite_json_migration(self, tmp_path):
        db_file = tmp_path / "migrated.db"
        json_file = tmp_path / "source.json"
        export_file = tmp_path / "exported.json"

        # Create JSON file
        sample_json_data = {
            "usr_alice": {"name": "Alice", "tier": "ultra"},
            "usr_bob": {"name": "Bob", "tier": "enterprise"},
        }
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(sample_json_data, f)

        storage = SqliteStorageBackend(str(db_file))
        imported_count = storage.import_from_json("accounts", str(json_file))
        assert imported_count == 2
        assert storage.get("accounts", "usr_alice")["name"] == "Alice"

        # Export back to JSON
        exported_count = storage.export_to_json("accounts", str(export_file))
        assert exported_count == 2
        assert export_file.exists()
        with open(export_file, encoding="utf-8") as f:
            exported_data = json.load(f)
        assert exported_data == sample_json_data


class TestPydanticV2SubscriptionSchemas:
    """Validate canonical Pydantic v2 schemas for subscriptions and account databases."""

    def test_01_user_subscription_schema_validation(self):
        user_raw = {
            "user_id": "usr_998877",
            "email": "dev@truthgpt.ai",
            "name": "Dev Account",
            "tier": "pro",
            "billing_cycle": "yearly",
            "status": "active",
            "api_keys": ["tgpt_cloud_live_abcdef123456"],
            "subscription_start_date": "2026-08-28T21:32:20.778825+00:00",
            "next_billing_date": "2027-08-28T21:32:20.778825+00:00",
            "usage": {
                "total_tokens_consumed": 25000,
                "tokens_consumed_today": 1200,
                "verifications_run": 15,
                "swarm_sessions_count": 2,
                "last_reset_timestamp": 1787952740.0,
                "daily_request_count": 8,
                "purchased_tokens_balance": 0,
                "total_purchased_tokens": 0
            },
            "invoices": [
                {
                    "invoice_id": "inv_001",
                    "user_id": "usr_998877",
                    "tier_id": "pro",
                    "amount_usd": 190.0,
                    "billing_cycle": "yearly",
                    "payment_method": "stripe_card",
                    "status": "paid",
                    "discount_applied_usd": 10.0,
                    "promo_code": "LAUNCH_PRO"
                }
            ],
            "api_key_details": [
                {
                    "key": "tgpt_cloud_live_abcdef123456",
                    "key_id": "key_01",
                    "key_prefix": "tgpt_cloud_live_...",
                    "label": "Production Key",
                    "name": "Production Key",
                    "is_active": True,
                    "scopes": ["all"]
                }
            ],
            "webhooks": [],
            "custom_limits": None
        }

        schema = UserSubscriptionSchema.model_validate(user_raw)
        assert schema.user_id == "usr_998877"
        assert schema.tier == "pro"
        assert schema.usage.total_tokens_consumed == 25000
        assert len(schema.invoices) == 1
        assert schema.invoices[0].amount_usd == 190.0

        # Convert to domain UserSubscription
        domain_user = schema.to_domain()
        assert isinstance(domain_user, UserSubscription)
        assert domain_user.tier == CloudTier.PRO
        assert isinstance(domain_user.usage, UsageRecord)
        assert domain_user.usage.verifications_run == 15

        # Convert back
        schema2 = UserSubscriptionSchema.from_domain(domain_user)
        assert schema2.user_id == schema.user_id
        assert schema2.email == schema.email

    def test_02_validate_subscription_db(self):
        db_raw = {
            "usr_01": {
                "user_id": "usr_01",
                "email": "user1@truthgpt.ai",
                "tier": "free",
                "usage": {"total_tokens_consumed": 500}
            },
            "usr_02": {
                "user_id": "usr_02",
                "email": "user2@truthgpt.ai",
                "tier": "ultra",
                "usage": {"total_tokens_consumed": 89000}
            }
        }
        validated = validate_subscription_db(db_raw)
        assert len(validated) == 2
        assert "usr_01" in validated
        assert "usr_02" in validated
        assert validated["usr_01"].tier == "free"
        assert validated["usr_02"].tier == "ultra"
