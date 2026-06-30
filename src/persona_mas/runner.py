from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from persona_mas.aggregation import majority_vote
from persona_mas.benchmarks import (
    load_abstention_hf,
    load_abstention_jsonl,
    load_deception_hf,
    load_deception_jsonl,
    load_gpqa_csv,
)
from persona_mas.generation import HFPersonaBackend, MockBackend
from persona_mas.judge import DeepSeekJudge, MockJudge
from persona_mas.metrics import summarize_records
from persona_mas.parsing import parse_debate_round_output, parse_for_benchmark, parse_synthesizer_output
from persona_mas.prompts import build_debate_prompt, build_independent_prompt, build_synthesizer_prompt
from persona_mas.schemas import AgentOutput, BenchmarkSample, ParsedOutput, RunRecord


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def load_samples(config: dict[str, Any]) -> list[BenchmarkSample]:
    samples: list[BenchmarkSample] = []
    for bench in config["benchmarks"]:
        name = bench["name"]
        limit = bench.get("limit")
        batch: list[BenchmarkSample]
        if name == "gpqa":
            batch = load_gpqa_csv(bench["path"], limit=limit, seed=bench.get("seed", 0))
        elif name == "abstentionbench":
            if bench.get("source", "local") == "hf":
                batch = load_abstention_hf(limit=limit)
            else:
                batch = load_abstention_jsonl(bench["path"], limit=limit)
        elif name == "deceptionbench":
            prompt_field = bench.get("prompt_field", "question")
            if bench.get("source", "local") == "hf":
                batch = load_deception_hf(limit=limit, prompt_field=prompt_field)
            else:
                batch = load_deception_jsonl(bench["path"], limit=limit, prompt_field=prompt_field)
        else:
            raise ValueError(f"Unsupported benchmark: {name}")
        if bench.get("manifest_path"):
            batch = _filter_samples_by_manifest(batch, bench["manifest_path"])
        samples.extend(batch)
    return samples


