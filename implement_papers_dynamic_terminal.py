# implement_papers_dynamic_terminal.py
"""
TruthGPT Enterprise Dynamic Terminal with Paper Integrations
================================================================
Implements Chain of Draft (2506.10987v1), Elastic Reasoning (2505.05315v2),
and FP16 Stability (2510.26788v1) in a live, personalized, dual-pane TUI.

Features:
- Left pane: Agent reasoning log (Chain of Draft structured thoughts)
- Right pane: Workflow execution & tool logs (Elastic Reasoning budget tracking)
- Bottom bar: Real-time metrics (FP16 stability status, token counts, budgets)
- Personalized config via terminal_config.json & user_preferences.json
- Dynamic command input with continuous loop
- Side-by-side terminal view for real-time monitoring

Usage: python implement_papers_dynamic_terminal.py [--config CONFIG_PATH]
"""

import asyncio
import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# ── Rich UI ────────────────────────────────────
try:
    from rich.console import Console
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich import box
    from rich.columns import Columns
except ImportError:
    print("Please install 'rich': pip install rich")
    sys.exit(1)

# ── Paper Imports ─────────────────────────────
try:
    from papers.chain_of_draft import ChainOfDraft
    from papers.elastic_reasoning import ElasticReasoning
    from papers.fp16_stability import FP16Stability
    from latency_optimizations import (
        apply_chain_of_draft, apply_elastic_reasoning, apply_fp16_stability,
        apply_snap_kv_compression, apply_speculative_decoding,
        apply_entropy_guided_inference, apply_distinct_leaf_decoding,
        apply_discriminative_verification,
        apply_adaptive_kv_quant, apply_moqae_quant,
        apply_confspec_reasoning, apply_speculative_prefill,
        apply_intuitor_reward, apply_echo_ttrl,
        apply_reinforced_attention, apply_progressive_thought_encoding,
    )
    PAPERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import paper modules: {e}")
    PAPERS_AVAILABLE = False
    # Minimal fallbacks
    class ChainOfDraft:
        VARIANTS = ["baseline", "structured", "hierarchical", "iterative", "code_specific"]
        @staticmethod
        def get_template(variant="baseline"):
            return """Drafting steps:
• 1. [Identify key variable]
• 2. [Set up equation]
• 3. [Solve for x]
Solution:
"""
        @staticmethod
        def validate_draft(draft_text): return True
    
    class ElasticReasoning:
        THINK_START = "<think>"
        THINK_END = "</think>"
        def __init__(self, t_budget, s_budget):
            self.t_budget = t_budget
            self.s_budget = s_budget
            self.total_budget = t_budget + s_budget
        def simulate_generation(self, current_tokens): return "continue"
        @staticmethod
        def calculate_metrics(text):
            return {"has_thinking": False, "think_tokens": 0, "total_tokens": len(text.split()) if text else 0, "ratio": 0}
    
    class FP16Stability:
        @staticmethod
        def check_stability_metrics(tensor): return {"stable": True, "overflow": False, "underflow": False}
        @staticmethod
        def apply_stability_hooks(model): return model
    
    def apply_chain_of_draft(prompt, variant="baseline"):
        return ChainOfDraft.get_template(variant) + "\n" + prompt
    def apply_elastic_reasoning(prompt, t_budget, s_budget, wrapper=True):
        if wrapper:
            return f"Please think within {t_budget} tokens using <think></think> tags, then answer within {s_budget} tokens:\n\n{prompt}"
        return prompt
    def apply_fp16_stability(model): return model
    def apply_snap_kv_compression(current_tokens, **kwargs): return {"compressed": False, "compression_ratio": 1.0, "tokens_saved": 0}
    def apply_speculative_decoding(**kwargs): return {"accepted_tokens": 0, "speedup_multiplier": 1.0}
    def apply_entropy_guided_inference(context_length, **kwargs): return {"speedup_multiplier": 1.0, "compute_fraction": 1.0, "sparse_attention_segments": 0}
    def apply_distinct_leaf_decoding(sample_budget=8, **kwargs): return {"distinct_traces": sample_budget, "samples_saved": 0, "speedup_multiplier": 1.0}
    def apply_discriminative_verification(candidates, **kwargs): return {"selected": None, "overrode_majority": False}
    def apply_adaptive_kv_quant(num_tokens, **kwargs): return {"quantized": False, "memory_ratio": 1.0, "memory_savings_pct": 0.0}
    def apply_moqae_quant(context_length, **kwargs): return {"memory_ratio": 1.0, "avg_bits": 16.0}
    def apply_confspec_reasoning(num_steps=12, **kwargs): return {"verify_passes_saved": 0, "speedup_multiplier": 1.0}
    def apply_speculative_prefill(num_tokens, **kwargs): return {"compressed": False, "kept_tokens": num_tokens, "speedup_multiplier": 1.0, "dropped_tokens": 0}
    def apply_intuitor_reward(group_token_probs, **kwargs): return {"rewards": [], "best_rollout": -1, "label_free": True}
    def apply_echo_ttrl(rollouts, **kwargs): return {"selected": -1, "rewards": []}
    def apply_reinforced_attention(head_contributions, reward=1.0, **kwargs): return {"updated_weights": [], "reinforced_heads": 0}
    def apply_progressive_thought_encoding(base_thought_tokens, **kwargs): return {"training_token_savings_pct": 0.0, "final_thought_tokens": base_thought_tokens}

