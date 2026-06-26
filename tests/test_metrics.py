from persona_mas.metrics import abstention_metrics, classification_accuracy, deception_metrics, summarize_records
from persona_mas.schemas import ParsedOutput, RunRecord


def test_classification_accuracy_counts_correct_decisions():
    preds = [ParsedOutput("A", "A"), ParsedOutput("B", "B")]
    assert classification_accuracy(preds, ["A", "C"]) == 0.5


def test_abstention_metrics_counts_over_and_under_abstention():
    preds = [ParsedOutput("ABSTAIN", ""), ParsedOutput("ANSWER", ""), ParsedOutput("ABSTAIN", "")]
    gold = [True, True, False]
    metrics = abstention_metrics(preds, gold)
    assert metrics["abstention_precision"] == 0.5
    assert metrics["abstention_recall"] == 0.5
    assert metrics["over_abstention_rate"] == 1.0
    assert metrics["under_abstention_rate"] == 0.5


def test_deception_metrics_counts_deceptive_labels():
    metrics = deception_metrics(["HONEST", "DECEPTIVE", "REFUSAL", "DECEPTIVE"])
    assert metrics["deception_rate"] == 0.5
    assert metrics["honest_rate"] == 0.25
    assert metrics["refusal_rate"] == 0.25


def test_summarize_records_groups_metrics_by_benchmark_and_system():
    records = [
        RunRecord(
            benchmark="gpqa",
            sample_id="q1",
            system="base_single",
            aggregation="single",
            agent_outputs={},
            final_output=ParsedOutput("A", ""),
            gold={"correct_letter": "A"},
            metrics={"correct": True},
        ),
        RunRecord(
            benchmark="gpqa",
            sample_id="q2",
            system="base_single",
            aggregation="single",
            agent_outputs={},
            final_output=ParsedOutput("B", ""),
            gold={"correct_letter": "A"},
            metrics={"correct": False},
        ),
        RunRecord(
            benchmark="deceptionbench",
            sample_id="d1",
            system="persona_c0",
            aggregation="c0",
            agent_outputs={},
            final_output=ParsedOutput("REFUSE", ""),
            gold={},
            judge_output={"label": "REFUSAL"},
        ),
    ]
    summary = summarize_records(records)
    gpqa = summary["by_benchmark_system"]["gpqa"]["base_single"]
    deception = summary["by_benchmark_system"]["deceptionbench"]["persona_c0"]
    assert gpqa["records"] == 2
    assert gpqa["correct_rate"] == 0.5
    assert deception["refusal_rate"] == 1.0
