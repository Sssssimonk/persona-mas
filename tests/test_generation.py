from types import SimpleNamespace

from persona_mas.generation import MockBackend, resolve_torch_dtype


def test_mock_backend_returns_gpqa_format():
    backend = MockBackend()
    text = backend.generate("agent", "Answer: <A|B|C|D>")
    assert "Answer:" in text
    assert "Confidence:" in text


def test_mock_backend_returns_synthesizer_format():
    backend = MockBackend()
    text = backend.generate("base", "Final decision: <ANSWER|ABSTAIN|HONEST_RESPONSE|REFUSE|A|B|C|D>")
    assert "Final decision:" in text
    assert "Final response:" in text


def test_resolve_torch_dtype_auto_uses_float16_when_bf16_is_not_supported():
    torch = SimpleNamespace(
        float16="float16",
        bfloat16="bfloat16",
        float32="float32",
        cuda=SimpleNamespace(is_available=lambda: True, is_bf16_supported=lambda: False),
    )
    assert resolve_torch_dtype(torch, "auto") == "float16"


def test_resolve_torch_dtype_auto_uses_bfloat16_when_supported():
    torch = SimpleNamespace(
        float16="float16",
        bfloat16="bfloat16",
        float32="float32",
        cuda=SimpleNamespace(is_available=lambda: True, is_bf16_supported=lambda: True),
    )
    assert resolve_torch_dtype(torch, "auto") == "bfloat16"


def test_resolve_torch_dtype_accepts_explicit_float16():
    torch = SimpleNamespace(
        float16="float16",
        bfloat16="bfloat16",
        float32="float32",
        cuda=SimpleNamespace(is_available=lambda: True, is_bf16_supported=lambda: True),
    )
    assert resolve_torch_dtype(torch, "float16") == "float16"
