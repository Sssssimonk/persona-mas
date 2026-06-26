from __future__ import annotations

import argparse
import importlib.machinery
import json
import ssl
import sys
import types
from pathlib import Path


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


def main() -> None:
    ssl._create_default_https_context = ssl._create_unverified_context
    _install_torch_stub_if_needed()
    import datasets

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="benchmarks/abstentionbench/abstention_trial10.jsonl")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    abstention_bench_data = datasets.load_dataset("facebook/AbstentionBench", trust_remote_code=True)
    split = abstention_bench_data["train"] if "train" in abstention_bench_data else next(iter(abstention_bench_data.values()))

    with output_path.open("w", encoding="utf-8") as handle:
        for idx, row in enumerate(split):
            if idx >= args.limit:
                break
            record = {
                "id": row.get("id", f"abstention_real_{idx}"),
                "question": row["question"],
                "reference_answers": list(row.get("reference_answers") or []),
                "should_abstain": bool(row["should_abstain"]),
                "metadata_json": row.get("metadata_json", {}),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"wrote {args.limit} records to {output_path}")


if __name__ == "__main__":
    main()
