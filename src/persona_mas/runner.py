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
        if name == "gpqa":
            samples.extend(load_gpqa_csv(bench["path"], limit=limit, seed=bench.get("seed", 0)))
        elif name == "abstentionbench":
            if bench.get("source", "local") == "hf":
                samples.extend(load_abstention_hf(limit=limit))
            else:
                samples.extend(load_abstention_jsonl(bench["path"], limit=limit))
        elif name == "deceptionbench":
            prompt_field = bench.get("prompt_field", "question")
            if bench.get("source", "local") == "hf":
                samples.extend(load_deception_hf(limit=limit, prompt_field=prompt_field))
            else:
                samples.extend(load_deception_jsonl(bench["path"], limit=limit, prompt_field=prompt_field))
        else:
            raise ValueError(f"Unsupported benchmark: {name}")
    return samples


def _agent_call(backend: Any, sample: BenchmarkSample, agent: str) -> AgentOutput:
    prompt = build_independent_prompt(sample, agent)
    raw = backend.generate(agent, prompt)
    parsed = parse_for_benchmark(sample.benchmark, raw)
    return AgentOutput(agent=agent, prompt=prompt, raw_text=raw, parsed=parsed)


def _single_record(backend: Any, sample: BenchmarkSample, agent: str, system: str, judge: Any | None) -> RunRecord:
    output = _agent_call(backend, sample, agent)
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


def _voting_record(backend: Any, sample: BenchmarkSample, personas: list[str], judge: Any | None) -> RunRecord:
    outputs = {agent: _agent_call(backend, sample, agent) for agent in personas}
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


def _c_record(backend: Any, sample: BenchmarkSample, personas: list[str], c1: bool, judge: Any | None) -> RunRecord:
    initial_agent_outputs = {agent: _agent_call(backend, sample, agent) for agent in personas}
    initial = {agent: output.parsed for agent, output in initial_agent_outputs.items()}
    debate: dict[str, ParsedOutput] | None = None
    all_outputs = dict(initial_agent_outputs)
    if c1:
        debate = {}
        for agent, own in initial.items():
            others = {other: output for other, output in initial.items() if other != agent}
            prompt = build_debate_prompt(sample, agent, own, others)
            raw = backend.generate(agent, prompt)
            parsed = parse_debate_round_output(raw)
            all_outputs[f"{agent}_round1"] = AgentOutput(agent=f"{agent}_round1", prompt=prompt, raw_text=raw, parsed=parsed)
            debate[agent] = parsed
    synth_prompt = build_synthesizer_prompt(sample, initial, debate)
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
    systems = set(config.get("systems", ["base_single"]))
    output_dir = Path(config.get("output_dir", "outputs/smoke"))
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[RunRecord] = []
    samples = load_samples(config)
    for sample_index, sample in enumerate(samples, start=1):
        print(f"[{sample_index}/{len(samples)}] {sample.benchmark}/{sample.sample_id}", flush=True)
        if "base_single" in systems:
            records.append(_single_record(backend, sample, "base", "base_single", judge))
        if "persona_voting" in systems and sample.benchmark in {"gpqa", "abstentionbench"}:
            records.append(_voting_record(backend, sample, personas, judge))
        if "persona_c0" in systems:
            records.append(_c_record(backend, sample, personas, c1=False, judge=judge))
        if "persona_c1" in systems:
            records.append(_c_record(backend, sample, personas, c1=True, judge=judge))
    records_path = output_dir / "records.jsonl"
    with records_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, default=_json_default) + "\n")
    summary = summarize_records(records)
    summary.update({"output_dir": str(output_dir), "records_path": str(records_path)})
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