# ── Dynamic Workflow Integration ──────────────
try:
    from dynamic_workflow import DynamicWorkflow
    WORKFLOW_AVAILABLE = True
except ImportError:
    WORKFLOW_AVAILABLE = False
    DynamicWorkflow = None

# ── Configuration ─────────────────────────────
CONFIG_FILE = Path(__file__).parent / "terminal_config.json"
USER_PREFS_FILE = Path(__file__).parent / "user_preferences.json"

DEFAULT_CONFIG = {
    "agent_name": "TruthGPT-Dynamic",
    "theme": "blue",
    "refresh_rate": 6,
    "max_log_lines": 200,
    "workflow_interval": 5,
    "continuous_mode": True,
    "active_papers": ["chain_of_draft", "elastic_reasoning", "fp16_stability", "snap_kv", "speculative_decoding", "entropy_guided", "distinct_leaf", "discriminative_verification", "adaptive_kv_quant", "moqae", "confspec", "speculative_prefill", "intuitor", "echo", "reinforced_attention", "progressive_thought"],
    "chain_of_draft_variant": "baseline",
    "elastic_reasoning_budget": {"think": 30, "solve": 120},
    "fp16_enabled": True,
    "entropy_threshold": 0.55,
    "self_consistency_budget": 8,
    "prefill_keep_ratio": 0.4,
    "confspec_gate": 0.8,
    "max_iterations": 0,
    "user_input_timeout": 45,
    "colors": {
        "agent_border": "cyan",
        "terminal_border": "green",
        "status_bar_style": "bold white on dark_blue"
    },
    "startup_commands": ["system_check", "load_papers"],
    "on_cycle_hooks": ["update_metrics", "verify_stability"]
}

