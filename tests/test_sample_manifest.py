import json

from persona_mas.sample_manifest import build_jsonl_manifest, build_gpqa_manifest


def test_build_jsonl_manifest_balances_abstention_labels():
    records = [
        {"id": "a0", "should_abstain": False},
        {"id": "a1", "should_abstain": False},
        {"id": "a2", "should_abstain": True},
        {"id": "a3", "should_abstain": True},
    ]

    manifest = build_jsonl_manifest(records, benchmark="abstentionbench", sample_size=4, seed=0)

    assert [row["sample_id"] for row in manifest] == ["a0", "a2", "a1", "a3"]
    assert {row["strata"]["should_abstain"] for row in manifest} == {False, True}


def test_build_jsonl_manifest_covers_deception_topic_dimension_strata():
    records = [
        {"id": "d0", "topic": "Economy", "dimension": "A"},
        {"id": "d1", "topic": "Economy", "dimension": "B"},
        {"id": "d2", "topic": "Health", "dimension": "C"},
    ]

    manifest = build_jsonl_manifest(records, benchmark="deceptionbench", sample_size=3, seed=0)

    assert [row["sample_id"] for row in manifest] == ["d0", "d1", "d2"]
    assert [row["strata"]["topic"] for row in manifest] == ["Economy", "Economy", "Health"]


def test_build_gpqa_manifest_uses_stable_generated_sample_ids(tmp_path):
    path = tmp_path / "gpqa.csv"
    path.write_text(
        "Question,Correct Answer,Incorrect Answer 1,Incorrect Answer 2,Incorrect Answer 3,High-level domain\n"
        "Q0,Right,W1,W2,W3,Physics\n"
        "Q1,Right,W1,W2,W3,Chemistry\n",
        encoding="utf-8",
    )

    manifest = build_gpqa_manifest(path, sample_size=2, seed=0)

    assert [row["sample_id"] for row in manifest] == ["gpqa_0", "gpqa_1"]
    assert [row["strata"]["domain"] for row in manifest] == ["Physics", "Chemistry"]


def test_manifest_rows_are_json_serializable():
    manifest = build_jsonl_manifest([{"id": "x0", "should_abstain": True}], "abstentionbench", 1, 0)

    assert json.loads(json.dumps(manifest[0]))["sample_id"] == "x0"
