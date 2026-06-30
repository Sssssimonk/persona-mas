from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


def _round_robin_stratified(rows: list[dict[str, Any]], strata_key, sample_size: int, seed: int) -> list[dict[str, Any]]:
    groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[strata_key(row)].append(row)
    rng = random.Random(seed)
    for group_rows in groups.values():
        rng.shuffle(group_rows)

    selected: list[dict[str, Any]] = []
    group_keys = sorted(groups, key=lambda key: str(key))
    while len(selected) < sample_size and any(groups[key] for key in group_keys):
        for key in group_keys:
            if groups[key]:
                selected.append(groups[key].pop(0))
                if len(selected) >= sample_size:
                    break
    return selected


def build_jsonl_manifest(
    records: list[dict[str, Any]],
    benchmark: str,
    sample_size: int,
    seed: int,
    split: str | None = None,
) -> list[dict[str, Any]]:
    if benchmark == "abstentionbench":
        selected = _round_robin_stratified(records, lambda row: bool(row.get("should_abstain")), sample_size, seed)
        return [
            {
                "benchmark": benchmark,
                "sample_id": str(row.get("id", f"abstention_{index}")),
                "split": split or f"{benchmark}_n{sample_size}_seed{seed}",
                "seed": seed,
                "strata": {"should_abstain": bool(row.get("should_abstain"))},
            }
            for index, row in enumerate(selected)
        ]
    if benchmark == "deceptionbench":
        selected = _round_robin_stratified(
            records,
            lambda row: (row.get("topic", "unknown"), row.get("dimension", "unknown")),
            sample_size,
            seed,
        )
        return [
            {
                "benchmark": benchmark,
                "sample_id": str(row.get("id", f"deception_{index}")),
                "split": split or f"{benchmark}_n{sample_size}_seed{seed}",
                "seed": seed,
                "strata": {"topic": row.get("topic"), "dimension": row.get("dimension")},
            }
            for index, row in enumerate(selected)
        ]
    raise ValueError(f"Unsupported JSONL benchmark: {benchmark}")


def build_gpqa_manifest(path: str | Path, sample_size: int, seed: int, split: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle)):
            rows.append({"sample_id": f"gpqa_{index}", "domain": row.get("High-level domain"), "subdomain": row.get("Subdomain")})
    rng = random.Random(seed)
    if sample_size < len(rows):
        rows = sorted(rng.sample(rows, sample_size), key=lambda row: int(row["sample_id"].split("_")[1]))
    return [
        {
            "benchmark": "gpqa",
            "sample_id": row["sample_id"],
            "split": split or f"gpqa_n{sample_size}_seed{seed}",
            "seed": seed,
            "strata": {"domain": row.get("domain"), "subdomain": row.get("subdomain")},
        }
        for row in rows[:sample_size]
    ]


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_manifest(rows: list[dict[str, Any]], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
