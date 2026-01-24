import src.application
from src.application.ports import (
    content_provider,
    current_user_provider,
    map_renderer,
    repositories,
)
from src.application.use_cases.generate_card import execute as generate
from src.application.use_cases.list_cards import execute as list_cards
from src.application.use_cases.save_card import execute as save_card
from src.application.use_cases.create_variant import execute as create_variant
from src.application.use_cases.manage_favorites import add_favorite, remove_favorite
from src.application.use_cases.manage_presets import list_presets
from src.application.use_cases.render_map_svg import execute as render_map
from src.infrastructure.content.file_content_provider import FileContentProvider
from src.infrastructure.maps.svg_renderer import SvgRenderer


class DummyRepo:
    def __init__(self) -> None:
        self.saved = []

    def save(self, card, owner_id: str) -> None:
        self.saved.append((card, owner_id))

    def list_for_owner(self, owner_id: str):
        return [c for c, o in self.saved if o == owner_id]


def test_generate_card_use_case():
    card = generate("casual", 7, FileContentProvider())
    assert card.seed == 7


def test_save_and_list_cards():
    repo = DummyRepo()
    card = generate("casual", 7, FileContentProvider())
    save_card(repo, card, "u1")
    assert len(list_cards(repo, "u1")) == 1


def test_create_variant_returns_card():
    card = generate("casual", 7, FileContentProvider())
    assert create_variant(card, 99) == card


def test_favorites_noop():
    assert add_favorite("c1", "u1") is None
    assert remove_favorite("c1", "u1") is None


def test_list_presets():
    presets = list_presets()
    assert any(p["id"] == "standard" for p in presets)


def test_render_map_svg():
    svg = render_map(SvgRenderer(), {"width": 10, "height": 10})
    assert svg.startswith("<svg")


def test_ports_importable():
    assert src.application is not None
    assert content_provider is not None
    assert current_user_provider is not None
    assert map_renderer is not None
    assert repositories is not None
