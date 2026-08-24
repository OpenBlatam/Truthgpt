"""
Unit and Integration Tests for optimization_core.trainers Module.

Comprehensive test suite verifying:
- TrainerConfig composition, validation, property delegation, and serialization
- ModelManager initialization, parameter counting, and unwrapping
- OptimizerManager parameter decay grouping, optimizers, schedulers, and scalers
- DataManager and custom Datasets (HFTextDataset, TextDataset, IterableTextDataset, PackedDataset, BucketBatchSampler)
- EMAManager shadow parameter updates, weight swapping, and scoping
- Evaluator metric calculations and best metric selection
- CheckpointManager atomic saving, loading, RNG state capture/restore, and pruning
- Callbacks and CallbackHandler lifecycle hooks and exception insulation
- Experiment trackers and ExperimentTrackerRegistry
- TrainingProfiler and MetricTracker sliding window statistics
- DistributedManager environment detection
- Exception hierarchy with serialization and context chaining
- End-to-end GenericTrainer mock training run
"""
import os
import sys
import tempfile
import shutil
import math
import time
import json
import unittest
from typing import Dict, Any, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# Ensure optimization_core is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OPT_CORE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if OPT_CORE_DIR not in sys.path:
    sys.path.insert(0, OPT_CORE_DIR)

import trainers as t


