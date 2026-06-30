from __future__ import annotations

from collections import Counter
from itertools import combinations

from persona_mas.schemas import ParsedOutput


def majority_vote(outputs: list[ParsedOutput]) -> ParsedOutput:
    decisions = [output.decision for output in outputs if output.decision]
    if not decisions:
        return ParsedOutput(decision=None, final_response="")
    counts = Counter(decisions)
    top_count = max(counts.values())
    winners = [decision for decision, count in counts.items() if count == top_count]
    if len(winners) != 1:
        return ParsedOutput(decision=None, final_response="TIE")
    decision = winners[0]
    return ParsedOutput(decision=decision, final_response=decision)


def pairwise_disagreement_rate(outputs: list[ParsedOutput]) -> float:
    pairs = list(combinations(outputs, 2))
    if not pairs:
        return 0.0
    disagreements = sum(1 for left, right in pairs if left.decision != right.decision)
    return disagreements / len(pairs)


def oracle_correct(outputs: list[ParsedOutput], correct_decision: str) -> bool:
    return any(output.decision == correct_decision for output in outputs)


def all_decisions(outputs: list[ParsedOutput]) -> list[str | None]:
    return [output.decision for output in outputs]
