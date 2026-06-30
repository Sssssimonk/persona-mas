from __future__ import annotations

import argparse
import importlib.machinery
import json
import ssl
import sys
import types
from pathlib import Path
from typing import Any, Iterable


def _install_torch_stub_if_needed() -> None:
    try:
        import torch  # noqa: F401

        return
    except ImportError:
        pass

    class Dataset:
        pass

    class Tensor:
        pass

    class Generator:
        pass

    class Module:
        pass

    torch = types.ModuleType("torch")
    torch.__spec__ = importlib.machinery.ModuleSpec("torch", loader=None)
    torch.Tensor = Tensor
    torch.Generator = Generator
    torch_utils = types.ModuleType("torch.utils")
    torch_utils.__spec__ = importlib.machinery.ModuleSpec("torch.utils", loader=None)
    torch_data = types.ModuleType("torch.utils.data")
    torch_data.__spec__ = importlib.machinery.ModuleSpec("torch.utils.data", loader=None)
    torch_data.Dataset = Dataset
    torch_nn = types.ModuleType("torch.nn")
    torch_nn.__spec__ = importlib.machinery.ModuleSpec("torch.nn", loader=None)
    torch_nn.Module = Module
    torch_utils.data = torch_data
    torch.utils = torch_utils
    torch.nn = torch_nn
    sys.modules["torch"] = torch
    sys.modules["torch.utils"] = torch_utils
    sys.modules["torch.utils.data"] = torch_data
    sys.modules["torch.nn"] = torch_nn


def normalize_abstention_row(row: dict[str, Any], idx: int) -> dict[str, Any]:
    metadata_json = row.get("metadata_json", {})
    if isinstance(metadata_json, str):
        metadata_json = json.loads(metadata_json) if metadata_json else {}
    return {
        "id": row.get("id", f"abstention_{idx}"),
        "question": row["question"],
        "reference_answers": list(row.get("reference_answers") or []),
        "should_abstain": bool(row["should_abstain"]),
        "metadata_json": metadata_json,
    }


def normalize_deception_row(row: dict[str, Any], idx: int) -> dict[str, Any]:
    record = dict(row)
    record.setdefault("id", f"deception_{idx}")
    record["question"] = record["question"]
    record["groundtruth"] = record.get("groundtruth")
    record["goal"] = record.get("goal")
    return record


def write_jsonl(records: Iterable[dict[str, Any]], output_path: str | Path) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def select_default_split(dataset, split_name: str | None):
    if split_name:
        return dataset[split_name]
    if hasattr(dataset, "column_names"):
        return dataset
    if "train" in dataset:
        return dataset["train"]
    return next(iter(dataset.values()))


def _load_hf_split(dataset_name: str, split_name: str | None, trust_remote_code: bool):
    from datasets import load_dataset

    dataset = load_dataset(dataset_name, trust_remote_code=trust_remote_code)
    return select_default_split(dataset, split_name)


def _normalized_rows(split, normalizer, limit: int | None):
    for idx, row in enumerate(split):
        if limit is not None and idx >= limit:
            break
        yield normalizer(row, idx)


def export_dataset(dataset_key: str, output_path: str | Path, limit: int | None = None, split_name: str | None = None) -> int:
    ssl._create_default_https_context = ssl._create_unverified_context
    _install_torch_stub_if_needed()
    if dataset_key == "abstentionbench":
        split = _load_hf_split("facebook/AbstentionBench", split_name, trust_remote_code=True)
        rows = _normalized_rows(split, normalize_abstention_row, limit)
    elif dataset_key == "deceptionbench":
        split = _load_hf_split("skyai798/DeceptionBench", split_name, trust_remote_code=False)
        rows = _normalized_rows(split, normalize_deception_row, limit)
    else:
        raise ValueError(f"Unsupported dataset key: {dataset_key}")
    return write_jsonl(rows, output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", choices=["abstentionbench", "deceptionbench"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--split")
    args = parser.parse_args()

    count = export_dataset(args.dataset, args.output, limit=args.limit, split_name=args.split)
    print(f"wrote {count} records to {args.output}")


if __name__ == "__main__":
    main()
