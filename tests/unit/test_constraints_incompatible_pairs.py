from domain.cards.constraints import incompatible_pairs_ok


def test_incompatible_pairs():
    selected = ["a", "b"]
    pairs = [("a", "b")]
    assert incompatible_pairs_ok(selected, pairs) is False


def test_compatible_pairs():
    selected = ["a", "c"]
    pairs = [("a", "b")]
    assert incompatible_pairs_ok(selected, pairs) is True


def test_incompatible_pairs_ok_when_no_conflicts():
    selected = ["x", "y", "z"]
    pairs = [("a", "b"), ("c", "d")]
    assert incompatible_pairs_ok(selected, pairs) is True
