from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def first_existing(paths: list[str]) -> tuple[str, str]:
    for path in paths:
        if Path(path).exists():
            return path, path
    raise FileNotFoundError(f"None of these records files exist: {paths}")


def load_records(path: str) -> dict[str, dict[str, dict[str, Any]]]:
    by_sample: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            by_sample[record["sample_id"]][record["system"]] = record
    return by_sample


def metric(record: dict[str, Any] | None, key: str) -> Any:
    return ((record or {}).get("metrics") or {}).get(key)


def judge_label(record: dict[str, Any] | None) -> str | None:
    return ((record or {}).get("judge_output") or {}).get("label")


def decision(record: dict[str, Any] | None) -> str | None:
    return ((record or {}).get("final_output") or {}).get("decision")


def clipped(value: Any, limit: int = 1600) -> str:
    text = "" if value is None else str(value).strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def prompt_question(record: dict[str, Any]) -> str:
    outputs = record.get("agent_outputs") or {}
    first = next(iter(outputs.values())) if outputs else {}
    prompt = (first.get("prompt") or "").strip()
    for marker in ["Respond exactly in this format:", "You are the base model synthesizer."]:
        if marker in prompt:
            prompt = prompt.split(marker)[0].strip()
    return clipped(prompt, 2200)


def agent_raw(record: dict[str, Any], agent: str) -> str:
    output = (record.get("agent_outputs") or {}).get(agent) or {}
    parsed = output.get("parsed") or {}
    return "\n".join(
        [
            f"decision={parsed.get('decision')}",
            f"response={clipped(parsed.get('final_response'), 500)}",
            f"reason={clipped(parsed.get('reason'), 500)}",
            "raw:",
            clipped(output.get("raw_text"), 1200),
        ]
    )


def final_block(record: dict[str, Any]) -> str:
    final = record.get("final_output") or {}
    return "\n".join(
        [
            f"decision={final.get('decision')}",
            f"response={clipped(final.get('final_response'), 700)}",
            f"reason={clipped(final.get('reason'), 700)}",
            "raw:",
            clipped(final.get("raw_text"), 1200),
        ]
    )


def status_line(record: dict[str, Any]) -> str:
    parts = [f"decision={decision(record)}"]
    metrics = record.get("metrics") or {}
    if "correct" in metrics:
        parts.append(f"correct={metrics['correct']}")
    if "correct_abstention_decision" in metrics:
        parts.append(f"abstention_correct={metrics['correct_abstention_decision']}")
    if judge_label(record):
        parts.append(f"judge={judge_label(record)}")
    return ", ".join(parts)


def write_case(parts: list[str], title: str, sample: dict[str, dict[str, Any]], reason: str) -> None:
    base = sample.get("base_single") or next(iter(sample.values()))
    systems = ["base_single", "mathematical_single", "goodness_single", "remorse_single", "persona_c0", "persona_c1"]
    parts.extend(
        [
            f"## {title}",
            "",
            f"Selection reason: {reason}",
            "",
            "**Question / Scenario**",
            "",
            "```text",
            prompt_question(base),
            "```",
            "",
            "**Gold / Metadata**",
            "",
            "```json",
            json.dumps(base.get("gold"), ensure_ascii=False, indent=2),
            "```",
            "",
            "**System Summary**",
            "",
        ]
    )
    for system in systems:
        if system in sample:
            parts.append(f"- `{system}`: {status_line(sample[system])}")
    parts.extend(["", "**Base / Single Persona Raw Outputs**", ""])
    for system, agent in [
        ("base_single", "base"),
        ("mathematical_single", "mathematical"),
        ("goodness_single", "goodness"),
        ("remorse_single", "remorse"),
    ]:
        if system in sample:
            parts.extend([f"### {system}", "```text", agent_raw(sample[system], agent), "```", ""])
    for system in ["persona_c0", "persona_c1"]:
        if system in sample:
            parts.extend([f"### {system} final", "```text", final_block(sample[system]), "```", ""])
            if system == "persona_c1":
                parts.extend([f"### {system} agent flow", ""])
                for agent in [
                    "mathematical",
                    "goodness",
                    "remorse",
                    "mathematical_round1",
                    "goodness_round1",
                    "remorse_round1",
                ]:
                    if agent in (sample[system].get("agent_outputs") or {}):
                        parts.extend([f"#### {agent}", "```text", agent_raw(sample[system], agent), "```", ""])
    parts.extend(["---", ""])


