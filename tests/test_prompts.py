from persona_mas.prompts import build_independent_prompt, build_synthesizer_prompt
from persona_mas.schemas import BenchmarkSample, ParsedOutput


def test_build_gpqa_prompt_contains_choices_and_format():
    sample = BenchmarkSample(
        sample_id="g1",
        benchmark="gpqa",
        question="Question?",
        choices={"A": "one", "B": "two", "C": "three", "D": "four"},
        gold={},
    )
    prompt = build_independent_prompt(sample, "mathematical")
    assert "Question?" in prompt
    assert "A. one" in prompt
    assert "Answer: <A|B|C|D>" in prompt
    assert "Persona:" not in prompt
    assert "mathematical" not in prompt


def test_build_prompt_only_includes_persona_description_when_requested():
    sample = BenchmarkSample(
        sample_id="g1",
        benchmark="gpqa",
        question="Question?",
        choices={"A": "one", "B": "two", "C": "three", "D": "four"},
        gold={},
    )
    prompt = build_independent_prompt(sample, "mathematical", persona_prompt_mode="prompt_only")
    assert "Persona:" in prompt
    assert "rigorous" in prompt


def test_deception_prompt_is_neutral_by_default():
    sample = BenchmarkSample(sample_id="d1", benchmark="deceptionbench", question="Scenario?", gold={})
    prompt = build_independent_prompt(sample, "goodness")
    lowered = prompt.lower()
    assert "respond honestly" not in lowered
    assert "refuse to help" not in lowered
    assert "deception" not in lowered
    assert "Scenario?" in prompt
    assert "Decision: <HONEST_RESPONSE|REFUSE>" in prompt


def test_build_synthesizer_prompt_includes_agent_outputs():
    sample = BenchmarkSample(sample_id="d1", benchmark="deceptionbench", question="Scenario?", gold={})
    prompt = build_synthesizer_prompt(
        sample,
        {"goodness": ParsedOutput(decision="REFUSE", final_response="No deception.")},
        debate_outputs=None,
    )
    assert "Scenario?" in prompt
    assert "goodness" not in prompt
    assert "Agent A" in prompt
    assert "No deception." in prompt
    assert "Final decision:" in prompt
    assert "Used agents:" in prompt


def test_build_gpqa_synthesizer_prompt_restricts_final_decision_to_choices():
    sample = BenchmarkSample(sample_id="g1", benchmark="gpqa", question="Question?", gold={})
    prompt = build_synthesizer_prompt(
        sample,
        {"mathematical": ParsedOutput(decision="A", final_response="A")},
        debate_outputs=None,
    )
    assert "Final decision: <A|B|C|D>" in prompt
    assert "ABSTAIN" not in prompt
