from collections import Counter
from dataclasses import FrozenInstanceError

import pytest

from tw_mahjong.model import (
    Action, ActionKind, MahjongError, Meld, MeldKind, SettlementConfig,
    Tile, check_player, full_deck, tile_kind,
)


def test_full_deck_identity_and_kind_counts():
    deck = full_deck()
    assert isinstance(deck, tuple)
    assert tuple(t.id for t in deck) == tuple(range(144))
    counts = Counter(t.kind for t in deck)
    assert counts == {**{k: 4 for k in range(34)}, **{k: 1 for k in range(34, 42)}}
    assert len(set(deck)) == 144
    assert Tile(0) != Tile(1)


@pytest.mark.parametrize("kind,code", list(enumerate(
    [f"{rank}{suit}" for suit in "mps" for rank in range(1, 10)]
    + list("ESWNRGB") + [f"F{i}" for i in range(1, 9)])))
def test_tile_codes_round_trip(kind, code):
    tile = Tile(kind * 4 if kind < 34 else kind + 102)
    assert tile.kind == tile_kind(code) == kind
    assert tile.code == code
    assert tile.is_flower is (kind >= 34)


@pytest.mark.parametrize("value", [-1, 144, True, False, 1.0, "1", None])
def test_invalid_tile_ids(value):
    with pytest.raises(MahjongError) as caught:
        Tile(value)
    assert caught.value.code == "INVALID_TILE"
    assert isinstance(caught.value, ValueError)


@pytest.mark.parametrize("code", ["", "1M", "e", "0m", "10m", " F1", "F9", 1, None])
def test_invalid_tile_codes(code):
    with pytest.raises(MahjongError) as caught:
        tile_kind(code)
    assert caught.value.code == "INVALID_TILE"


@pytest.mark.parametrize("player", [-1, 4, True, 1.0, "0", None])
def test_invalid_player(player):
    with pytest.raises(MahjongError) as caught:
        check_player(player)
    assert caught.value.code == "INVALID_PLAYER"


@pytest.mark.parametrize("kind,ids,source,claimed", [
    (MeldKind.CHI, (0, 4, 8), 3, 4),
    (MeldKind.PENG, (0, 1, 2), 1, 0),
    (MeldKind.KONG_EXPOSED, (0, 1, 2, 3), 2, 3),
    (MeldKind.KONG_ADDED, (0, 1, 2, 3), 2, 0),
    (MeldKind.KONG_CONCEALED, (0, 1, 2, 3), None, None),
])
def test_valid_melds(kind, ids, source, claimed):
    meld = Meld(kind, tuple(map(Tile, ids)), source, claimed)
    assert tuple(t.id for t in meld.tiles) == ids


@pytest.mark.parametrize("kind,ids,source,claimed", [
    (MeldKind.CHI, (28, 32, 36), 0, 28),  # cannot cross suits
    (MeldKind.CHI, (108, 112, 116), 0, 108),
    (MeldKind.PENG, (0, 1, 4), 0, 0),
    (MeldKind.PENG, (0, 0, 1), 0, 0),
    (MeldKind.PENG, (2, 1, 0), 0, 0),
    (MeldKind.PENG, (0, 1, 2), True, 0),
    (MeldKind.PENG, (0, 1, 2), 0, 3),
    (MeldKind.PENG, (136, 137, 138), 0, 136),
    (MeldKind.KONG_CONCEALED, (0, 1, 2, 3), 0, 0),
])
def test_invalid_melds(kind, ids, source, claimed):
    with pytest.raises(MahjongError) as caught:
        Meld(kind, tuple(map(Tile, ids)), source, claimed)
    assert caught.value.code == "INVALID_MELD"


@pytest.mark.parametrize("base,tai", [(-1, 20), (0, 0), (1, -1), (True, 20), (100, False), (1.0, 20)])
def test_invalid_settlement_settings(base, tai):
    with pytest.raises(MahjongError) as caught:
        SettlementConfig(base, tai)
    assert caught.value.code == "INVALID_SETTLEMENT"


def test_public_values_are_frozen():
    for value, field, replacement in [(Tile(0), "id", 1),
                                      (Action(ActionKind.PASS, 0), "player", 1),
                                      (SettlementConfig(), "base", 0)]:
        with pytest.raises(FrozenInstanceError):
            setattr(value, field, replacement)
