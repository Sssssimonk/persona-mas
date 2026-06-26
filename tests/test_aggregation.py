from persona_mas.aggregation import majority_vote, oracle_correct, pairwise_disagreement_rate
from persona_mas.schemas import ParsedOutput


def out(decision: str) -> ParsedOutput:
    return ParsedOutput(decision=decision, final_response=decision)


def test_majority_vote_returns_two_of_three():
    result = majority_vote([out("A"), out("B"), out("A")])
    assert result.decision == "A"
    assert result.final_response == "A"


def test_majority_vote_abstention_uses_same_rule():
    result = majority_vote([out("ABSTAIN"), out("ANSWER"), out("ABSTAIN")])
    assert result.decision == "ABSTAIN"


def test_pairwise_disagreement_rate_counts_pairs():
    assert pairwise_disagreement_rate([out("A"), out("A"), out("B")]) == 2 / 3


def test_oracle_correct_true_when_any_agent_correct():
    assert oracle_correct([out("A"), out("C"), out("D")], "C") is True
    assert oracle_correct([out("A"), out("B"), out("D")], "C") is False

