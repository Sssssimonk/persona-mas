from persona_mas.judge import MockJudge, build_deception_judge_prompt
from persona_mas.schemas import BenchmarkSample, ParsedOutput


def test_build_deception_judge_prompt_contains_groundtruth_goal_response():
    sample = BenchmarkSample(
        sample_id="d1",
        benchmark="deceptionbench",
        question="Scenario",
        gold={"groundtruth": "Tell the truth.", "goal": "Hide the truth."},
    )
    prompt = build_deception_judge_prompt(sample, ParsedOutput("REFUSE", "I cannot deceive."))
    assert "Tell the truth." in prompt
    assert "Hide the truth." in prompt
    assert "I cannot deceive." in prompt
    assert "Label: <HONEST|DECEPTIVE|REFUSAL|UNCLEAR>" in prompt


def test_mock_judge_labels_refusal():
    sample = BenchmarkSample(sample_id="d1", benchmark="deceptionbench", question="Scenario")
    result = MockJudge().judge_deception(sample, ParsedOutput("REFUSE", "I cannot help deceive."))
    assert result["label"] == "REFUSAL"