def _filter_samples_by_manifest(samples: list[BenchmarkSample], manifest_path: str | Path) -> list[BenchmarkSample]:
    by_id = {sample.sample_id: sample for sample in samples}
    selected: list[BenchmarkSample] = []
    with Path(manifest_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            sample_id = str(row["sample_id"])
            if sample_id not in by_id:
                raise ValueError(f"Manifest sample_id not found: {sample_id}")
            selected.append(by_id[sample_id])
    return selected


def _agent_call(backend: Any, sample: BenchmarkSample, agent: str, persona_prompt_mode: str = "none") -> AgentOutput:
    prompt = build_independent_prompt(sample, agent, persona_prompt_mode=persona_prompt_mode)
    raw = backend.generate(agent, prompt)
    parsed = parse_for_benchmark(sample.benchmark, raw)
    return AgentOutput(agent=agent, prompt=prompt, raw_text=raw, parsed=parsed)


def _single_record(
    backend: Any,
    sample: BenchmarkSample,
    agent: str,
    system: str,
    judge: Any | None,
    persona_prompt_mode: str = "none",
) -> RunRecord:
    output = _agent_call(backend, sample, agent, persona_prompt_mode=persona_prompt_mode)
    return RunRecord(
        benchmark=sample.benchmark,
        sample_id=sample.sample_id,
        system=system,
        aggregation="single",
        agent_outputs={agent: output},
        final_output=output.parsed,
        gold=sample.gold,
        judge_output=_judge_if_needed(judge, sample, output.parsed),
        metrics=_basic_metrics(sample, output.parsed),
    )


def _persona_initial_outputs(
    backend: Any,
    sample: BenchmarkSample,
    personas: list[str],
    cache: dict[str, AgentOutput],
    persona_prompt_mode: str,
) -> dict[str, AgentOutput]:
    for agent in personas:
        if agent not in cache:
            cache[agent] = _agent_call(backend, sample, agent, persona_prompt_mode=persona_prompt_mode)
    return {agent: cache[agent] for agent in personas}


def _agent_labels(personas: list[str]) -> dict[str, str]:
    return {agent: f"Agent {chr(65 + index)}" for index, agent in enumerate(personas)}


def _voting_record(
    backend: Any,
    sample: BenchmarkSample,
    personas: list[str],
    judge: Any | None,
    initial_cache: dict[str, AgentOutput],
    persona_prompt_mode: str,
) -> RunRecord:
    outputs = _persona_initial_outputs(backend, sample, personas, initial_cache, persona_prompt_mode)
    final = majority_vote([output.parsed for output in outputs.values()])
    return RunRecord(
        benchmark=sample.benchmark,
        sample_id=sample.sample_id,
        system="persona_voting",
        aggregation="voting",
        agent_outputs=outputs,
        final_output=final,
        gold=sample.gold,
        judge_output=_judge_if_needed(judge, sample, final),
        metrics=_basic_metrics(sample, final),
    )


def _c_record(
    backend: Any,
    sample: BenchmarkSample,
    personas: list[str],
    c1: bool,
    judge: Any | None,
    initial_cache: dict[str, AgentOutput],
    persona_prompt_mode: str,
) -> RunRecord:
    initial_agent_outputs = _persona_initial_outputs(backend, sample, personas, initial_cache, persona_prompt_mode)
    initial = {agent: output.parsed for agent, output in initial_agent_outputs.items()}
    debate: dict[str, ParsedOutput] | None = None
    all_outputs = dict(initial_agent_outputs)
    labels = _agent_labels(personas)
    if c1:
        debate = {}
        for agent, own in initial.items():
            others = {other: output for other, output in initial.items() if other != agent}
            prompt = build_debate_prompt(
                sample,
                agent,
                own,
                others,
                persona_prompt_mode=persona_prompt_mode,
                agent_labels=labels,
            )
            raw = backend.generate(agent, prompt)
            parsed = parse_debate_round_output(raw)
            all_outputs[f"{agent}_round1"] = AgentOutput(agent=f"{agent}_round1", prompt=prompt, raw_text=raw, parsed=parsed)
            debate[agent] = parsed
    synth_prompt = build_synthesizer_prompt(sample, initial, debate, agent_labels=labels)
    synth_raw = backend.generate("base_synthesizer", synth_prompt)
    final = parse_synthesizer_output(synth_raw)
    system = "persona_c1" if c1 else "persona_c0"
    return RunRecord(
        benchmark=sample.benchmark,
        sample_id=sample.sample_id,
        system=system,
        aggregation="c1" if c1 else "c0",
        agent_outputs=all_outputs,
        final_output=final,
        gold=sample.gold,
        judge_output=_judge_if_needed(judge, sample, final),
        metrics=_basic_metrics(sample, final),
    )


def _basic_metrics(sample: BenchmarkSample, output: ParsedOutput) -> dict[str, Any]:
    if sample.benchmark == "gpqa":
        return {"correct": output.decision == sample.gold.get("correct_letter")}
    if sample.benchmark == "abstentionbench":
        should = bool(sample.gold.get("should_abstain"))
        return {
            "correct_abstention_decision": (output.decision == "ABSTAIN") == should,
            "should_abstain": should,
        }
    return {}


def _judge_if_needed(judge: Any | None, sample: BenchmarkSample, output: ParsedOutput) -> dict[str, Any] | None:
    if judge is None:
        return None
    if sample.benchmark == "deceptionbench":
        return judge.judge_deception(sample, output)
    return None


def run_experiment(config: dict[str, Any]) -> dict[str, Any]:
    backend_name = config.get("backend", "mock")
    if backend_name == "mock":
        backend: Any = MockBackend()
    elif backend_name == "hf_peft":
        backend = HFPersonaBackend(
            model_name=config.get("model_name", "Qwen/Qwen2.5-7B-Instruct"),
            adapter_paths=config.get("adapter_paths", {}),
            max_new_tokens=int(config.get("max_new_tokens", 256)),
            torch_dtype=config.get("torch_dtype", "auto"),
        )
    else:
        raise ValueError(f"Unsupported backend: {backend_name}")
    judge_config = config.get("judge", {"backend": "none"})
    judge_backend = judge_config.get("backend", "none")
    if judge_backend == "none":
        judge = None
    elif judge_backend == "mock":
        judge = MockJudge()
    elif judge_backend == "deepseek":
        judge = DeepSeekJudge(
            model=judge_config.get("model", "deepseek-v4-flash"),
            base_url=judge_config.get("base_url"),
            api_key_env=judge_config.get("api_key_env", "DEEPSEEK_API_KEY"),
        )
    else:
        raise ValueError(f"Unsupported judge backend: {judge_backend}")
    personas = config.get("personas", ["mathematical", "goodness", "remorse"])
    persona_prompt_mode = config.get("persona_prompt_mode", "none")
    systems = set(config.get("systems", ["base_single"]))
    output_dir = Path(config.get("output_dir", "outputs/smoke"))
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[RunRecord] = []
    samples = load_samples(config)
    for sample_index, sample in enumerate(samples, start=1):
        print(f"[{sample_index}/{len(samples)}] {sample.benchmark}/{sample.sample_id}", flush=True)
        initial_cache: dict[str, AgentOutput] = {}
        if "base_single" in systems:
            records.append(_single_record(backend, sample, "base", "base_single", judge, persona_prompt_mode="none"))
        if "persona_voting" in systems and sample.benchmark in {"gpqa", "abstentionbench"}:
            records.append(_voting_record(backend, sample, personas, judge, initial_cache, persona_prompt_mode))
        if "persona_c0" in systems:
            records.append(_c_record(backend, sample, personas, c1=False, judge=judge, initial_cache=initial_cache, persona_prompt_mode=persona_prompt_mode))
        if "persona_c1" in systems:
            records.append(_c_record(backend, sample, personas, c1=True, judge=judge, initial_cache=initial_cache, persona_prompt_mode=persona_prompt_mode))
    records_path = output_dir / "records.jsonl"
    with records_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, default=_json_default) + "\n")
    summary = summarize_records(records)
    summary.update({"output_dir": str(output_dir), "records_path": str(records_path)})
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
