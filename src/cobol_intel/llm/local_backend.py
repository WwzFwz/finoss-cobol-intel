"""Local fine-tuned model backend using HuggingFace transformers.

Loads a PEFT/LoRA fine-tuned model (or any HuggingFace causal LM) for fully
offline inference. Designed for models trained with tools/finetune.py.

Requirements (install via extras):
    pip install "cobol-intel[local]"

Environment variables:
    COBOL_INTEL_LOCAL_MODEL_PATH: path to the model directory
    COBOL_INTEL_LOCAL_MAX_NEW_TOKENS: max tokens to generate (default 1024)
    COBOL_INTEL_LOCAL_DEVICE: device to use (default "auto")
    COBOL_INTEL_LOCAL_DO_SAMPLE: enable sampling (default false)
    COBOL_INTEL_LOCAL_TEMPERATURE: sampling temperature (default 0.7)
    COBOL_INTEL_LOCAL_TOP_P: nucleus sampling top-p (default 0.9)
    COBOL_INTEL_LOCAL_REPETITION_PENALTY: repetition penalty (default 1.1)
"""

from __future__ import annotations

import os

from cobol_intel.llm.backend import LLMBackend, LLMResponse

_DEFAULT_MAX_NEW_TOKENS = 1024
_DEFAULT_DO_SAMPLE = False
_DEFAULT_TEMPERATURE = 0.7
_DEFAULT_TOP_P = 0.9
_DEFAULT_REPETITION_PENALTY = 1.1


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    return float(value)


class LocalBackend(LLMBackend):
    """LLM backend using a locally loaded HuggingFace model."""

    def __init__(
        self,
        model_path: str | None = None,
        max_new_tokens: int | None = None,
        device: str | None = None,
        do_sample: bool | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        repetition_penalty: float | None = None,
    ) -> None:
        self._model_path = (
            model_path
            or os.environ.get("COBOL_INTEL_LOCAL_MODEL_PATH", "")
        )
        if not self._model_path:
            raise ValueError(
                "Model path required. Set COBOL_INTEL_LOCAL_MODEL_PATH or "
                "pass model_path argument."
            )
        self._max_new_tokens = max_new_tokens or int(
            os.environ.get(
                "COBOL_INTEL_LOCAL_MAX_NEW_TOKENS",
                _DEFAULT_MAX_NEW_TOKENS,
            )
        )
        self._device = device or os.environ.get(
            "COBOL_INTEL_LOCAL_DEVICE", "auto",
        )
        self._do_sample = (
            do_sample
            if do_sample is not None
            else _env_bool("COBOL_INTEL_LOCAL_DO_SAMPLE", _DEFAULT_DO_SAMPLE)
        )
        self._temperature = (
            temperature
            if temperature is not None
            else _env_float("COBOL_INTEL_LOCAL_TEMPERATURE", _DEFAULT_TEMPERATURE)
        )
        self._top_p = (
            top_p
            if top_p is not None
            else _env_float("COBOL_INTEL_LOCAL_TOP_P", _DEFAULT_TOP_P)
        )
        self._repetition_penalty = (
            repetition_penalty
            if repetition_penalty is not None
            else _env_float(
                "COBOL_INTEL_LOCAL_REPETITION_PENALTY",
                _DEFAULT_REPETITION_PENALTY,
            )
        )
        self._model = None
        self._tokenizer = None

    def _load(self):
        """Lazy-load model and tokenizer on first use."""
        if self._model is not None:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as e:
            raise ImportError(
                f"Missing dependency: {e}\n"
                'Install: pip install "cobol-intel[local]"'
            ) from e

        self._tokenizer = AutoTokenizer.from_pretrained(
            self._model_path, trust_remote_code=True,
        )
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        model_kwargs = {
            "trust_remote_code": True,
            "torch_dtype": torch.bfloat16,
        }
        if self._device == "auto":
            model_kwargs["device_map"] = "auto"

        # Try loading as PEFT model first, fall back to a regular causal LM.
        try:
            from peft import AutoPeftModelForCausalLM

            self._model = AutoPeftModelForCausalLM.from_pretrained(
                self._model_path, **model_kwargs,
            )
        except Exception:
            self._model = AutoModelForCausalLM.from_pretrained(
                self._model_path, **model_kwargs,
            )

        self._model.eval()

    @property
    def name(self) -> str:
        return "local"

    @property
    def model_id(self) -> str:
        return self._model_path

    def clone(self) -> LocalBackend:
        return LocalBackend(
            model_path=self._model_path,
            max_new_tokens=self._max_new_tokens,
            device=self._device,
            do_sample=self._do_sample,
            temperature=self._temperature,
            top_p=self._top_p,
            repetition_penalty=self._repetition_penalty,
        )

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        """Generate a completion using the local model."""
        import torch

        self._load()

        # Match the Alpaca-style prompt template used by tools/finetune.py.
        if system:
            full_prompt = (
                f"### Instruction:\n{system}\n\n"
                f"### Input:\n{prompt}\n\n"
                f"### Response:\n"
            )
        else:
            full_prompt = (
                f"### Instruction:\n{prompt}\n\n"
                f"### Response:\n"
            )

        inputs = self._tokenizer(
            full_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=4096 - self._max_new_tokens,
        )
        if self._device != "auto":
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
        else:
            inputs = {
                k: v.to(self._model.device) for k, v in inputs.items()
            }

        input_length = inputs["input_ids"].shape[1]
        generate_kwargs = {
            "max_new_tokens": self._max_new_tokens,
            "do_sample": self._do_sample,
            "repetition_penalty": self._repetition_penalty,
            "pad_token_id": self._tokenizer.pad_token_id,
        }
        if self._do_sample:
            generate_kwargs["temperature"] = self._temperature
            generate_kwargs["top_p"] = self._top_p

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                **generate_kwargs,
            )

        generated_ids = outputs[0][input_length:]
        text = self._tokenizer.decode(generated_ids, skip_special_tokens=True)

        return LLMResponse(
            text=text.strip(),
            model=self._model_path,
            input_tokens=input_length,
            output_tokens=len(generated_ids),
        )
