from domain.cards.constraints import incompatible_pairs_ok


def test_incompatible_pairs():
    selected = ["a", "b"]
    pairs = [("a", "b")]
    assert incompatible_pairs_ok(selected, pairs) is False
