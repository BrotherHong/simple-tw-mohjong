"""Physical tile identities, immutable values and meld/settlement contracts."""

from collections import Counter
from dataclasses import FrozenInstanceError

import pytest

from tw_mahjong.model import (
    Action, ActionKind, MahjongError, Meld, MeldKind, SettlementConfig,
    Tile, check_player, full_deck, tile_kind,
)


def test_full_deck_has_exact_multiplicities_and_codes():
    deck = full_deck()
    assert isinstance(deck, tuple)
    assert tuple(t.id for t in deck) == tuple(range(144))
    assert Counter(t.kind for t in deck) == Counter({**dict.fromkeys(range(34), 4),
                                                  **dict.fromkeys(range(34, 42), 1)})
    assert len(set(deck)) == 144
    for tile in deck:
        assert tile_kind(tile.code) == tile.kind
        assert tile.is_flower == (tile.id >= 136)


@pytest.mark.parametrize("tile_id,kind,code", [
    (0, 0, "1m"), (3, 0, "1m"), (35, 8, "9m"), (36, 9, "1p"),
    (71, 17, "9p"), (72, 18, "1s"), (107, 26, "9s"),
    (108, 27, "E"), (112, 28, "S"), (116, 29, "W"), (120, 30, "N"),
    (124, 31, "R"), (128, 32, "G"), (132, 33, "B"),
    (136, 34, "F1"), (143, 41, "F8"),
])
def test_tile_mapping_boundaries(tile_id, kind, code):
    tile = Tile(tile_id)
    assert (tile.kind, tile.code) == (kind, code)


@pytest.mark.parametrize("value", [-1, 144, True, False, 1.0, "0", None])
def test_tile_rejects_invalid_identity(value):
    with pytest.raises(MahjongError) as error:
        Tile(value)
    assert error.value.code == "INVALID_TILE"


@pytest.mark.parametrize("code", ["1M", "e", "f1", "0m", "10m", "F0", "F9", " 1m", "1m ", "", 1, None])
def test_tile_kind_requires_exact_code(code):
    with pytest.raises(MahjongError) as error:
        tile_kind(code)
    assert error.value.code == "INVALID_TILE"


@pytest.mark.parametrize("player", [-1, 4, True, 1.0, "0", None])
def test_player_validation_does_not_accept_boolean(player):
    with pytest.raises(MahjongError) as error:
        check_player(player)
    assert error.value.code == "INVALID_PLAYER"


@pytest.mark.parametrize("kind,ids,source,claimed", [
    (MeldKind.CHI, (0, 4, 8), 0, 4),
    (MeldKind.PENG, (0, 1, 3), 2, 1),
    (MeldKind.KONG_EXPOSED, (0, 1, 2, 3), 1, 0),
    (MeldKind.KONG_ADDED, (0, 1, 2, 3), 3, 2),
    (MeldKind.KONG_CONCEALED, (0, 1, 2, 3), None, None),
])
def test_valid_melds(kind, ids, source, claimed):
    meld = Meld(kind, tuple(Tile(i) for i in ids), source, claimed)
    assert meld.kind is kind and tuple(t.id for t in meld.tiles) == ids
    with pytest.raises(FrozenInstanceError):
        meld.source = 2


@pytest.mark.parametrize("kind,ids,source,claimed", [
    (MeldKind.CHI, (28, 32, 36), 0, 28),  # crosses suits
    (MeldKind.CHI, (108, 112, 116), 0, 108),  # honors cannot form a run
    (MeldKind.CHI, (0, 4, 12), 0, 0),
    (MeldKind.PENG, (0, 1, 4), 0, 0),
    (MeldKind.PENG, (0, 0, 1), 0, 0),
    (MeldKind.PENG, (2, 1, 0), 0, 0),
    (MeldKind.PENG, (0, 1, 2), True, 0),
    (MeldKind.PENG, (0, 1, 2), 4, 0),
    (MeldKind.PENG, (0, 1, 2), 0, 3),
    (MeldKind.PENG, (0, 1, 2), 0, False),
    (MeldKind.PENG, (136, 137, 138), 0, 136),
    (MeldKind.KONG_CONCEALED, (0, 1, 2, 3), 0, None),
    (MeldKind.KONG_CONCEALED, (0, 1, 2, 3), None, 0),
    (MeldKind.KONG_EXPOSED, (0, 1, 2), 0, 0),
    ("PENG", (0, 1, 2), 0, 0),
])
def test_invalid_melds_have_stable_error(kind, ids, source, claimed):
    with pytest.raises(MahjongError) as error:
        Meld(kind, tuple(Tile(i) for i in ids), source, claimed)
    assert error.value.code == "INVALID_MELD"


def test_values_are_frozen_and_physical_copies_distinct():
    assert Tile(0) != Tile(1)
    assert Tile(0).kind == Tile(1).kind
    for value, attribute, replacement in [
        (Tile(0), "id", 1),
        (Action(ActionKind.PASS, 0), "player", 1),
        (SettlementConfig(), "base", 0),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(value, attribute, replacement)
    assert issubclass(MahjongError, ValueError)


@pytest.mark.parametrize("base,tai_value", [(-1, 20), (True, 20), (0.0, 20), (0, 0), (0, -1), (0, True), (0, 1.0)])
def test_invalid_settlement_configuration(base, tai_value):
    with pytest.raises(MahjongError) as error:
        SettlementConfig(base, tai_value)
    assert error.value.code == "INVALID_SETTLEMENT"


def test_zero_base_and_positive_tai_value_are_allowed():
    assert SettlementConfig(0, 1).base == 0
