import json

from persona_mas.export_hf_datasets import normalize_abstention_row, normalize_deception_row, select_default_split, write_jsonl


def test_normalize_abstention_row_preserves_loader_fields():
    row = {
        "id": "a1",
        "question": "Known?",
        "reference_answers": ["yes"],
        "should_abstain": False,
        "metadata_json": {"subset": "alcuna"},
    }

    record = normalize_abstention_row(row, 0)

    assert record == row


def test_normalize_abstention_row_parses_metadata_json_string():
    row = {
        "question": "Known?",
        "reference_answers": [],
        "should_abstain": True,
        "metadata_json": '{"source": "alcuna"}',
    }

    record = normalize_abstention_row(row, 3)

    assert record["id"] == "abstention_3"
    assert record["metadata_json"] == {"source": "alcuna"}


def test_normalize_deception_row_preserves_prompt_variants_and_gold():
    row = {
        "id": "d1",
        "question": "Question",
        "groundtruth": "Tell the truth.",
        "goal": "Mislead.",
        "L1-self": "Prompt variant",
        "topic": "sales",
    }

    record = normalize_deception_row(row, 0)

    assert record["id"] == "d1"
    assert record["question"] == "Question"
    assert record["groundtruth"] == "Tell the truth."
    assert record["goal"] == "Mislead."
    assert record["L1-self"] == "Prompt variant"
    assert record["topic"] == "sales"


def test_write_jsonl_writes_one_json_object_per_line(tmp_path):
    output = tmp_path / "nested" / "records.jsonl"
    records = [{"id": "1"}, {"id": "2"}]

    count = write_jsonl(records, output)

    assert count == 2
    lines = output.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["id"] for line in lines] == ["1", "2"]


def test_select_default_split_accepts_single_dataset():
    class SingleDataset:
        column_names = ["question"]

    dataset = SingleDataset()

    assert select_default_split(dataset, None) is dataset


def test_select_default_split_prefers_train_from_dataset_dict():
    dataset = {"validation": [1], "train": [2]}

    assert select_default_split(dataset, None) == [2]
