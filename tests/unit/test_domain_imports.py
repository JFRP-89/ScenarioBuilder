import domain
import domain.cards
import domain.maps


def test_domain_packages_importable():
    assert domain is not None
    assert domain.cards is not None
    assert domain.maps is not None
