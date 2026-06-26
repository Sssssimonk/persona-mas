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


def test_build_synthesizer_prompt_includes_agent_outputs():
    sample = BenchmarkSample(sample_id="d1", benchmark="deceptionbench", question="Scenario?", gold={})
    prompt = build_synthesizer_prompt(
        sample,
        {"goodness": ParsedOutput(decision="REFUSE", final_response="No deception.")},
        debate_outputs=None,
    )
    assert "Scenario?" in prompt
    assert "goodness" in prompt
    assert "No deception." in prompt
    assert "Final decision:" in prompt


def test_build_gpqa_synthesizer_prompt_restricts_final_decision_to_choices():
    sample = BenchmarkSample(sample_id="g1", benchmark="gpqa", question="Question?", gold={})
    prompt = build_synthesizer_prompt(
        sample,
        {"mathematical": ParsedOutput(decision="A", final_response="A")},
        debate_outputs=None,
    )
    assert "Final decision: <A|B|C|D>" in prompt
    assert "ABSTAIN" not in prompt
