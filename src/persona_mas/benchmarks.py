from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Any

from persona_mas.schemas import BenchmarkSample


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_gpqa_csv(path: str | Path, limit: int | None = None, seed: int = 0) -> list[BenchmarkSample]:
    samples: list[BenchmarkSample] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader):
            options = [
                ("correct", row["Correct Answer"]),
                ("incorrect", row["Incorrect Answer 1"]),
                ("incorrect", row["Incorrect Answer 2"]),
                ("incorrect", row["Incorrect Answer 3"]),
            ]
            rng = random.Random(f"{seed}:{idx}")
            rng.shuffle(options)
            choices = {letter: text for letter, (_, text) in zip("ABCD", options)}
            correct_letter = next(letter for letter, (kind, _) in zip("ABCD", options) if kind == "correct")
            samples.append(
                BenchmarkSample(
                    sample_id=f"gpqa_{idx}",
                    benchmark="gpqa",
                    question=row["Question"],
                    choices=choices,
                    gold={"correct_letter": correct_letter, "correct_answer": row["Correct Answer"]},
                    metadata={key: value for key, value in row.items() if key not in choices},
                )
            )
            if limit is not None and len(samples) >= limit:
                break
    return samples


def load_abstention_jsonl(path: str | Path, limit: int | None = None) -> list[BenchmarkSample]:
    rows = _read_jsonl(path)
    samples: list[BenchmarkSample] = []
    for idx, row in enumerate(rows[:limit]):
        samples.append(
            BenchmarkSample(
                sample_id=str(row.get("id", f"abstention_{idx}")),
                benchmark="abstentionbench",
                question=row["question"],
                gold={
                    "should_abstain": bool(row["should_abstain"]),
                    "reference_answers": row.get("reference_answers"),
                },
                metadata={"metadata_json": row.get("metadata_json", {})},
            )
        )
    return samples


def load_deception_jsonl(path: str | Path, limit: int | None = None, prompt_field: str = "question") -> list[BenchmarkSample]:
    rows = _read_jsonl(path)
    samples: list[BenchmarkSample] = []
    for idx, row in enumerate(rows[:limit]):
        question = row.get(prompt_field) or row["question"]
        samples.append(
            BenchmarkSample(
                sample_id=str(row.get("id", f"deception_{idx}")),
                benchmark="deceptionbench",
                question=question,
                gold={"groundtruth": row.get("groundtruth"), "goal": row.get("goal")},
                metadata={key: value for key, value in row.items() if key not in {"question", "groundtruth", "goal"}},
            )
        )
    return samples


def load_abstention_hf(limit: int | None = None) -> list[BenchmarkSample]:
    from datasets import load_dataset

    dataset = load_dataset("facebook/AbstentionBench", trust_remote_code=True)
    split = dataset["train"] if "train" in dataset else next(iter(dataset.values()))
    samples: list[BenchmarkSample] = []
    for idx, row in enumerate(split):
        samples.append(
            BenchmarkSample(
                sample_id=str(row.get("id", f"abstention_{idx}")),
                benchmark="abstentionbench",
                question=row["question"],
                gold={
                    "should_abstain": bool(row["should_abstain"]),
                    "reference_answers": row.get("reference_answers"),
                },
                metadata={"metadata_json": row.get("metadata_json", {})},
            )
        )
        if limit is not None and len(samples) >= limit:
            break
    return samples


def load_deception_hf(limit: int | None = None, prompt_field: str = "question") -> list[BenchmarkSample]:
    from datasets import load_dataset

    dataset = load_dataset("skyai798/DeceptionBench")
    split = dataset["train"] if "train" in dataset else next(iter(dataset.values()))
    samples: list[BenchmarkSample] = []
    for idx, row in enumerate(split):
        question = row.get(prompt_field) or row["question"]
        samples.append(
            BenchmarkSample(
                sample_id=str(row.get("id", f"deception_{idx}")),
                benchmark="deceptionbench",
                question=question,
                gold={"groundtruth": row.get("groundtruth"), "goal": row.get("goal")},
                metadata={key: value for key, value in row.items() if key not in {"question", "groundtruth", "goal"}},
            )
        )
        if limit is not None and len(samples) >= limit:
            break
    return samples