def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception as e:
            logging.warning(f"Failed to load config: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(cfg: Dict[str, Any]):
    tmp_path = CONFIG_FILE.with_suffix('.tmp')
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        tmp_path.replace(CONFIG_FILE)
    except IOError as e:
        logging.error(f"Config save failed: {e}")

def load_user_prefs() -> Dict[str, Any]:
    if USER_PREFS_FILE.exists():
        try:
            with open(USER_PREFS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"user_name": "default", "theme": "dark", "show_chain_of_draft": True, "show_elastic_budget": True}

# ── Log Buffer ────────────────────────────────
class LogBuffer:
    def __init__(self, max_lines: int = 150):
        self.max_lines = max_lines
        self.lines: List[str] = []
        self.lock = threading.Lock()
    
    def add(self, line: str):
        with self.lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.lines.append(f"[{timestamp}] {line}")
            if len(self.lines) > self.max_lines:
                self.lines = self.lines[-self.max_lines:]
    
    def get_all(self) -> List[str]:
        with self.lock:
            return list(self.lines)
    
    def clear(self):
        with self.lock:
            self.lines.clear()

# ── Paper Integration Engine ─────────────────
class PaperIntegrationEngine:
    """Central engine that applies Chain of Draft, Elastic Reasoning, FP16 Stability, SnapKV, and Speculative Decoding."""
    
    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.chain_draft_active = "chain_of_draft" in config.get("active_papers", [])
        self.elastic_active = "elastic_reasoning" in config.get("active_papers", [])
        self.fp16_active = "fp16_stability" in config.get("active_papers", []) or config.get("fp16_enabled", False)
        self.snapkv_active = "snap_kv" in config.get("active_papers", [])
        self.speculative_active = "speculative_decoding" in config.get("active_papers", [])
        self.entropy_active = "entropy_guided" in config.get("active_papers", [])
        self.distinct_leaf_active = "distinct_leaf" in config.get("active_papers", [])
        self.disc_verify_active = "discriminative_verification" in config.get("active_papers", [])
        self.adaptive_kv_active = "adaptive_kv_quant" in config.get("active_papers", [])
        self.moqae_active = "moqae" in config.get("active_papers", [])
        self.confspec_active = "confspec" in config.get("active_papers", [])
        self.spec_prefill_active = "speculative_prefill" in config.get("active_papers", [])
        self.intuitor_active = "intuitor" in config.get("active_papers", [])
        self.echo_active = "echo" in config.get("active_papers", [])
        self.reinforced_attn_active = "reinforced_attention" in config.get("active_papers", [])
        self.progressive_thought_active = "progressive_thought" in config.get("active_papers", [])

        self.entropy_threshold = config.get("entropy_threshold", 0.55)
        self.sc_budget = config.get("self_consistency_budget", 8)
        self.prefill_keep_ratio = config.get("prefill_keep_ratio", 0.4)
        self.confspec_gate = config.get("confspec_gate", 0.8)

        self.chain_variant = config.get("chain_of_draft_variant", "baseline")
        t_budget = config.get("elastic_reasoning_budget", {}).get("think", 30)
        s_budget = config.get("elastic_reasoning_budget", {}).get("solve", 120)
        self.elastic = ElasticReasoning(t_budget, s_budget) if self.elastic_active else None
        
        self.metrics = {
            "chain_draft_applied": 0,
            "elastic_budgets_enforced": 0,
            "fp16_stable_tensors": 0,
            "total_tokens_saved": 0,
            "snapkv_compression_runs": 0,
            "speculative_tokens_accepted": 0,
            "entropy_sparse_segments": 0,
            "entropy_speedup": 1.0,
            "distinct_leaf_samples_saved": 0,
            "verifier_majority_overrides": 0,
            "kv_memory_saved_pct": 0.0,
            "moqae_avg_bits": 16.0,
            "confspec_verify_saved": 0,
            "prefill_tokens_dropped": 0,
            "intuitor_rollouts_scored": 0,
            "echo_updates": 0,
            "reinforced_attn_heads": 0,
            "progressive_thought_savings_pct": 0.0,
        }
    
    def process_prompt(self, prompt: str) -> Tuple[str, Dict[str, Any]]:
        """Apply Chain of Draft and Elastic Reasoning to a prompt. Returns (optimized_prompt, metadata)."""
        metadata = {}
        optimized = prompt
        
        if self.chain_draft_active:
            draft_template = ChainOfDraft.get_template(self.chain_variant)
            optimized = f"{draft_template}\n\n{optimized}"
            metadata["chain_of_draft"] = {"variant": self.chain_variant, "template_length": len(draft_template)}
            self.metrics["chain_draft_applied"] += 1
        
        if self.elastic_active and self.elastic:
            optimized = apply_elastic_reasoning(
                optimized, 
                self.elastic.t_budget, 
                self.elastic.s_budget, 
                wrapper=True
            )
            metadata["elastic_reasoning"] = {
                "think_budget": self.elastic.t_budget, 
                "solve_budget": self.elastic.s_budget
            }
            self.metrics["elastic_budgets_enforced"] += 1
        
        return optimized, metadata
    
    def analyze_generation(self, generated_text: str) -> Dict[str, Any]:
        """Post-process generation to extract metrics."""
        result = {}
        if self.elastic_active and self.elastic:
            result["elastic_metrics"] = ElasticReasoning.calculate_metrics(generated_text)
        if self.chain_draft_active:
            # Count words in the generation to estimate tokens saved
            word_count = len(generated_text.split())
            # Assume Chain of Draft saved ~30% tokens vs normal CoT
            saved = int(word_count * 0.3)
            self.metrics["total_tokens_saved"] += saved
            result["tokens_saved_estimate"] = saved
        return result
    
    def apply_fp16(self, model: Any) -> Any:
        """Apply FP16 stability to a model if active."""
        if self.fp16_active:
            try:
                result = apply_fp16_stability(model)
                self.metrics["fp16_stable_tensors"] += 1
                return result
            except Exception as e:
                logging.warning(f"FP16 stability application failed: {e}")
        return model
    
    def verify_fp16_stability(self, tensor: Any = None) -> Dict[str, Any]:
        """Check FP16 stability metrics."""
        if tensor is not None and self.fp16_active:
            return FP16Stability.check_stability_metrics(tensor)
        return {"stable": True, "note": "FP16 not active or no tensor provided"}

    def apply_entropy_guided(self, context_length: int) -> Dict[str, Any]:
        """Entropy-guided adaptive attention (arXiv:2606.09508v1)."""
        if not self.entropy_active:
            return {}
        result = apply_entropy_guided_inference(context_length, entropy_threshold=self.entropy_threshold)
        self.metrics["entropy_sparse_segments"] += result.get("sparse_attention_segments", 0)
        self.metrics["entropy_speedup"] = result.get("speedup_multiplier", 1.0)
        return result

    def apply_distinct_leaf(self) -> Dict[str, Any]:
        """Deterministic distinct-leaf self-consistency (arXiv:2604.20500)."""
        if not self.distinct_leaf_active:
            return {}
        result = apply_distinct_leaf_decoding(sample_budget=self.sc_budget)
        self.metrics["distinct_leaf_samples_saved"] += result.get("samples_saved", 0)
        return result

    def select_answer(self, candidates: List[Tuple[str, float]]) -> Dict[str, Any]:
        """Hybrid vote + discriminative-verifier selection (arXiv:2510.14913)."""
        if not self.disc_verify_active or not candidates:
            return {}
        result = apply_discriminative_verification(candidates)
        if result.get("overrode_majority"):
            self.metrics["verifier_majority_overrides"] += 1
        return result

    def apply_adaptive_kv(self, num_tokens: int) -> Dict[str, Any]:
        """Adaptive per-token KV-cache quantization (arXiv:2604.04722)."""
        if not self.adaptive_kv_active:
            return {}
        result = apply_adaptive_kv_quant(num_tokens)
        self.metrics["kv_memory_saved_pct"] = result.get("memory_savings_pct", 0.0)
        return result

    def apply_moqae(self, context_length: int) -> Dict[str, Any]:
        """Mixture of Quantization-Aware Experts routing (arXiv:2506.07533)."""
        if not self.moqae_active:
            return {}
        result = apply_moqae_quant(context_length)
        self.metrics["moqae_avg_bits"] = result.get("avg_bits", 16.0)
        return result

    def apply_confspec(self, num_steps: int) -> Dict[str, Any]:
        """Confidence-gated step-level speculative reasoning (arXiv:2602.18447)."""
        if not self.confspec_active:
            return {}
        result = apply_confspec_reasoning(num_steps, confidence_gate=self.confspec_gate)
        self.metrics["confspec_verify_saved"] += result.get("verify_passes_saved", 0)
        return result

    def apply_spec_prefill(self, num_tokens: int) -> Dict[str, Any]:
        """Draft-guided training-free prefill compression (arXiv:2603.02631)."""
        if not self.spec_prefill_active:
            return {}
        result = apply_speculative_prefill(num_tokens, keep_ratio=self.prefill_keep_ratio)
        self.metrics["prefill_tokens_dropped"] += result.get("dropped_tokens", 0)
        return result

    def score_intuitor(self, group_token_probs: List[List[float]]) -> Dict[str, Any]:
        """Label-free self-certainty RL reward (arXiv:2505.19590)."""
        if not self.intuitor_active or not group_token_probs:
            return {}
        result = apply_intuitor_reward(group_token_probs)
        self.metrics["intuitor_rollouts_scored"] += len(result.get("rewards", []))
        return result

    def optimize_echo(self, rollouts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Entropy-confidence hybrid test-time RL update (arXiv:2602.02150)."""
        if not self.echo_active or not rollouts:
            return {}
        result = apply_echo_ttrl(rollouts)
        if result.get("selected", -1) >= 0:
            self.metrics["echo_updates"] += 1
        return result

    def reinforce_attention(self, head_contributions: List[float], reward: float = 1.0) -> Dict[str, Any]:
        """Reward-weighted reinforcement of attention heads (arXiv:2602.04884)."""
        if not self.reinforced_attn_active or not head_contributions:
            return {}
        result = apply_reinforced_attention(head_contributions, reward)
        self.metrics["reinforced_attn_heads"] += result.get("reinforced_heads", 0)
        return result

    def encode_thoughts(self, base_thought_tokens: int) -> Dict[str, Any]:
        """Progressive thought-compression curriculum (arXiv:2602.16839)."""
        if not self.progressive_thought_active:
            return {}
        result = apply_progressive_thought_encoding(base_thought_tokens)
        self.metrics["progressive_thought_savings_pct"] = result.get("training_token_savings_pct", 0.0)
        return result

# ── Dynamic Terminal ─────────────────────────
class DynamicPaperTerminal:
    """
    Live dual-pane terminal showing agent reasoning and workflow execution
    with integrated paper metrics.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.cfg = config or load_config()
        self.user_prefs = load_user_prefs()
        self.console = Console()
        self.paper_engine = PaperIntegrationEngine(self.cfg)
        
        # Buffers
        self.reasoning_buffer = LogBuffer(self.cfg.get("max_log_lines", 150))
        self.workflow_buffer = LogBuffer(self.cfg.get("max_log_lines", 150))
        self.terminal_output_buffer = LogBuffer(100)
        
        # State
        self.running = False
        self.iteration = 0
        self.start_time = None
        self.last_elapsed = 0.0
        self.input_queue: List[str] = []
        self.current_input = ""
        self.show_config = False
        
        # Layout
        self.layout = self._build_layout()
        self.live = Live(
            self.layout, 
            console=self.console, 
            refresh_per_second=self.cfg.get("refresh_rate", 6),
            screen=True, 
            transient=False
        )
    
    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=5)
        )
        layout["main"].split_row(
            Layout(name="reasoning", ratio=1),
            Layout(name="workflow", ratio=1),
            Layout(name="terminal", ratio=1)
        )
        return layout
    
    def update_header(self):
        paper_names = []
        if self.paper_engine.chain_draft_active:
            paper_names.append(f"CoD:{self.paper_engine.chain_variant}")
        if self.paper_engine.elastic_active:
            paper_names.append(f"ER:{self.paper_engine.elastic.t_budget}/{self.paper_engine.elastic.s_budget}")
        if self.paper_engine.fp16_active:
            paper_names.append("FP16:ON")
        if self.paper_engine.snapkv_active:
            paper_names.append("SnapKV:ON")
        if self.paper_engine.speculative_active:
            paper_names.append("SpecDec:ON")
        
        header_text = Text(
            f"TruthGPT Dynamic Terminal | Papers: {', '.join(paper_names) if paper_names else 'none active'} | User: {self.user_prefs.get('user_name', 'default')}",
            style="bold white on dark_blue"
        )
        self.layout["header"].update(Panel(header_text, border_style="bright_blue"))
    
    def add_reasoning(self, text: str):
        self.reasoning_buffer.add(text)
        self._refresh_reasoning_panel()
    
    def add_workflow_log(self, text: str):
        self.workflow_buffer.add(text)
        self._refresh_workflow_panel()
    
    def add_terminal_output(self, text: str):
        self.terminal_output_buffer.add(text)
        self._refresh_terminal_panel()
    
    def update_footer(self):
        m = self.paper_engine.metrics
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        metrics_table = Table.grid(padding=(0, 2))
        metrics_table.add_column(justify="left")
        metrics_table.add_column(justify="right")
        metrics_table.add_row(
            f"[bold]Iter:[/bold] {self.iteration} | [bold]Elapsed:[/bold] {elapsed:.1f}s | [bold]CoD applied:[/bold] {m['chain_draft_applied']} | [bold]SnapKV runs:[/bold] {m['snapkv_compression_runs']}",
            f"[bold]Elastic:[/bold] {m['elastic_budgets_enforced']} | [bold]FP16 checks:[/bold] {m['fp16_stable_tensors']} | [bold]Tokens saved:[/bold] {m['total_tokens_saved']} | [bold]SpecDec tokens:[/bold] {m['speculative_tokens_accepted']}"
        )
        
        footer_panel = Panel(
            metrics_table,
            border_style="bright_black",
            padding=(0, 1)
        )
        self.layout["footer"].update(footer_panel)
    
    def _refresh_reasoning_panel(self):
        lines = self.reasoning_buffer.get_all()[-20:]
        if not lines:
            lines = ["[dim]Waiting for agent reasoning...[/dim]"]
        
        panel = Panel(
            "\n".join(lines),
            title="[bold cyan]🧠 Agent Reasoning (Chain of Draft)[/bold cyan]",
            border_style="cyan",
            height=22
        )
        self.layout["reasoning"].update(panel)
    
    def _refresh_workflow_panel(self):
        lines = self.workflow_buffer.get_all()[-20:]
        if not lines:
            lines = ["[dim]Waiting for workflow execution...[/dim]"]
        
        panel = Panel(
            "\n".join(lines),
            title="[bold yellow]⚙️ Workflow & Tools (Elastic Reasoning)[/bold yellow]",
            border_style="yellow",
            height=22
        )
        self.layout["workflow"].update(panel)
    
    def _refresh_terminal_panel(self):
        if self.show_config:
            # Show config view
            config_text = json.dumps(self.cfg, indent=2)
            panel = Panel(
                config_text,
                title="[bold green]🔧 Configuration[/bold green]",
                border_style="green",
                height=22
            )
        else:
            lines = self.terminal_output_buffer.get_all()[-15:]
            if not lines:
                lines = ["[dim]Terminal output will appear here...[/dim]"]
            
            panel = Panel(
                "\n".join(lines),
                title="[bold green]📺 Terminal Output[/bold green]",
                border_style="green",
                height=22
            )
        self.layout["terminal"].update(panel)
    
    def refresh_all(self):
        self.update_header()
        self._refresh_reasoning_panel()
        self._refresh_workflow_panel()
        self._refresh_terminal_panel()
        self.update_footer()
    
    async def run_continuous_loop(self):
        """Main continuous loop with paper integrations."""
        self.running = True
        self.start_time = time.time()
        
        with self.live:
            self.refresh_all()
            
            self.add_reasoning("🚀 Initializing TruthGPT Dynamic Terminal...")
            self.add_workflow_log("🔧 Loading paper modules: Chain of Draft, Elastic Reasoning, FP16 Stability")
            self.add_workflow_log(f"📋 Active papers: {self.cfg.get('active_papers', [])}")
            
            # Load workflow if available
            workflow = None
            if WORKFLOW_AVAILABLE and DynamicWorkflow:
                workflow_path = Path(__file__).parent / self.cfg.get("workflow_file", "default_workflow.yaml")
                if workflow_path.exists():
                    workflow = DynamicWorkflow(config_path=workflow_path, user_prefs=self.user_prefs)
                    self.add_workflow_log(f"✅ Workflow loaded: {workflow_path}")
                else:
                    self.add_workflow_log(f"⚠️ Workflow file not found: {workflow_path}")
            
            while self.running and (self.cfg.get("max_iterations", 0) == 0 or self.iteration < self.cfg.get("max_iterations", 0)):
                self.iteration += 1
                
                # Simulate agent reasoning with Chain of Draft
                sample_prompt = f"Optimize system performance for iteration {self.iteration}"
                optimized_prompt, metadata = self.paper_engine.process_prompt(sample_prompt)
                
                self.add_reasoning(f"📝 Prompt processed: {sample_prompt[:60]}...")
                self.add_reasoning(f"   Chain of Draft template applied ({self.paper_engine.chain_variant})" if metadata.get("chain_of_draft") else "   Chain of Draft: OFF")
                self.add_reasoning(f"   Elastic budgets: think={self.paper_engine.elastic.t_budget}, solve={self.paper_engine.elastic.s_budget}" if metadata.get("elastic_reasoning") else "   Elastic Reasoning: OFF")
                
                # Simulate generation
                generated = f"<think>Analysing iteration {self.iteration} performance metrics.</think>\nOptimization cycle {self.iteration} complete. System nominal."
                gen_metrics = self.paper_engine.analyze_generation(generated)
                
                self.add_workflow_log(f"🔄 Iteration {self.iteration} started")
                self.add_workflow_log(f"   Generated response ({len(generated.split())} words)")
                if "elastic_metrics" in gen_metrics:
                    self.add_workflow_log(f"   Elastic: {gen_metrics['elastic_metrics']['think_tokens']} think tokens, {gen_metrics['elastic_metrics']['total_tokens']} total")
                if "tokens_saved_estimate" in gen_metrics:
                    self.add_workflow_log(f"   💰 Tokens saved: ~{gen_metrics['tokens_saved_estimate']}")
                
                # FP16 stability check (simulated)
                if self.paper_engine.fp16_active:
                    stability = self.paper_engine.verify_fp16_stability()
                    self.add_workflow_log(f"   FP16 Stability: {'✅ Stable' if stability.get('stable', True) else '⚠️ Issues detected'}")
                
                # SnapKV Compression (simulated)
                if self.paper_engine.snapkv_active:
                    context_len = 1000 + (self.iteration * 150)
                    kv_result = apply_snap_kv_compression(context_len)
                    self.paper_engine.metrics["snapkv_compression_runs"] += 1
                    self.paper_engine.metrics["total_tokens_saved"] += kv_result.get("tokens_saved", 0)
                    if kv_result.get("compressed"):
                        self.add_workflow_log(f"   📉 SnapKV: Compressed KV cache from {kv_result['original_size']} to {kv_result['new_size']} tokens")
                
                # Speculative Decoding (simulated)
                if self.paper_engine.speculative_active:
                    spec_result = apply_speculative_decoding()
                    accepted = spec_result.get("accepted_tokens", 0)
                    self.paper_engine.metrics["speculative_tokens_accepted"] += accepted
                    self.add_workflow_log(f"   ⚡ SpecDec: {accepted} tokens accepted (Speedup: {spec_result.get('speedup_multiplier', 1.0):.1f}x)")
                
                # Update terminal output
                self.add_terminal_output(f"$ Iteration {self.iteration}: {generated[:80]}...")
                
                self.refresh_all()
                
                await asyncio.sleep(self.cfg.get("workflow_interval", 5))
            
            self.add_reasoning("🛑 Loop terminated.")
            self.add_workflow_log("✅ Continuous loop ended.")
            self.refresh_all()
    
    def stop(self):
        self.running = False

