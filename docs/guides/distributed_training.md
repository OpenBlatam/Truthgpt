# Practical Guide: Distributed Training Setup

This guide provides step-by-step instructions for configuring and executing multi-GPU and multi-node distributed training using TruthGPT on cloud GPU clusters (AWS EC2, Lambda Labs, RunPod, GCP).

---

## 🛠️ Step 1: Environment & Network Preparation

Ensure all nodes have identical PyTorch and CUDA installations, and can communicate over SSH and NCCL ports (e.g. 29500).

```bash
# Verify GPU topology and NVLink bandwidth
nvidia-smi topo -m
```

---

## ⚙️ Step 2: Configure FSDP in YAML

Create `configs/cluster_fsdp_run.yaml`:

```yaml
model:
  name: "meta-llama/Llama-2-70b"
  save_safetensors: true

distributed:
  backend: "fsdp"
  sharding_strategy: "full_shard"
  mixed_precision: "bf16"
  backward_prefetch: "backward_pre"
  forward_prefetch: true
  limit_all_gathers: true

training:
  epochs: 3
  train_batch_size: 2
  grad_accum_steps: 16
  learning_rate: 1e-4

optimization:
  optimizer: "lion"
  allow_tf32: true
  torch_compile: true
```

---

## 🚀 Step 3: Launch with `torchrun`

### Single Node (8 GPUs)

```bash
torchrun --nproc_per_node=8 train_llm.py --config configs/cluster_fsdp_run.yaml
```

### Multi-Node Setup (e.g. 4 Nodes $\times$ 8 GPUs = 32 GPUs)

**On Master Node (Node 0 - IP: 10.0.0.1):**
```bash
torchrun \
    --nnodes=4 \
    --nproc_per_node=8 \
    --node_rank=0 \
    --master_addr=10.0.0.1 \
    --master_port=29500 \
    train_llm.py --config configs/cluster_fsdp_run.yaml
```

**On Worker Nodes (Node 1, 2, 3 - set `--node_rank=1`, etc.):**
```bash
torchrun \
    --nnodes=4 \
    --nproc_per_node=8 \
    --node_rank=1 \
    --master_addr=10.0.0.1 \
    --master_port=29500 \
    train_llm.py --config configs/cluster_fsdp_run.yaml
```
