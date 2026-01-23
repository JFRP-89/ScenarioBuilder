import src.domain
import src.domain.cards
import src.domain.maps


def test_domain_packages_importable():
    assert src.domain is not None
    assert src.domain.cards is not None
    assert src.domain.maps is not None
