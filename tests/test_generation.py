from persona_mas.generation import MockBackend


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
