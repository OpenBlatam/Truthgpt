import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from . import register_model


@register_model("hf-transformers")
class HFLLM:
    def __init__(self) -> None:
        self.tokenizer = None
        self.model = None

    def _resolve_dtype(self, mixed_precision: str):
        if mixed_precision == "bf16":
            return torch.bfloat16
        if mixed_precision == "fp16":
            return torch.float16
        return None

    def load(self, cfg):
        name = cfg["model"]["name_or_path"]
        mp = cfg.get("training", {}).get("mixed_precision", "no")
        dtype = self._resolve_dtype(mp)

        self.tokenizer = AutoTokenizer.from_pretrained(name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(name, torch_dtype=dtype)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(device).eval()
        if hasattr(self.model, "config"):
            try:
                self.model.config.use_cache = True
            except Exception:
                pass

    @torch.inference_mode()
    def infer(self, inputs):
        device = next(self.model.parameters()).device
        toks = self.tokenizer(inputs["text"], return_tensors="pt").to(device)
        output_ids = self.model.generate(
            **toks,
            max_new_tokens=int(inputs.get("max_new_tokens", 64)),
            do_sample=True,
            temperature=float(inputs.get("temperature", 0.8)),
            pad_token_id=self.tokenizer.eos_token_id,
        )
        return {"text": self.tokenizer.decode(output_ids[0], skip_special_tokens=True)}





