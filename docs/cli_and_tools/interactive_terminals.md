# Interactive Terminals, TUI & Dashboards

TruthGPT includes a rich terminal user interface (TUI) and live monitoring dashboards for tracking training loss curves, GPU utilization, memory allocations, and agent swarm conversations in real time.

---

## 🖥️ Enhanced Dynamic Terminal (`enhanced_dynamic_terminal.py`)

Launch the full-screen dynamic terminal:

```bash
python enhanced_dynamic_terminal.py
```

### Features
- **Live Metric Gauges**: CPU, GPU VRAM, CUDA Core utilization, Loss, Tokens/sec.
- **Interactive REPL**: Directly dispatch prompts to the OpenClaw Swarm or control active training runs.
- **Log Stream Window**: Color-coded logging stream with filtering for `INFO`, `WARNING`, and `ERROR`.

---

## 📈 Real-Time Training Monitor (`utils/monitor_training.py`)

A lightweight terminal monitor that attaches to any active training run directory:

```bash
python utils/monitor_training.py runs/my_experiment_run
```

- Automatically tails training logs.
- Displays step count, learning rate, elapsed time, and ETA.
- Updates an ASCII loss progression sparkline.

---

## 🌐 Web Dashboard (`dashboard.py`)

Launch the local web-based telemetry dashboard:

```bash
python dashboard.py --port 8501
```

Provides a browser-based GUI for viewing historical runs, comparing loss curves, and inspecting saved checkpoint metadata.