def first_case(samples: dict[str, dict[str, dict[str, Any]]], predicate) -> tuple[str, dict[str, dict[str, Any]]] | None:
    for sample_id, sample in samples.items():
        if predicate(sample):
            return sample_id, sample
    return None


def main() -> None:
    gpqa_path, gpqa_label = first_existing(
        [
            "outputs/gpqa_cot_n50_fast768/records.jsonl",
            "outputs/gpqa_full/records.jsonl",
        ]
    )
    deception_path, deception_label = first_existing(
        [
            "outputs/deception_l1_self_n50/records.jsonl",
            "outputs/deception_n100/records.jsonl",
        ]
    )
    abstention_path, abstention_label = first_existing(
        [
            "outputs/abstention_natural_n50/records.jsonl",
            "outputs/abstention_n100/records.jsonl",
        ]
    )
    gpqa = load_records(gpqa_path)
    deception = load_records(deception_path)
    abstention = load_records(abstention_path)

    selected: list[tuple[str, str, dict[str, dict[str, Any]], str]] = []
    candidates = [
        (
            "GPQA: C1 correct, base wrong",
            gpqa,
            lambda s: metric(s.get("base_single"), "correct") is False
            and metric(s.get("persona_c1"), "correct") is True,
            "C1 修正了 base 的错误",
        ),
        (
            "GPQA: base correct, C1 wrong",
            gpqa,
            lambda s: metric(s.get("base_single"), "correct") is True
            and metric(s.get("persona_c1"), "correct") is False,
            "C1/debate 反而破坏正确答案",
        ),
        (
            "Deception: C1 reduces deception",
            deception,
            lambda s: judge_label(s.get("base_single")) == "DECEPTIVE"
            and judge_label(s.get("persona_c1")) in {"HONEST", "REFUSAL"},
            "base 被判 deceptive，C1 变成 honest/refusal",
        ),
        (
            "Deception: C1 worse than base",
            deception,
            lambda s: judge_label(s.get("base_single")) in {"HONEST", "REFUSAL"}
            and judge_label(s.get("persona_c1")) == "DECEPTIVE",
            "base 非 deceptive，C1 被判 deceptive",
        ),
        (
            "Abstention: C1 correct, base wrong",
            abstention,
            lambda s: metric(s.get("base_single"), "correct_abstention_decision") is False
            and metric(s.get("persona_c1"), "correct_abstention_decision") is True,
            "C1 的拒答/回答判断修正了 base",
        ),
        (
            "Abstention: base correct, C1 wrong",
            abstention,
            lambda s: metric(s.get("base_single"), "correct_abstention_decision") is True
            and metric(s.get("persona_c1"), "correct_abstention_decision") is False,
            "C1 的拒答/回答判断比 base 更差",
        ),
    ]
    for title, samples, predicate, reason in candidates:
        case = first_case(samples, predicate)
        if case:
            sample_id, sample = case
            selected.append((title, sample_id, sample, reason))

    parts = [
        "# Three Benchmark Qualitative Examples",
        "",
        "Diagnostic cases from the currently available records files.",
        "",
        "Source files:",
        "",
        f"- GPQA: `{gpqa_label}`",
        f"- DeceptionBench: `{deception_label}`",
        f"- AbstentionBench: `{abstention_label}`",
        "",
    ]
    for title, sample_id, sample, reason in selected:
        write_case(parts, f"{title} ({sample_id})", sample, reason)

    output = Path("analysis_examples/three_benchmark_n50_examples.md")
    output.parent.mkdir(exist_ok=True)
    output.write_text("\n".join(parts), encoding="utf-8")
    print(output)
    print(f"examples={len(selected)}")
    for title, sample_id, _, reason in selected:
        print(f"- {title}: {sample_id} ({reason})")


if __name__ == "__main__":
    main()
