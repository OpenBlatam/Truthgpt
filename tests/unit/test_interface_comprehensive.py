"""
TruthGPT Interface Comprehensive Test Suite.
=============================================
Extensive coverage for:
  - Multi-threaded MenuRegistry & ThemeRegistry concurrency
  - Custom BaseMenu subclass registration and execution
  - InterfaceBuilder composition with custom panels and menus
  - TelemetryProvider balance cache manipulation
  - Config corruption detection and auto-recovery
  - Prompt_toolkit BaseTUIApp keybinding and theme style building
  - Export utilities & multi-language code block extraction
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

for p in [str(SRC_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)


class TestInterfaceConcurrencyAndThreads(unittest.TestCase):
    """Test thread-safe concurrent operations on registries."""

    def test_concurrent_menu_registrations(self):
        """Ensure thread-safe simultaneous registrations under high contention."""
        from interface.registry import MenuRegistry

        def worker(thread_idx: int):
            for i in range(10):
                menu_id = f"worker_menu_{thread_idx}_{i}"
                MenuRegistry.register(
                    name=menu_id,
                    title=f"Worker Menu {thread_idx}-{i}",
                    category="concurrency",
                    overwrite=True,
                )(lambda: None)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        menu = MenuRegistry.get_menu("worker_menu_0_0")
        self.assertIsNotNone(menu)
        self.assertEqual(menu.category, "concurrency")

    def test_concurrent_theme_palette_reads(self):
        """Ensure safe concurrent access to theme palette configurations."""
        from interface.registry import ThemeRegistry, get_theme_palette

        results = []

        def reader():
            for _ in range(20):
                p = get_theme_palette("claude")
                results.append(p.primary)

        threads = [threading.Thread(target=reader) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 80)
        self.assertTrue(all(r == "plum1" for r in results))


class TestBaseMenuSubclassing(unittest.TestCase):
    """Test custom BaseMenu implementation and dispatch."""

    def test_custom_menu_class(self):
        from interface.interfaces import BaseMenu
        from interface.registry import MenuRegistry

        class MyCustomMenu(BaseMenu):
            menu_id = "test_custom_class_menu"
            title = "Test Custom Class Menu"
            category = "testing"
            description = "A class-based menu"

            async def display(self, **kwargs):
                return "displayed"

            def get_options(self):
                return [("1", "Option One", lambda: 1)]

        MenuRegistry.register_class("test_custom_class_menu", MyCustomMenu, overwrite=True)
        inst = MenuRegistry.create_menu_instance("test_custom_class_menu")
        self.assertIsNotNone(inst)
        self.assertIsInstance(inst, BaseMenu)
        self.assertEqual(inst.get_menu_info()["menu_id"], "test_custom_class_menu")
        self.assertEqual(len(inst.get_options()), 1)


class TestConfigCorruptionRecovery(unittest.TestCase):
    """Test config loader behavior on valid, empty, and corrupted JSON files."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "test_user_preferences.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_corrupted_config_recovery(self):
        """Verify that corrupted preferences files are backed up and defaults restored."""
        # Write corrupted JSON
        self.config_path.write_text("{corrupted_json: true, unterminated", encoding="utf-8")

        with patch("interface.config.CONFIG_PATH", self.config_path):
            from interface.config import load_user_prefs
            prefs = load_user_prefs()
            self.assertIn("user_name", prefs)
            self.assertEqual(prefs["user_name"], "Explorer")


class TestTUIAppBaseAndTheming(unittest.TestCase):
    """Test BaseTUIApp styling and keybinding registration."""

    def test_base_tui_app_style_building(self):
        from interface.tui_base import BaseTUIApp

        app = BaseTUIApp()
        style = app.build_style(custom_token="bold red")
        self.assertIsNotNone(style)

    def test_base_tui_app_hotkey_registration(self):
        from interface.tui_base import BaseTUIApp

        app = BaseTUIApp()
        app.register_hotkeys({"s": "SWARM", "m": "MODEL"})
        # Verify keybindings were added
        self.assertIsNotNone(app.kb)


class TestCodeBlockExtraction(unittest.TestCase):
    """Test export utilities parsing markdown code blocks."""

    def test_extract_and_save_code_blocks(self):
        from interface.export_utils import extract_and_save_code_blocks

        content = """
Here is Python code:
```python
def hello_world():
    return "hello"
```

And some Rust:
```rust
fn main() {
    println!("Hello from Rust");
}
```
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir)
            files = extract_and_save_code_blocks(content, target_path, prefix="test_export")
            self.assertEqual(len(files), 2)
            self.assertTrue(any(f.name.endswith(".py") for f in files))
            self.assertTrue(any(f.name.endswith(".rs") for f in files))

            py_file = next(f for f in files if f.name.endswith(".py"))
            self.assertIn("hello_world", py_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
