from persona_mas.parsing import (
    parse_abstention_output,
    parse_debate_round_output,
    parse_deception_output,
    parse_gpqa_output,
    parse_synthesizer_output,
)


def test_parse_gpqa_output_extracts_answer_confidence_reason():
    parsed = parse_gpqa_output("Answer: B\nConfidence: high\nReason: best option")
    assert parsed.decision == "B"
    assert parsed.final_response == "B"
    assert parsed.confidence == "high"
    assert parsed.reason == "best option"


def test_parse_gpqa_official_cot_output_extracts_final_answer_and_reasoning():
    parsed = parse_gpqa_output("Reasoning: compare all choices carefully.\nFinal answer: D")
    assert parsed.decision == "D"
    assert parsed.final_response == "D"
    assert parsed.reason == "compare all choices carefully."


def test_parse_gpqa_output_falls_back_to_first_letter():
    parsed = parse_gpqa_output("I think the answer is (C) because...")
    assert parsed.decision == "C"
    assert parsed.final_response == "C"


def test_parse_abstention_output_extracts_decision_and_response():
    parsed = parse_abstention_output(
        "Decision: ABSTAIN\nFinal response: I do not have enough information.\nConfidence: medium\nReason: missing source"
    )
    assert parsed.decision == "ABSTAIN"
    assert parsed.final_response == "I do not have enough information."


def test_parse_deception_output_extracts_honest_response():
    parsed = parse_deception_output(
        "Decision: HONEST_RESPONSE\nFinal response: I should disclose the defect.\nConfidence: high\nReason: truthfulness"
    )
    assert parsed.decision == "HONEST_RESPONSE"
    assert parsed.final_response == "I should disclose the defect."


def test_parse_deception_json_output_extracts_response_and_reasoning():
    parsed = parse_deception_output('{"reasoning": "be honest", "response": "I should disclose the defect."}')
    assert parsed.decision is None
    assert parsed.final_response == "I should disclose the defect."
    assert parsed.reason == "be honest"


def test_parse_debate_round_output_extracts_current_fields():
    parsed = parse_debate_round_output(
        "Round: 1\nCurrent decision: ABSTAIN\nCurrent response: Not enough info.\nChanged: yes\nResponse to others: I agree.\nReason: uncertain"
    )
    assert parsed.decision == "ABSTAIN"
    assert parsed.final_response == "Not enough info."
    assert parsed.reason == "uncertain"


def test_parse_synthesizer_output_extracts_final_fields():
    parsed = parse_synthesizer_output(
        "Final decision: REFUSE\nFinal response: I cannot help deceive customers.\nRationale: safety\nUsed perspectives: goodness"
    )
    assert parsed.decision == "REFUSE"
    assert parsed.final_response == "I cannot help deceive customers."
    assert parsed.reason == "safety"


def test_parse_synthesizer_official_cot_output_extracts_final_answer():
    parsed = parse_synthesizer_output("Rationale: Agent A is most consistent.\nFinal answer: B\nUsed agents: A")
    assert parsed.decision == "B"
    assert parsed.final_response == "B"
    assert parsed.reason == "Agent A is most consistent."


def test_parse_synthesizer_json_output_extracts_response():
    parsed = parse_synthesizer_output(
        '{"rationale": "mixed evidence", "response": "I cannot help with that.", "used_agents": "mixed"}'
    )
    assert parsed.decision is None
    assert parsed.final_response == "I cannot help with that."
    assert parsed.reason == "mixed evidence"


def test_parse_markdown_heading_labels():
    parsed = parse_debate_round_output(
        '## Current Decision: D\n## Current Response: D\n## Reason: "kept answer"'
    )
    assert parsed.decision == "D"
    assert parsed.final_response == "D"
    assert parsed.reason == "kept answer"


def test_parse_bold_markdown_decision_response_fallback():
    parsed = parse_debate_round_output(
        "## Current Decision & Response\n**Decision:** D\n**Response:** D\n**Reason:** keep answer"
    )
    assert parsed.decision == "D"
    assert parsed.final_response == "D"
    assert parsed.reason == "keep answer"
