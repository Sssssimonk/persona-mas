from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from persona_mas.runner import load_samples


SYSTEM_ORDER = [
    "base_single",
    "mathematical_single",
    "goodness_single",
    "remorse_single",
    "persona_voting",
    "persona_c0",
    "persona_c1",
]


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _fenced(text: Any, lang: str = "text") -> str:
    if text is None:
        text = ""
    return f"```{lang}\n{str(text).strip()}\n```"


def _json_fenced(value: Any) -> str:
    return _fenced(json.dumps(value, ensure_ascii=False, indent=2), "json")


def _sample_block(sample: Any) -> str:
    parts = [
        f"### {sample.benchmark} / {sample.sample_id}",
        "",
        "**Question**",
        "",
        _fenced(sample.question),
    ]
    if sample.choices:
        parts.extend(["", "**Choices**", "", _json_fenced(sample.choices)])
    parts.extend(["", "**Gold / Metadata**", "", _json_fenced({"gold": sample.gold, "metadata": sample.metadata})])
    return "\n".join(parts)


def _agent_output_block(agent_name: str, output: dict[str, Any]) -> str:
    parsed = output.get("parsed", {})
    parts = [
        f"#### Agent output: {agent_name}",
        "",
        "**Parsed**",
        "",
        _json_fenced(parsed),
        "",
        "**Raw output**",
        "",
        _fenced(output.get("raw_text", "")),
    ]
    return "\n".join(parts)


def _record_block(record: dict[str, Any]) -> str:
    parts = [
        f"### System: {record['system']} ({record['aggregation']})",
        "",
        "**Final output**",
        "",
        _json_fenced(record.get("final_output")),
    ]
    if record.get("judge_output") is not None:
        parts.extend(["", "**Judge output**", "", _json_fenced(record["judge_output"])])
    parts.extend(["", "**Metrics**", "", _json_fenced(record.get("metrics", {}))])

    agent_outputs = record.get("agent_outputs", {})
    for agent_name in sorted(agent_outputs):
        parts.extend(["", _agent_output_block(agent_name, agent_outputs[agent_name])])
    return "\n".join(parts)


def _ordered_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = {system: index for index, system in enumerate(SYSTEM_ORDER)}
    return sorted(records, key=lambda record: order.get(record["system"], 999))


def append_benchmark(
    chunks: list[str],
    title: str,
    config_path: str,
    output_dir: str,
    note: str | None = None,
) -> None:
    config = _read_json(config_path)
    samples = {sample.sample_id: sample for sample in load_samples(config)}
    records = _read_jsonl(Path(output_dir) / "records.jsonl")
    summary = _read_json(Path(output_dir) / "summary.json")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["sample_id"]].append(record)

    chunks.extend([f"## {title}", ""])
    if note:
        chunks.extend([note, ""])
    chunks.extend(["**Summary**", "", _json_fenced(summary), ""])
    for sample_id in sorted(grouped):
        chunks.extend([_sample_block(samples[sample_id]), ""])
        for record in _ordered_records(grouped[sample_id]):
            chunks.extend([_record_block(record), ""])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="analysis_examples/protocol_v1_trial_examples.md")
    args = parser.parse_args()

    chunks = [
        "# Protocol v1 Trial Complete Reply Examples",
        "",
        "This file contains two full reply-flow examples per benchmark from the protocol v1 trial runs.",
        "Prompts are not repeated in full; the original question, agent raw outputs, final synthesizer outputs, judge labels, and metrics are preserved.",
        "",
    ]
    append_benchmark(
        chunks,
        "GPQA Diamond / official_cot / n=2",
        "configs/experiment0_gpqa_cot_trial2.json",
        "outputs/protocol_v1_trial_gpqa_cot_n2",
    )
    append_benchmark(
        chunks,
        "AbstentionBench / official_natural / unanswerable n=2",
        "configs/experiment0_abstention_natural_unanswerable_trial2.json",
        "outputs/protocol_v1_trial_abstention_unanswerable_n2",
        note="These two examples are selected from `should_abstain=true` samples (`abstention_3`, `abstention_4`) rather than the first two dataset rows.",
    )
    append_benchmark(
        chunks,
        "DeceptionBench / L1-self JSON / n=2",
        "configs/experiment0_deception_l1_self_trial2.json",
        "outputs/protocol_v1_trial_deception_l1_self_n2",
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(chunks), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
