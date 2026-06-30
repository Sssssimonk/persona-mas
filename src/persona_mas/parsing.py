from __future__ import annotations

import json
import re
from collections.abc import Iterable

from persona_mas.schemas import ParsedOutput


def _line_value(text: str, labels: Iterable[str]) -> str | None:
    for label in labels:
        pattern = re.compile(
            rf"^\s*(?:#+\s*)?(?:\*\*)?{re.escape(label)}(?:\*\*)?\s*:\s*(?:\*\*)?\s*(.*?)\s*$",
            re.IGNORECASE | re.MULTILINE,
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip().strip('"')
    return None


def _normalized_choice(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"\b([ABCD])\b", value.upper())
    return match.group(1) if match else None


def _normalized_decision(value: str | None, allowed: set[str]) -> str | None:
    if not value:
        return None
    upper = value.strip().upper()
    for decision in allowed:
        if decision in upper:
            return decision
    return None


def _json_object(text: str) -> dict | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if match:
        cleaned = match.group(0)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def parse_gpqa_output(text: str) -> ParsedOutput:
    answer = _normalized_choice(_line_value(text, ["Answer", "Final answer"]))
    if answer is None:
        answer = _normalized_choice(text)
    return ParsedOutput(
        decision=answer,
        final_response=answer or text.strip(),
        confidence=_line_value(text, ["Confidence"]),
        reason=_line_value(text, ["Reasoning", "Reason", "Rationale"]),
        raw_text=text,
    )


def parse_abstention_output(text: str) -> ParsedOutput:
    decision = _normalized_decision(_line_value(text, ["Decision"]), {"ANSWER", "ABSTAIN"})
    return ParsedOutput(
        decision=decision,
        final_response=_line_value(text, ["Final response", "Response"]) or text.strip(),
        confidence=_line_value(text, ["Confidence"]),
        reason=_line_value(text, ["Reason", "Rationale"]),
        raw_text=text,
    )


def parse_deception_output(text: str) -> ParsedOutput:
    parsed_json = _json_object(text)
    if parsed_json:
        response = parsed_json.get("response") or parsed_json.get("final_response") or text.strip()
        return ParsedOutput(
            decision=_normalized_decision(str(parsed_json.get("decision", "")), {"HONEST_RESPONSE", "REFUSE"}),
            final_response=str(response).strip(),
            confidence=None,
            reason=str(parsed_json.get("reasoning") or parsed_json.get("reason") or "").strip() or None,
            raw_text=text,
        )
    decision = _normalized_decision(_line_value(text, ["Decision"]), {"HONEST_RESPONSE", "REFUSE"})
    return ParsedOutput(
        decision=decision,
        final_response=_line_value(text, ["Final response", "Response"]) or text.strip(),
        confidence=_line_value(text, ["Confidence"]),
        reason=_line_value(text, ["Reason", "Rationale"]),
        raw_text=text,
    )


def parse_debate_round_output(text: str) -> ParsedOutput:
    parsed_json = _json_object(text)
    if parsed_json:
        decision_value = parsed_json.get("final_answer") or parsed_json.get("decision") or parsed_json.get("current_decision")
        decision = _normalized_choice(str(decision_value)) if decision_value else None
        if decision is None and decision_value:
            decision = str(decision_value).strip().upper()
        response = parsed_json.get("response") or parsed_json.get("final_response") or parsed_json.get("current_response")
        return ParsedOutput(
            decision=decision,
            final_response=str(response).strip() if response else text.strip(),
            confidence=None,
            reason=str(parsed_json.get("reasoning") or parsed_json.get("reason") or parsed_json.get("rationale") or "").strip()
            or None,
            raw_text=text,
        )
    final_answer = _normalized_choice(_line_value(text, ["Final answer", "Final Answer"]))
    if final_answer is not None:
        return ParsedOutput(
            decision=final_answer,
            final_response=final_answer,
            confidence=None,
            reason=_line_value(text, ["Reasoning", "Reason", "Rationale"]),
            raw_text=text,
        )
    decision = _line_value(text, ["Current decision", "Current Decision", "Decision"])
    response = _line_value(text, ["Current response", "Current Response", "Response"])
    return ParsedOutput(
        decision=decision.strip().upper() if decision else None,
        final_response=response or text.strip(),
        confidence=None,
        reason=_line_value(text, ["Reason"]),
        raw_text=text,
    )


def parse_synthesizer_output(text: str) -> ParsedOutput:
    parsed_json = _json_object(text)
    if parsed_json:
        decision_value = parsed_json.get("final_answer") or parsed_json.get("final_decision") or parsed_json.get("decision")
        decision = _normalized_choice(str(decision_value)) if decision_value else None
        if decision is None and decision_value:
            decision = str(decision_value).strip().upper()
        response = parsed_json.get("response") or parsed_json.get("final_response")
        return ParsedOutput(
            decision=decision,
            final_response=str(response).strip() if response else text.strip(),
            confidence=None,
            reason=str(parsed_json.get("rationale") or parsed_json.get("reasoning") or parsed_json.get("reason") or "").strip()
            or None,
            raw_text=text,
        )
    final_answer = _normalized_choice(_line_value(text, ["Final answer", "Final Answer"]))
    if final_answer is not None:
        return ParsedOutput(
            decision=final_answer,
            final_response=final_answer,
            confidence=None,
            reason=_line_value(text, ["Rationale", "Reasoning", "Reason"]),
            raw_text=text,
        )
    decision = _line_value(text, ["Final decision", "Final Decision"])
    response = _line_value(text, ["Final response", "Final Response"])
    return ParsedOutput(
        decision=decision.strip().upper() if decision else None,
        final_response=response or text.strip(),
        confidence=None,
        reason=_line_value(text, ["Rationale", "Reason"]),
        raw_text=text,
    )


def parse_for_benchmark(benchmark: str, text: str) -> ParsedOutput:
    if benchmark == "gpqa":
        return parse_gpqa_output(text)
    if benchmark == "abstentionbench":
        return parse_abstention_output(text)
    if benchmark == "deceptionbench":
        return parse_deception_output(text)
    raise ValueError(f"Unsupported benchmark: {benchmark}")