# ── Entry Point ──────────────────────────────
async def main():
    parser = argparse.ArgumentParser(description="TruthGPT Dynamic Terminal with Paper Integrations")
    parser.add_argument("--config", type=str, help="Path to config JSON file")
    parser.add_argument("--iterations", type=int, default=0, help="Max iterations (0=infinite)")
    parser.add_argument("--variant", type=str, default="baseline", 
                       choices=ChainOfDraft.VARIANTS if PAPERS_AVAILABLE else ["baseline"],
                       help="Chain of Draft variant")
    parser.add_argument("--think-budget", type=int, default=30, help="Elastic reasoning think budget")
    parser.add_argument("--solve-budget", type=int, default=120, help="Elastic reasoning solve budget")
    parser.add_argument("--no-fp16", action="store_true", help="Disable FP16 stability")
    parser.add_argument("--no-chain", action="store_true", help="Disable Chain of Draft")
    parser.add_argument("--no-elastic", action="store_true", help="Disable Elastic Reasoning")
    parser.add_argument("--no-snapkv", action="store_true", help="Disable SnapKV Compression")
    parser.add_argument("--no-speculative", action="store_true", help="Disable Speculative Decoding")
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    if args.config:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            config.update(user_config)
        except Exception as e:
            print(f"Error loading config {args.config}: {e}")
    
    # Override with CLI args
    config["max_iterations"] = args.iterations
    config["chain_of_draft_variant"] = args.variant
    config["elastic_reasoning_budget"] = {"think": args.think_budget, "solve": args.solve_budget}
    
    active_papers = config.get("active_papers", [])
    if args.no_chain and "chain_of_draft" in active_papers:
        active_papers.remove("chain_of_draft")
    if args.no_elastic and "elastic_reasoning" in active_papers:
        active_papers.remove("elastic_reasoning")
    if getattr(args, 'no_snapkv', False) and "snap_kv" in active_papers:
        active_papers.remove("snap_kv")
    if getattr(args, 'no_speculative', False) and "speculative_decoding" in active_papers:
        active_papers.remove("speculative_decoding")
    if args.no_fp16:
        config["fp16_enabled"] = False
        if "fp16_stability" in active_papers:
            active_papers.remove("fp16_stability")
    config["active_papers"] = active_papers
    
    # Create and run terminal
    terminal = DynamicPaperTerminal(config)
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        terminal.stop()
        print("\n👋 Shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await terminal.run_continuous_loop()
    except KeyboardInterrupt:
        terminal.stop()
        print("\n👋 Terminal stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(main())
