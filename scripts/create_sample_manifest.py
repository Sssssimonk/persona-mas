from __future__ import annotations

import argparse

from persona_mas.sample_manifest import build_gpqa_manifest, build_jsonl_manifest, read_jsonl, write_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True, choices=["gpqa", "abstentionbench", "deceptionbench"])
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample-size", type=int, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--split")
    args = parser.parse_args()

    if args.benchmark == "gpqa":
        rows = build_gpqa_manifest(args.input, args.sample_size, args.seed, split=args.split)
    else:
        rows = build_jsonl_manifest(read_jsonl(args.input), args.benchmark, args.sample_size, args.seed, split=args.split)
    write_manifest(rows, args.output)
    print(f"wrote {len(rows)} samples to {args.output}")


if __name__ == "__main__":
    main()
