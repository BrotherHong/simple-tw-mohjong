"""Tile identity, meld shape and immutable public value contracts."""

from collections import Counter
from dataclasses import FrozenInstanceError

import pytest

from tw_mahjong.model import MahjongError, Meld, MeldKind, SettlementConfig, Tile, full_deck, tile_kind


def test_full_deck_has_exact_physical_identities():
    deck = full_deck()
    assert isinstance(deck, tuple)
    assert tuple(t.id for t in deck) == tuple(range(144))
    assert Counter(t.kind for t in deck) == Counter({**dict.fromkeys(range(34), 4), **dict.fromkeys(range(34, 42), 1)})
    assert sum(t.is_flower for t in deck) == 8
    assert Tile(0) != Tile(1)
    assert Tile(0).kind == Tile(1).kind


@pytest.mark.parametrize("kind,code", list(enumerate(
    [f"{r}{s}" for s in "mps" for r in range(1, 10)]
    + list("ESWNRGB") + [f"F{i}" for i in range(1, 9)])))
def test_tile_code_and_kind_roundtrip(kind, code):
    tile = Tile(kind * 4 if kind < 34 else kind + 102)
    assert tile.kind == tile_kind(code) == kind
    assert tile.code == code
    assert tile.is_flower == (kind >= 34)


@pytest.mark.parametrize("value", [-1, 144, True, False, 1.0, "1", None])
def test_invalid_tile_id(value):
    with pytest.raises(MahjongError) as exc:
        Tile(value)
    assert exc.value.code == "INVALID_TILE"


@pytest.mark.parametrize("code", ["", "1M", "e", "F0", "F9", "10m", " 1m", "1m ", None, 1])
def test_tile_codes_require_exact_match(code):
    with pytest.raises(MahjongError) as exc:
        tile_kind(code)
    assert exc.value.code == "INVALID_TILE"


@pytest.mark.parametrize("kind,ids,source,claimed", [
    (MeldKind.CHI, (0, 4, 8), 3, 4),
    (MeldKind.PENG, (0, 1, 3), 1, 1),
    (MeldKind.KONG_EXPOSED, (0, 1, 2, 3), 2, 3),
    (MeldKind.KONG_ADDED, (0, 1, 2, 3), 2, 1),
    (MeldKind.KONG_CONCEALED, (0, 1, 2, 3), None, None),
])
def test_valid_melds(kind, ids, source, claimed):
    meld = Meld(kind, tuple(Tile(i) for i in ids), source, claimed)
    assert meld.claimed_tile == claimed
    assert tuple(t.id for t in meld.tiles) == ids


@pytest.mark.parametrize("kind,ids,source,claimed", [
    (MeldKind.CHI, (28, 32, 36), 0, 28),  # suit boundary
    (MeldKind.CHI, (108, 112, 116), 0, 108),  # honors
    (MeldKind.PENG, (0, 1, 4), 0, 0),
    (MeldKind.PENG, (0, 0, 1), 0, 0),
    (MeldKind.PENG, (2, 1, 0), 0, 0),
    (MeldKind.PENG, (0, 1, 2), True, 0),
    (MeldKind.PENG, (0, 1, 2), 4, 0),
    (MeldKind.PENG, (0, 1, 2), 0, True),
    (MeldKind.PENG, (0, 1, 2), 0, 3),
    (MeldKind.PENG, (136, 137, 138), 0, 136),
    (MeldKind.KONG_CONCEALED, (0, 1, 2, 3), 0, None),
    (MeldKind.KONG_CONCEALED, (0, 1, 2, 3), None, 0),
    (MeldKind.KONG_EXPOSED, (0, 1, 2), 0, 0),
])
def test_invalid_melds(kind, ids, source, claimed):
    with pytest.raises(MahjongError) as exc:
        Meld(kind, tuple(Tile(i) for i in ids), source, claimed)
    assert exc.value.code == "INVALID_MELD"


@pytest.mark.parametrize("base,tai", [(-1, 20), (0, 0), (100, -1), (True, 20), (0, True), (1.0, 20), (0, "20")])
def test_settlement_config_validates_integers(base, tai):
    with pytest.raises(MahjongError) as exc:
        SettlementConfig(base, tai)
    assert exc.value.code == "INVALID_SETTLEMENT"


def test_public_values_are_frozen():
    with pytest.raises(FrozenInstanceError):
        Tile(0).id = 1
    with pytest.raises(FrozenInstanceError):
        SettlementConfig().base = 1
    assert SettlementConfig(0, 1).base == 0
    assert issubclass(MahjongError, ValueError)
