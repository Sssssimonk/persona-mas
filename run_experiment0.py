from __future__ import annotations

import argparse
import json

from persona_mas.runner import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Experiment 0 persona MAS harness.")
    parser.add_argument("--config", required=True, help="Path to JSON config.")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as handle:
        config = json.load(handle)
    summary = run_experiment(config)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

