from src.domain.cards.scoring import matched_score


def test_matched_penalizes_risk_flags():
    assert matched_score(["visibility", "attrition"]) == 80
