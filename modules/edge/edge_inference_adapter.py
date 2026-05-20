import torch
from typing import Optional
from transformers import AutoModelForCausalLM, AutoTokenizer

from modules.memory.advanced_memory_manager import create_advanced_memory_manager
from modules.attention.attn_autotune import choose_best_backend


class EdgeInferenceAdapter:
    def __init__(self, model_name: str = "gpt2", max_new_tokens: int = 64) -> None:
        self.mm = create_advanced_memory_manager()
        self.dtype = self.mm.select_dtype_adaptive()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model.to(self.device)
        self.model.eval()
        self.max_new_tokens = max_new_tokens
        # Decide attention backend on a small probe (H,T,D approximations)
        h = getattr(self.model.config, "n_head", 12)
        d = getattr(self.model.config, "n_embd", 768) // max(1, h)
        backend = choose_best_backend(h=h, t=128, d=d, dtype=self.dtype)
        self.use_sdpa = backend == "sdpa"

    @torch.no_grad()
    def generate(self, prompt: str, temperature: float = 0.8, max_new_tokens: Optional[int] = None) -> str:
        max_new = max_new_tokens or self.max_new_tokens
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        autocast_dtype = self.dtype if self.device.type == "cuda" else None
        with torch.cuda.amp.autocast(enabled=(self.device.type == "cuda"), dtype=autocast_dtype):
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new,
                do_sample=True,
                temperature=temperature,
                pad_token_id=self.tokenizer.eos_token_id,
                use_cache=True,
            )
        return self.tokenizer.decode(output_ids[0], skip_special_tokens=True)





