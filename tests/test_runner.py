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


def test_runner_reuses_round0_outputs_across_voting_c0_and_c1(tmp_path):
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
        "systems": ["persona_voting", "persona_c0", "persona_c1"],
        "personas": ["mathematical", "goodness", "remorse"],
        "output_dir": str(output_dir),
    }
    run_experiment(config)
    records = [json.loads(line) for line in (output_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()]
    by_system = {record["system"]: record for record in records}
    for agent in ["mathematical", "goodness", "remorse"]:
        voting_raw = by_system["persona_voting"]["agent_outputs"][agent]["raw_text"]
        assert by_system["persona_c0"]["agent_outputs"][agent]["raw_text"] == voting_raw
        assert by_system["persona_c1"]["agent_outputs"][agent]["raw_text"] == voting_raw


def test_runner_uses_neutral_prompt_mode_by_default(tmp_path):
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
        "systems": ["base_single", "persona_voting"],
        "personas": ["mathematical", "goodness", "remorse"],
        "output_dir": str(output_dir),
    }
    run_experiment(config)
    records = [json.loads(line) for line in (output_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()]
    prompts = []
    for record in records:
        prompts.extend(output["prompt"] for output in record["agent_outputs"].values())
    assert all("Persona:" not in prompt for prompt in prompts)


def test_runner_passes_prompt_protocol_to_agent_and_synthesizer_prompts(tmp_path):
    gpqa_path = tmp_path / "gpqa.csv"
    gpqa_path.write_text(
        "Question,Correct Answer,Incorrect Answer 1,Incorrect Answer 2,Incorrect Answer 3\n"
        "What is true?,Right,Wrong1,Wrong2,Wrong3\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "outputs"
    config = {
        "backend": "mock",
        "prompt_protocol": "official_cot",
        "benchmarks": [{"name": "gpqa", "path": str(gpqa_path), "limit": 1}],
        "systems": ["persona_c1"],
        "personas": ["mathematical", "goodness", "remorse"],
        "output_dir": str(output_dir),
    }
    run_experiment(config)
    record = json.loads((output_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()[0])
    first_prompt = record["agent_outputs"]["mathematical"]["prompt"]
    round_prompt = record["agent_outputs"]["mathematical_round1"]["prompt"]
    assert "Reasoning: <your step-by-step reasoning>" in first_prompt
    assert "Final answer: <A|B|C|D>" in first_prompt
    assert "Other agents' initial answers:" in round_prompt
    assert "Changed:" not in round_prompt
    assert record["metrics"]["round1_changed_count"] == 0


def test_runner_supports_single_persona_system(tmp_path):
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
        "systems": ["single_persona"],
        "personas": ["mathematical", "goodness", "remorse"],
        "output_dir": str(output_dir),
    }
    run_experiment(config)
    records = [json.loads(line) for line in (output_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [record["system"] for record in records] == ["mathematical_single", "goodness_single", "remorse_single"]


def test_runner_supports_base_ensemble_and_homogeneous_controls(tmp_path):
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
        "systems": ["base_ensemble_c0", "homogeneous_mathematical_c0"],
        "personas": ["mathematical", "goodness", "remorse"],
        "output_dir": str(output_dir),
    }
    run_experiment(config)
    records = [json.loads(line) for line in (output_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()]
    by_system = {record["system"]: record for record in records}
    assert set(by_system["base_ensemble_c0"]["agent_outputs"]) == {"base_1", "base_2", "base_3"}
    assert set(by_system["homogeneous_mathematical_c0"]["agent_outputs"]) == {
        "mathematical_1",
        "mathematical_2",
        "mathematical_3",
    }


def test_runner_uses_abstention_judge_for_natural_protocol(tmp_path):
    abstention_path = tmp_path / "abstention.jsonl"
    abstention_path.write_text(
        json.dumps({"id": "a0", "question": "What is the answer?", "should_abstain": True}) + "\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "outputs"
    config = {
        "backend": "mock",
        "prompt_protocol": "official_natural",
        "benchmarks": [{"name": "abstentionbench", "source": "local", "path": str(abstention_path)}],
        "systems": ["base_single"],
        "judge": {"backend": "mock"},
        "output_dir": str(output_dir),
    }
    summary = run_experiment(config)
    record = json.loads((output_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["judge_output"]["label"] == "ANSWER"
    assert "judge_answer_rate" in summary["by_benchmark_system"]["abstentionbench"]["base_single"]


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


def test_load_samples_filters_and_orders_by_manifest(tmp_path):
    abstention_path = tmp_path / "abstention.jsonl"
    rows = [
        {"id": "a0", "question": "Q0", "should_abstain": False},
        {"id": "a1", "question": "Q1", "should_abstain": True},
        {"id": "a2", "question": "Q2", "should_abstain": False},
    ]
    abstention_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    manifest_path = tmp_path / "manifest.jsonl"
    manifest_path.write_text(
        json.dumps({"sample_id": "a2"}) + "\n" + json.dumps({"sample_id": "a0"}) + "\n",
        encoding="utf-8",
    )

    samples = load_samples(
        {
            "benchmarks": [
                {
                    "name": "abstentionbench",
                    "source": "local",
                    "path": str(abstention_path),
                    "manifest_path": str(manifest_path),
                }
            ]
        }
    )

    assert [sample.sample_id for sample in samples] == ["a2", "a0"]


def test_load_samples_manifest_only_filters_its_own_benchmark(tmp_path):
    gpqa_path = tmp_path / "gpqa.csv"
    gpqa_path.write_text(
        "Question,Correct Answer,Incorrect Answer 1,Incorrect Answer 2,Incorrect Answer 3\n"
        "What is true?,Right,Wrong1,Wrong2,Wrong3\n",
        encoding="utf-8",
    )
    abstention_path = tmp_path / "abstention.jsonl"
    abstention_path.write_text(
        json.dumps({"id": "a0", "question": "Q0", "should_abstain": False}) + "\n"
        + json.dumps({"id": "a1", "question": "Q1", "should_abstain": True}) + "\n",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.jsonl"
    manifest_path.write_text(json.dumps({"sample_id": "a1"}) + "\n", encoding="utf-8")

    samples = load_samples(
        {
            "benchmarks": [
                {"name": "gpqa", "path": str(gpqa_path), "limit": 1},
                {
                    "name": "abstentionbench",
                    "source": "local",
                    "path": str(abstention_path),
                    "manifest_path": str(manifest_path),
                },
            ]
        }
    )

    assert [sample.sample_id for sample in samples] == ["gpqa_0", "a1"]
