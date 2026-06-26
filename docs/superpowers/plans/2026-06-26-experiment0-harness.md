# Experiment 0 Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable MVP harness for Experiment 0 covering GPQA, AbstentionBench, DeceptionBench, persona outputs, voting, C0/C1 aggregation, and smoke-testable generation.

**Architecture:** Use a small Python package under `src/persona_mas`. Keep benchmark loading, parsing, aggregation, generation backends, and CLI orchestration separate so each part can be tested without loading models.

**Tech Stack:** Python 3.12-compatible stdlib, `datasets`, `pandas`, optional `transformers/peft/torch`, `pytest`.

---

## Task 1: Core Parsing and Aggregation

**Files:**
- Create: `src/persona_mas/schemas.py`
- Create: `src/persona_mas/parsing.py`
- Create: `src/persona_mas/aggregation.py`
- Test: `tests/test_parsing.py`
- Test: `tests/test_aggregation.py`

- [ ] Write tests for GPQA/abstention/deception/synthesizer parsers.
- [ ] Implement minimal parsers that extract structured fields from strict text output.
- [ ] Write tests for majority vote and C0/C1 trace objects.
- [ ] Implement aggregation helpers.

## Task 2: Benchmark Loaders

**Files:**
- Create: `src/persona_mas/benchmarks.py`
- Test: `tests/test_benchmarks.py`

- [ ] Write tests for loading small local fixture records into normalized `BenchmarkSample`.
- [ ] Implement GPQA CSV loader with deterministic option shuffle.
- [ ] Implement AbstentionBench HF loader with optional local JSONL fallback.
- [ ] Implement DeceptionBench HF loader with optional local JSONL fallback.

## Task 3: Prompt Builders and Generation Backends

**Files:**
- Create: `src/persona_mas/prompts.py`
- Create: `src/persona_mas/generation.py`
- Test: `tests/test_prompts.py`
- Test: `tests/test_generation.py`

- [ ] Write tests for benchmark-specific prompts.
- [ ] Implement strict prompt builders for independent, debate round, and synthesizer calls.
- [ ] Implement `MockBackend` for smoke tests.
- [ ] Implement lazy `HFBackend` skeleton for real model inference.

## Task 4: CLI Runner and Metrics

**Files:**
- Create: `src/persona_mas/runner.py`
- Create: `src/persona_mas/metrics.py`
- Create: `run_experiment0.py`
- Create: `configs/experiment0_smoke.json`
- Test: `tests/test_metrics.py`

- [ ] Write tests for accuracy, abstention metrics, and deception-rate metrics.
- [ ] Implement a runner that executes single, voting, C0, and C1 on a small sample.
- [ ] Save raw generations and summary metrics to `outputs/`.
- [ ] Add a smoke config using mock generation.

## Task 5: Remote Smoke Test

**Files:**
- Create: `scripts/remote_run_smoke.sh`

- [ ] Sync code to remote.
- [ ] Run local tests on remote base environment.
- [ ] Run `run_experiment0.py --config configs/experiment0_smoke.json`.

