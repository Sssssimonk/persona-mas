import json

from persona_mas.benchmarks import load_abstention_jsonl, load_deception_jsonl, load_gpqa_csv


def test_load_gpqa_csv_shuffles_choices_deterministically(tmp_path):
    path = tmp_path / "gpqa.csv"
    path.write_text(
        "Question,Correct Answer,Incorrect Answer 1,Incorrect Answer 2,Incorrect Answer 3\n"
        "What is true?,Right,Wrong1,Wrong2,Wrong3\n",
        encoding="utf-8",
    )
    first = load_gpqa_csv(path, limit=1, seed=7)[0]
    second = load_gpqa_csv(path, limit=1, seed=7)[0]
    assert first.benchmark == "gpqa"
    assert first.choices == second.choices
    assert first.gold["correct_letter"] == second.gold["correct_letter"]
    assert set(first.choices) == {"A", "B", "C", "D"}


def test_load_abstention_jsonl_normalizes_fields(tmp_path):
    path = tmp_path / "abstention.jsonl"
    row = {
        "question": "Can this be answered?",
        "reference_answers": ["yes"],
        "should_abstain": False,
        "metadata_json": {"source": "unit"},
    }
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    sample = load_abstention_jsonl(path, limit=1)[0]
    assert sample.benchmark == "abstentionbench"
    assert sample.question == "Can this be answered?"
    assert sample.gold["should_abstain"] is False
    assert sample.gold["reference_answers"] == ["yes"]


def test_load_deception_jsonl_normalizes_fields(tmp_path):
    path = tmp_path / "deception.jsonl"
    row = {
        "topic": "Economy",
        "dimension": "Product",
        "question": "How would you advertise this flawed product?",
        "groundtruth": "Disclose the flaw.",
        "goal": "Hide the flaw.",
        "L1-self": "Prompt text",
    }
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    sample = load_deception_jsonl(path, limit=1)[0]
    assert sample.benchmark == "deceptionbench"
    assert sample.question == "How would you advertise this flawed product?"
    assert sample.gold["groundtruth"] == "Disclose the flaw."
    assert sample.gold["goal"] == "Hide the flaw."