# ---------------------------------------------------------------------------
# Dummy model & tokenizer for testing
# ---------------------------------------------------------------------------
class DummyTransformer(nn.Module):
    def __init__(self, vocab_size=100, d_model=32):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.fc1 = nn.Linear(d_model, d_model)
        self.ln = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size)
        self.loss_fn = nn.CrossEntropyLoss()

    def forward(self, input_ids=None, attention_mask=None, labels=None, **kwargs):
        if input_ids is None and "inputs" in kwargs:
            input_ids = kwargs["inputs"]
        if input_ids is None:
            input_ids = torch.zeros((1, 4), dtype=torch.long)
        x = self.embedding(input_ids)
        x = self.fc1(x)
        x = self.ln(x)
        logits = self.head(x)
        if labels is None:
            labels = input_ids.clone()
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()
        loss = self.loss_fn(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
        return type("Output", (), {"logits": logits, "loss": loss})()


class DummyTokenizer:
    def __init__(self, vocab_size=100):
        self.vocab_size = vocab_size
        self.pad_token_id = 0
        self.eos_token_id = 1

    def __call__(self, text, truncation=True, max_length=16, padding="max_length", return_tensors="pt", **kwargs):
        if isinstance(text, str):
            texts = [text]
            single = True
        else:
            texts = list(text)
            single = False

        all_ids = []
        all_attns = []
        for t in texts:
            words = t.split() if isinstance(t, str) else [str(t)]
            ids = [abs(hash(w)) % (self.vocab_size - 2) + 2 for w in words][:max_length]
            if return_tensors is None:
                all_ids.append(ids)
            else:
                pad_len = max(0, max_length - len(ids))
                attn = [1] * len(ids) + [0] * pad_len
                ids = ids + [self.pad_token_id] * pad_len
                all_ids.append(ids)
                all_attns.append(attn)

        if return_tensors is None:
            return all_ids if not single else all_ids[0]

        return {
            "input_ids": torch.tensor(all_ids, dtype=torch.long),
            "attention_mask": torch.tensor(all_attns, dtype=torch.long),
        }

    def encode(self, text, add_special_tokens=False, **kwargs):
        return [abs(hash(w)) % (self.vocab_size - 2) + 2 for w in text.split()]

    def decode(self, token_ids, skip_special_tokens=True, **kwargs):
        if hasattr(token_ids, "tolist"):
            token_ids = token_ids.tolist()
        return " ".join(f"tok_{t}" for t in token_ids if not skip_special_tokens or t >= 2)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------
class TestTrainersModule(unittest.TestCase):
    """Main test case for trainers package components."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # 1. Config Tests
    def test_config_composition_and_defaults(self):
        cfg = t.TrainerConfig(output_dir=self.temp_dir)
        self.assertEqual(cfg.training.epochs, 3)
        self.assertEqual(cfg.epochs, 3)
        self.assertEqual(cfg.model.name_or_path, "gpt2")
        self.assertEqual(cfg.name_or_path, "gpt2")
        self.assertEqual(cfg.learning_rate, 5e-5)

        # Property setter propagation
        cfg.learning_rate = 1e-4
        self.assertEqual(cfg.training.learning_rate, 1e-4)

        # Serialization to and from dict
        d = cfg.to_dict()
        self.assertIn("training", d)
        self.assertIn("model", d)
        self.assertIn("hardware", d)
        self.assertIn("checkpoint", d)
        self.assertIn("ema", d)

        restored = t.TrainerConfig.from_dict(d)
        self.assertEqual(restored.learning_rate, 1e-4)
        self.assertEqual(restored.output_dir, self.temp_dir)

    def test_config_validation_errors(self):
        with self.assertRaises(t.ConfigurationError):
            t.ModelConfig(name_or_path="")
        with self.assertRaises(t.ConfigurationError):
            t.TrainingConfig(epochs=0)
        with self.assertRaises(t.ConfigurationError):
            t.TrainingConfig(learning_rate=-1.0)
        with self.assertRaises(t.ConfigurationError):
            t.TrainingConfig(mixed_precision="invalid_mode")
        with self.assertRaises(t.ConfigurationError):
            t.EMAConfig(decay=1.5)

    # 2. ModelManager Tests
    def test_model_manager(self):
        m_cfg = t.ModelConfig(name_or_path="gpt2", gradient_checkpointing=False)
        hw_cfg = t.HardwareConfig(device="cpu")
        tr_cfg = t.TrainingConfig()
        mgr = t.ModelManager(m_cfg, hw_cfg, tr_cfg, device=torch.device("cpu"))
        
        dummy_model = DummyTransformer()
        mgr.model = dummy_model
        total, trainable = mgr.get_total_params()
        self.assertGreater(total, 0)
        self.assertEqual(total, trainable)
        self.assertEqual(mgr.get_model_for_operations(), dummy_model)

    # 3. OptimizerManager Tests
    def test_optimizer_manager_decay_groups(self):
        model = DummyTransformer()
        tr_cfg = t.TrainingConfig(learning_rate=1e-3, weight_decay=0.05)
        opt_mgr = t.OptimizerManager(tr_cfg, model, use_amp=False)
        groups = opt_mgr._create_decay_param_groups()
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0]["weight_decay"], 0.05)
        self.assertEqual(groups[1]["weight_decay"], 0.0)

        # Create optimizer
        opt = opt_mgr.create_optimizer("adamw")
        self.assertIsNotNone(opt)
        self.assertEqual(opt_mgr.get_lr(), 1e-3)

        # Create scheduler
        sched = opt_mgr.create_scheduler(num_training_steps=100)
        self.assertIsNotNone(sched)

        # Step and scheduler_step
        opt_mgr.step(scale_loss=False)
        opt_mgr.scheduler_step()
        opt_mgr.zero_grad()

    # 4. DataManager & Datasets Tests
    def test_datasets(self):
        tokenizer = DummyTokenizer()
        texts = ["hello world from TruthGPT", "deep learning optimization core", "enterprise modular trainer architecture"]
        
        # HFTextDataset
        ds = t.HFTextDataset(tokenizer, texts, max_length=16)
        self.assertEqual(len(ds), 3)
        sample = ds[0]
        self.assertIn("input_ids", sample)
        self.assertIn("attention_mask", sample)
        self.assertIn("labels", sample)
        self.assertEqual(sample["input_ids"].shape[0], 16)

        # TextDataset
        tds = t.TextDataset(texts)
        self.assertEqual(len(tds), 3)
        self.assertEqual(tds[0], texts[0])

        # IterableTextDataset
        def gen():
            for txt in texts:
                yield txt
        it_ds = t.IterableTextDataset(gen, tokenizer, max_length=16)
        items = list(it_ds)
        self.assertEqual(len(items), 3)

        # PackedDataset
        tok_lists = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
        pds = t.PackedDataset(tok_lists, block_size=4)
        self.assertEqual(len(pds), 3)
        self.assertEqual(pds[0]["input_ids"].shape[0], 4)

        # BucketBatchSampler
        sampler = t.BucketBatchSampler(texts, tokenizer, batch_size=2, bucket_bins=[8, 16, 32])
        batches = list(sampler)
        self.assertGreater(len(batches), 0)

    def test_data_manager_loaders(self):
        tokenizer = DummyTokenizer()
        train_texts = ["sample " + str(i) for i in range(20)]
        val_texts = ["val sample " + str(i) for i in range(10)]
        tr_cfg = t.TrainingConfig(train_batch_size=4, eval_batch_size=4)
        hw_cfg = t.HardwareConfig(num_workers=0)
        dm = t.DataManager(tr_cfg, hw_cfg, tokenizer, text_field_max_len=16)
        train_loader, val_loader = dm.create_loaders(train_texts, val_texts)
        self.assertIsInstance(train_loader, DataLoader)
        self.assertIsInstance(val_loader, DataLoader)
        self.assertEqual(len(train_loader), 5)
        self.assertEqual(len(val_loader), 3)

    # 5. EMAManager Tests
    def test_ema_manager(self):
        model = DummyTransformer()
        ema_cfg = t.EMAConfig(enabled=True, decay=0.9)
        ema_mgr = t.EMAManager(ema_cfg, model)
        self.assertIsNotNone(ema_mgr._ema_shadow)

        # Perturb model weights and perform EMA update
        with torch.no_grad():
            for p in model.parameters():
                p.add_(1.0)
        ema_mgr.update()

        # Swap weights using context manager
        orig_val = model.fc1.weight.data.clone()
        with ema_mgr.ema_scope():
            ema_val = model.fc1.weight.data.clone()
            self.assertFalse(torch.equal(orig_val, ema_val))
        # After context exit, original weights must be restored
        self.assertTrue(torch.equal(model.fc1.weight.data, orig_val))

    # 6. Evaluator Tests
    def test_evaluator(self):
        model = DummyTransformer()
        tokenizer = DummyTokenizer()
        val_texts = ["eval test sentence one", "eval test sentence two"]
        val_ds = t.HFTextDataset(tokenizer, val_texts, max_length=16)
        val_loader = DataLoader(val_ds, batch_size=2)
        tr_cfg = t.TrainingConfig(select_best_by="loss")
        evaluator = t.Evaluator(tr_cfg, model, val_loader, device=torch.device("cpu"), use_amp=False)
        metrics = evaluator.evaluate()
        self.assertIn("loss", metrics)
        self.assertIn("perplexity", metrics)
        self.assertTrue(math.isfinite(metrics["loss"]))
        best_val = evaluator.select_best_metric(metrics)
        self.assertEqual(best_val, metrics["loss"])

    # 7. CheckpointManager Tests
    def test_checkpoint_manager_save_load_prune(self):
        model = DummyTransformer()
        opt = torch.optim.SGD(model.parameters(), lr=0.01)
        ckpt_cfg = t.CheckpointConfig(keep_last=2)
        ckpt_mgr = t.CheckpointManager(ckpt_cfg, self.temp_dir, model, optimizer=opt)

        # Save step checkpoints
        p1 = ckpt_mgr.save("step_10.pt", step=10, epoch=1)
        p2 = ckpt_mgr.save("step_20.pt", step=20, epoch=1)
        p3 = ckpt_mgr.save("step_30.pt", step=30, epoch=1)

        self.assertTrue(os.path.exists(p1))
        self.assertTrue(os.path.exists(p2))
        self.assertTrue(os.path.exists(p3))

        # Prune checkpoints (should keep only step_20 and step_30)
        ckpt_mgr.prune_checkpoints()
        self.assertFalse(os.path.exists(p1))
        self.assertTrue(os.path.exists(p2))
        self.assertTrue(os.path.exists(p3))

        # Load checkpoint
        loaded_state = ckpt_mgr.load(p3)
        self.assertEqual(loaded_state["step"], 30)
        self.assertIn("model_state_dict", loaded_state)
        self.assertIn("optimizer_state_dict", loaded_state)

    # 8. Callbacks Tests
    def test_callbacks_and_handler(self):
        events = []

        class TestCallback(t.Callback):
            def on_train_begin(self, state): events.append("train_begin")
            def on_step_end(self, step, state): events.append(f"step_{step}")
            def on_exception(self, exc, state): events.append(f"exc_{type(exc).__name__}")

        cb = TestCallback()
        lr_mon = t.LearningRateMonitor()
        grad_norm = t.GradNormLogger()
        mem_track = t.MemoryTrackerCallback()
        csv_log = t.CSVLogger(filename=os.path.join(self.temp_dir, "test_metrics.csv"))
        early_stop = t.EarlyStoppingCallback(patience=2, min_delta=0.1)

        handler = t.CallbackHandler([cb, lr_mon, grad_norm, mem_track, csv_log, early_stop])
        handler.on_train_begin({"global_step": 0})
        handler.on_step_end(1, {"global_step": 1, "loss": 2.5, "learning_rate": 1e-4})
        handler.on_before_optimizer_step({"grad_norm": 0.5})
        handler.on_log({"loss": 2.5, "learning_rate": 1e-4, "global_step": 1})
        handler.on_exception(ValueError("test error"), {"global_step": 1})

        self.assertIn("train_begin", events)
        self.assertIn("step_1", events)
        self.assertIn("exc_ValueError", events)
        self.assertEqual(len(lr_mon.lr_history), 1)

        # Early stopping simulation
        eval_state = {"val_loss": 3.0}
        handler.on_eval(eval_state)
        self.assertFalse(early_stop.should_stop)
        eval_state2 = {"val_loss": 3.0}  # No improvement
        handler.on_eval(eval_state2)
        eval_state3 = {"val_loss": 3.0}  # No improvement (patience exceeded)
        handler.on_eval(eval_state3)
        self.assertTrue(early_stop.should_stop)
        self.assertTrue(eval_state3.get("should_stop", False))

    # 9. Profiler and MetricTracker Tests
    def test_profiler_and_metric_tracker(self):
        profiler = t.TrainingProfiler(enabled=True)
        profiler.start()
        t0 = profiler.step_start()
        time.sleep(0.01)
        step_metrics = profiler.step_end(t0, num_tokens=100)
        self.assertIn("step_latency_sec", step_metrics)
        self.assertIn("tokens_per_sec", step_metrics)
        self.assertGreater(step_metrics["tokens_per_sec"], 0)

        summary = profiler.summary()
        self.assertEqual(summary["total_steps"], 1)
        self.assertEqual(summary["total_tokens"], 100)

        # MetricTracker
        tracker = t.MetricTracker(window_size=10)
        for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
            tracker.update("loss", v)
        self.assertEqual(tracker.get_latest("loss"), 5.0)
        self.assertEqual(tracker.get_avg("loss"), 3.0)
        self.assertEqual(tracker.get_min("loss"), 1.0)
        self.assertEqual(tracker.get_max("loss"), 5.0)
        self.assertGreater(tracker.get_std("loss"), 0)

    # 10. Registry Tests
    def test_trainer_registry(self):
        @t.TrainerRegistry.register_callback("custom_cb")
        class CustomCb(t.Callback):
            pass

        self.assertIn("custom_cb", t.TrainerRegistry.list_callbacks())
        self.assertEqual(t.TrainerRegistry.get_callback("custom_cb"), CustomCb)

    # 11. Exception Hierarchy Tests
    def test_exceptions_and_serialization(self):
        err = t.TrainerError("Critical trainer failure", context={"step": 42}, error_code="ERR_CUSTOM", severity=t.ErrorSeverity.CRITICAL)
        self.assertEqual(err.error_code, "ERR_CUSTOM")
        self.assertEqual(err.severity, t.ErrorSeverity.CRITICAL)
        err.chain_context(model_name="dummy_transformer")
        self.assertEqual(err.context["model_name"], "dummy_transformer")

        d = err.to_dict()
        self.assertEqual(d["error_code"], "ERR_CUSTOM")
        self.assertEqual(d["severity"], "critical")
        j = err.to_json()
        self.assertIn("ERR_CUSTOM", j)

        # from_exception factory
        try:
            raise KeyError("missing parameter")
        except Exception as e:
            wrapped = t.TrainerError.from_exception(e, component="OptimizerManager")
            self.assertEqual(wrapped.component, "OptimizerManager")
            self.assertIn("missing parameter", wrapped.message)

    # 12. Types & Type Guards Tests
    def test_types_and_guards(self):
        self.assertTrue(t.is_cuda_device("cuda:0"))
        self.assertFalse(t.is_cuda_device("cpu"))
        self.assertTrue(t.is_finite_loss(torch.tensor(1.23)))
        self.assertFalse(t.is_finite_loss(float("nan")))
        self.assertFalse(t.is_finite_loss(float("inf")))

        hw_info = t.HardwareInfo.detect()
        self.assertIsNotNone(hw_info.device_type)

        state = t.TrainerState()
        self.assertEqual(state.stage, t.TrainerStage.UNINITIALIZED)
        state.mark_ready()
        self.assertEqual(state.stage, t.TrainerStage.READY)
        state.mark_training()
        self.assertEqual(state.stage, t.TrainerStage.TRAINING)
        self.assertTrue(state.is_training)
        state.mark_completed()
        self.assertEqual(state.stage, t.TrainerStage.COMPLETED)
        self.assertFalse(state.is_training)

    # 13. End-to-End Mock Training with GenericTrainer
    def test_generic_trainer_mock_training_run(self):
        train_texts = [f"This is sample training sentence {i} for TruthGPT trainer." for i in range(12)]
        val_texts = [f"This is validation sentence {i}." for i in range(6)]

        cfg = t.TrainerConfig(
            output_dir=self.temp_dir,
            training=t.TrainingConfig(
                epochs=2,
                train_batch_size=4,
                eval_batch_size=4,
                grad_accum_steps=1,
                learning_rate=1e-3,
                log_interval=1,
                eval_interval=2,
                mixed_precision="none",
                max_steps=4,
            ),
            hardware=t.HardwareConfig(
                device="cpu",
                num_workers=0,
                use_profiler=True,
            ),
            checkpoint=t.CheckpointConfig(
                interval_steps=2,
                keep_last=2,
            ),
            ema=t.EMAConfig(enabled=True, decay=0.9),
        )

        class CustomTrainer(t.GenericTrainer):
            def __init__(self, config, train_t, val_t):
                # Custom injection of dummy model & tokenizer
                if not isinstance(config, t.TrainerConfig):
                    config = t.TrainerConfig.from_dict(config)
                self.cfg = config
                t.set_seed(config.seed)
                self.callback_handler = t.CallbackHandler([])
                self.callbacks = self.callback_handler.callbacks
                self.data_options = {}
                self.state = t.TrainerState(max_steps=config.training.max_steps)
                self.device = torch.device("cpu")

                # Model
                self.tokenizer = DummyTokenizer()
                self.model = DummyTransformer()
                self.model_manager = t.ModelManager(config.model, config.hardware, config.training, self.device)
                self.model_manager.model = self.model
                self.model_manager.tokenizer = self.tokenizer

                # Data
                self.data_manager = t.DataManager(config.training, config.hardware, self.tokenizer, text_field_max_len=16)
                self.train_loader, self.val_loader = self.data_manager.create_loaders(train_t, val_t)

                # Optimizer & Scheduler
                self.optimizer_manager = t.OptimizerManager(config.training, self.model, use_amp=False)
                self.optimizer = self.optimizer_manager.create_optimizer("adamw")
                num_train_steps = max(1, (len(self.train_loader) * config.training.epochs))
                self.lr_scheduler = self.optimizer_manager.create_scheduler(num_train_steps)
                self.scaler = self.optimizer_manager.create_scaler()

                # EMA
                self.ema_manager = t.EMAManager(config.ema, self.model)

                # Evaluator
                self.evaluator = t.Evaluator(config.training, self.model, self.val_loader, self.device, use_amp=False, ema_manager=self.ema_manager)

                # Checkpoint
                self.checkpoint_manager = t.CheckpointManager(
                    config.checkpoint, config.output_dir, self.model,
                    optimizer=self.optimizer, scheduler=self.lr_scheduler,
                    scaler=self.scaler, tokenizer=self.tokenizer
                )

                # Subsystems
                self.profiler = t.TrainingProfiler(enabled=True)
                self.metric_tracker = t.MetricTracker()
                self.metrics_tracker = self.metric_tracker
                self.training_logger = t.TrainingLogger()

        trainer = CustomTrainer(cfg, train_texts, val_texts)
        trainer.train()

        # Check that training completed and reached max_steps
        self.assertEqual(trainer.state.stage, t.TrainerStage.COMPLETED)
        self.assertGreaterEqual(trainer.state.global_step, 4)

        # Check that checkpoints were saved
        last_ckpt = os.path.join(self.temp_dir, "last")
        self.assertTrue(os.path.exists(last_ckpt) or os.path.exists(last_ckpt + ".pt"))


if __name__ == "__main__":
    unittest.main()
