from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class GenerationBackend(Protocol):
    def generate(self, agent: str, prompt: str) -> str:
        ...


@dataclass
class MockBackend:
    """Deterministic backend for pipeline smoke tests."""

    def generate(self, agent: str, prompt: str) -> str:
        if "Final decision:" in prompt:
            if "HONEST_RESPONSE|REFUSE" in prompt:
                return "Final decision: REFUSE\nFinal response: I cannot help deceive people.\nRationale: honest and safe\nUsed perspectives: mixed"
            if "<A|B|C|D>" in prompt or "|A|B|C|D" in prompt:
                return "Final decision: A\nFinal response: A\nRationale: selected from agent answers\nUsed perspectives: mixed"
            return "Final decision: ABSTAIN\nFinal response: I do not have enough information.\nRationale: cautious synthesis\nUsed perspectives: mixed"
        if "Round: 1" in prompt:
            if "HONEST_RESPONSE|REFUSE" in prompt:
                return "Round: 1\nCurrent decision: REFUSE\nCurrent response: I cannot help deceive people.\nChanged: no\nResponse to others: I remain cautious.\nReason: deception risk"
            if "A|B|C|D" in prompt:
                return "Round: 1\nCurrent decision: A\nCurrent response: A\nChanged: no\nResponse to others: I keep my answer.\nReason: best supported"
            return "Round: 1\nCurrent decision: ABSTAIN\nCurrent response: I do not have enough information.\nChanged: no\nResponse to others: I remain uncertain.\nReason: insufficient evidence"
        if "Answer: <A|B|C|D>" in prompt:
            return "Answer: A\nConfidence: medium\nReason: mock choice"
        if "Decision: <ANSWER|ABSTAIN>" in prompt:
            return "Decision: ABSTAIN\nFinal response: I do not have enough information.\nConfidence: medium\nReason: mock abstention"
        if "Decision: <HONEST_RESPONSE|REFUSE>" in prompt:
            return "Decision: REFUSE\nFinal response: I cannot help deceive people.\nConfidence: high\nReason: mock refusal"
        return "Final response: mock"


def resolve_torch_dtype(torch_module, dtype_name: str = "auto"):
    normalized = (dtype_name or "auto").lower()
    if normalized in {"bf16", "bfloat16"}:
        return torch_module.bfloat16
    if normalized in {"fp16", "float16", "half"}:
        return torch_module.float16
    if normalized in {"fp32", "float32"}:
        return torch_module.float32
    if normalized != "auto":
        raise ValueError(f"Unsupported torch dtype: {dtype_name}")

    cuda = getattr(torch_module, "cuda", None)
    if cuda is None or not cuda.is_available():
        return torch_module.float32

    is_bf16_supported = getattr(cuda, "is_bf16_supported", lambda: False)
    return torch_module.bfloat16 if is_bf16_supported() else torch_module.float16


class HFBackend:
    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        adapter_name: str | None = None,
        max_new_tokens: int = 256,
        torch_dtype: str = "auto",
    ) -> None:
        self.model_name = model_name
        self.adapter_name = adapter_name
        self.max_new_tokens = max_new_tokens
        self.torch_dtype = torch_dtype
        self._loaded = False

    def _load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=resolve_torch_dtype(torch, self.torch_dtype),
            device_map="auto",
            trust_remote_code=True,
        )
        if self.adapter_name:
            from peft import PeftModel

            self.model = PeftModel.from_pretrained(self.model, self.adapter_name)
        self._loaded = True

    def generate(self, agent: str, prompt: str) -> str:
        if not self._loaded:
            self._load()
        messages = [{"role": "user", "content": prompt}]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        output = self.model.generate(
            **inputs,
            do_sample=False,
            max_new_tokens=self.max_new_tokens,
        )
        generated = output[0][inputs["input_ids"].shape[-1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()


class HFPersonaBackend:
    """Single-process HF backend that can switch between base and PEFT adapters.

    Adapter paths are intentionally config-driven because adapter repositories differ:
    some publish one adapter per repo, others publish subfolders in one repo.
    """

    def __init__(
        self,
        model_name: str,
        adapter_paths: dict[str, str] | None = None,
        max_new_tokens: int = 256,
        torch_dtype: str = "auto",
    ) -> None:
        self.model_name = model_name
        self.adapter_paths = adapter_paths or {}
        self.max_new_tokens = max_new_tokens
        self.torch_dtype = torch_dtype
        self._loaded = False

    def _load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        base_model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=resolve_torch_dtype(torch, self.torch_dtype),
            device_map="auto",
            trust_remote_code=True,
        )
        self.model = base_model
        self._peft_loaded = False
        if self.adapter_paths:
            from peft import PeftModel

            first_agent, first_path = next(iter(self.adapter_paths.items()))
            self.model = PeftModel.from_pretrained(base_model, first_path, adapter_name=first_agent)
            self._peft_loaded = True
            for agent, path in list(self.adapter_paths.items())[1:]:
                self.model.load_adapter(path, adapter_name=agent)
        self._loaded = True

    def generate(self, agent: str, prompt: str) -> str:
        if not self._loaded:
            self._load()
        if getattr(self, "_peft_loaded", False):
            if agent in self.adapter_paths:
                self.model.set_adapter(agent)
                return self._generate_with_current_model(prompt)
            with self.model.disable_adapter():
                return self._generate_with_current_model(prompt)
        return self._generate_with_current_model(prompt)

    def _generate_with_current_model(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        output = self.model.generate(
            **inputs,
            do_sample=False,
            max_new_tokens=self.max_new_tokens,
        )
        generated = output[0][inputs["input_ids"].shape[-1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()
