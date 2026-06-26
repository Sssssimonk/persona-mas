from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


BenchmarkName = Literal["gpqa", "abstentionbench", "deceptionbench"]
AggregationName = Literal["single", "voting", "c0", "c1"]


@dataclass(frozen=True)
class BenchmarkSample:
    sample_id: str
    benchmark: BenchmarkName
    question: str
    choices: dict[str, str] = field(default_factory=dict)
    gold: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedOutput:
    decision: str | None
    final_response: str
    confidence: str | None = None
    reason: str | None = None
    raw_text: str = ""


@dataclass(frozen=True)
class AgentOutput:
    agent: str
    prompt: str
    raw_text: str
    parsed: ParsedOutput


@dataclass(frozen=True)
class RunRecord:
    benchmark: str
    sample_id: str
    system: str
    aggregation: AggregationName
    agent_outputs: dict[str, AgentOutput]
    final_output: ParsedOutput
    gold: dict[str, Any]
    judge_output: dict[str, Any] | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

