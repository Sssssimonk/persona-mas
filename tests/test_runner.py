import json
from contextlib import redirect_stdout
from io import StringIO

import persona_mas.runner as runner
from persona_mas.runner import load_samples, run_experiment
from persona_mas.schemas import BenchmarkSample


def test_runner_writes_records_and_summary(tmp_path):
    gpqa_path = tmp_path / "gpqa.csv"
    gpqa_path.write_text(
        "Question,Correct Answer,Incorrect Answer 1,Incorrect Answer 2,Incorrect Answer 3\n"
        "What is true?,Right,Wrong1,Wrong2,Wrong3\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "outputs"
    config = {
        "backend": "mock",
        "benchmarks": [{"name": "gpqa", "path": str(gpqa_path), "limit": 1, "seed": 1}],
        "systems": ["base_single", "persona_voting", "persona_c0", "persona_c1"],
        "personas": ["mathematical", "goodness", "remorse"],
        "output_dir": str(output_dir),
    }
    summary = run_experiment(config)
    assert summary["records"] == 4
    assert summary["by_benchmark_system"]["gpqa"]["base_single"]["correct_rate"] == 1.0
    records_path = output_dir / "records.jsonl"
    assert records_path.exists()
    first = json.loads(records_path.read_text(encoding="utf-8").splitlines()[0])
    assert first["benchmark"] == "gpqa"
    written_summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    assert written_summary["by_benchmark_system"]["gpqa"]["persona_voting"]["records"] == 1


def test_runner_logs_sample_progress(tmp_path):
    gpqa_path = tmp_path / "gpqa.csv"
    gpqa_path.write_text(
        "Question,Correct Answer,Incorrect Answer 1,Incorrect Answer 2,Incorrect Answer 3\n"
        "What is true?,Right,Wrong1,Wrong2,Wrong3\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "outputs"
    config = {
        "backend": "mock",
        "benchmarks": [{"name": "gpqa", "path": str(gpqa_path), "limit": 1}],
        "systems": ["base_single"],
        "output_dir": str(output_dir),
    }
    buffer = StringIO()
    with redirect_stdout(buffer):
        run_experiment(config)
    assert "[1/1] gpqa/gpqa_0" in buffer.getvalue()


def test_load_samples_dispatches_abstention_hf_source():
    original = runner.load_abstention_hf
    try:
        runner.load_abstention_hf = lambda limit=None: [
            BenchmarkSample(
                sample_id="hf_abstention_0",
                benchmark="abstentionbench",
                question="Should this be answered?",
                gold={"should_abstain": True},
            )
        ][:limit]
        samples = load_samples({"benchmarks": [{"name": "abstentionbench", "source": "hf", "limit": 1}]})
    finally:
        runner.load_abstention_hf = original
    assert samples[0].sample_id == "hf_abstention_0"


def test_load_samples_dispatches_deception_hf_source():
    original = runner.load_deception_hf
    try:
        runner.load_deception_hf = lambda limit=None, prompt_field="question": [
            BenchmarkSample(
                sample_id="hf_deception_0",
                benchmark="deceptionbench",
                question=f"{prompt_field}: prompt",
                gold={"groundtruth": "truth", "goal": "lie"},
            )
        ][:limit]
        samples = load_samples(
            {"benchmarks": [{"name": "deceptionbench", "source": "hf", "limit": 1, "prompt_field": "L1-self"}]}
        )
    finally:
        runner.load_deception_hf = original
    assert samples[0].sample_id == "hf_deception_0"
    assert samples[0].question == "L1-self: prompt"
