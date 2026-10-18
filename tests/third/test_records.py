"""Strict JSON v1/v2 schemas, replay integrity and settlement tampering."""

import json
from dataclasses import replace
from random import Random

import pytest

from tw_mahjong.engine import create_game
from tw_mahjong.model import MahjongError, SettlementConfig, SimulationResult
from tw_mahjong.records import record_from_json, record_to_json
from tw_mahjong.simulation import SimplePolicy, simulate


def reject(text):
    with pytest.raises(MahjongError) as exc:
        record_from_json(text)
    assert exc.value.code == "INVALID_RECORD"


@pytest.mark.parametrize("version", [1, 2])
def test_full_seeded_game_roundtrip(version):
    initial = create_game(rng=Random(17), rules_version=version)
    config = SettlementConfig() if version == 1 else SettlementConfig(0, 37)
    result = simulate(initial, tuple(SimplePolicy(Random(p)) for p in range(4)), settlement_config=config)
    encoded = record_to_json(result)
    assert record_from_json(encoded) == result
    assert record_to_json(record_from_json(encoded)) == encoded
    data = json.loads(encoded)
    assert data["version"] == version
    if version == 1:
        assert set(data) == {"version", "initial_state", "actions", "final_state"}
        assert "rules_version" not in data["initial_state"]
        assert "draw_source" not in data["final_state"]
    else:
        assert set(data) == {"version", "initial_state", "actions", "final_state", "settlement_config", "settlement"}
        assert data["settlement_config"] == {"base": 0, "tai_value": 37}
        assert data["settlement"] is not None


def test_unfinished_prefix_roundtrip_has_null_settlement(prefix):
    data = json.loads(record_to_json(prefix))
    assert data["settlement"] is None
    assert data["initial_state"]["wall"][0] == 65
    assert data["actions"][0] == {"kind": "DISCARD", "player": 0, "tiles": [0]}
    assert record_from_json(json.dumps(data, separators=(",", ":"))) == prefix


def test_empty_record_and_pending_response_roundtrip(initial, prefix):
    from tw_mahjong.simulation import replay
    for actions in ((), prefix.actions[:1], prefix.actions[:2]):
        result = SimulationResult(initial, replay(initial, actions), actions)
        assert record_from_json(record_to_json(result)) == result


@pytest.mark.parametrize("text", [None, b"{}", "", "{", "[]", "null", "true", "42",
    '{"version":true}', '{"version":2.0}', '{"version":3}',
    '{"version":1,"version":2}', '{"version":NaN}', '{"version":Infinity}'])
def test_invalid_json_and_versions(text):
    reject(text)


@pytest.mark.parametrize("path,value", [
    (("extra",), 0),
    (("version",), True),
    (("initial_state", "turn"), True),
    (("initial_state", "dealer"), 4),
    (("initial_state", "phase"), "discard"),
    (("initial_state", "rules_version"), 1),
    (("initial_state", "round_wind"), 30.0),
    (("initial_state", "draw_source"), "normal"),
    (("initial_state", "wall", 0), True),
    (("initial_state", "wall", 0), 144),
    (("initial_state", "players", 0, "hand", 0), 4),
    (("initial_state", "players", 0, "unknown"), []),
    (("initial_state", "players"), []),
    (("initial_state", "responses"), {}),
    (("actions",), {}),
    (("actions", 0, "kind"), "DISCARDED"),
    (("actions", 0, "player"), True),
    (("actions", 0, "tiles"), [False]),
    (("actions", 0, "tiles"), [0, 4]),
    (("actions", 0, "extra"), 1),
    (("final_state", "dealer"), 1),
    (("settlement_config", "base"), -1),
    (("settlement_config", "tai_value"), True),
    (("settlement_config", "extra"), 1),
    (("settlement",), {}),
])
def test_schema_and_replay_corruption_is_rejected(prefix, path, value):
    data = json.loads(record_to_json(prefix))
    node = data
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    reject(json.dumps(data))


@pytest.mark.parametrize("path", [(), ("initial_state",), ("initial_state", "players", 0), ("actions", 0), ("settlement_config",)])
def test_missing_fields_at_every_object_level(prefix, path):
    data = json.loads(record_to_json(prefix))
    node = data
    for key in path:
        node = node[key]
    del node[next(iter(node))]
    reject(json.dumps(data))


def test_duplicate_nested_key_is_rejected(prefix):
    text = record_to_json(prefix)
    assert '"dealer": 0' in text
    reject(text.replace('"dealer": 0', '"dealer": 0, "dealer": 0', 1))


@pytest.mark.parametrize("path,value", [
    (("score", "tai"), True),
    (("score", "tai"), 4.0),
    (("score", "items", 0, "tai"), 99),
    (("score", "items", 0, "code"), "SELF_DRAW"),
    (("score", "decomposition", "pair"), 28),
    (("score", "winning_group"), [0, 1, 2]),
    (("payments", 0, "amount"), 0),
    (("payments", 0, "payer"), True),
    (("deltas", 0), 0),
    (("extra",), 1),
])
def test_settlement_is_recomputed_and_compared_with_types(won, path, value):
    result = SimulationResult(won, won, ())
    data = json.loads(record_to_json(result))
    node = data["settlement"]
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    reject(json.dumps(data))


def test_writer_rejects_inconsistent_results(prefix):
    bad_results = (None, replace(prefix, final_state=prefix.initial_state),
                   replace(prefix, actions=[]), replace(prefix, settlement_config=None))
    for result in bad_results:
        with pytest.raises(MahjongError) as exc:
            record_to_json(result)
        assert exc.value.code == "INVALID_RECORD"


def test_legacy_record_rejects_v2_settings_and_midrecord_version_change(prefix):
    legacy = create_game(rng=Random(0), rules_version=1)
    with pytest.raises(MahjongError) as exc:
        record_to_json(SimulationResult(legacy, legacy, (), SettlementConfig(0, 1)))
    assert exc.value.code == "INVALID_RECORD"
    data = json.loads(record_to_json(prefix))
    data["final_state"]["rules_version"] = 1
    reject(json.dumps(data))


def test_decoder_does_not_call_policies(prefix, monkeypatch):
    text = record_to_json(prefix)
    def fail(*args, **kwargs):
        pytest.fail("record decoding must replay actions without policy decisions")
    monkeypatch.setattr(SimplePolicy, "__call__", fail)
    assert record_from_json(text) == prefix


def test_robbed_kong_record_preserves_owned_tile_and_original_peng(robbed_win):
    text = record_to_json(robbed_win)
    data = json.loads(text)
    assert data["final_state"]["robbed_tile"] == 3
    assert data["final_state"]["players"][0]["melds"][0]["kind"] == "PENG"
    assert record_from_json(text) == robbed_win


def test_pending_and_completed_added_kong_records_roundtrip(added_kong_ready):
    from tw_mahjong.engine import apply_action
    from tw_mahjong.model import Action, ActionKind
    actions = (Action(ActionKind.KONG_ADDED, 0, (3,)),) + tuple(Action(ActionKind.PASS, p) for p in (1, 2, 3))
    state = added_kong_ready
    for index, action in enumerate(actions, 1):
        state = apply_action(state, action).state
        result = SimulationResult(added_kong_ready, state, actions[:index])
        data = record_to_json(result)
        assert record_from_json(data) == result
        if index == 1:
            assert json.loads(data)["final_state"]["pending_kong"] == {"player": 0, "tile": 3, "meld_index": 0}


def test_concealed_kong_roundtrip_preserves_null_source(make_state):
    from tw_mahjong.engine import apply_action
    from tw_mahjong.model import Action, ActionKind, Tile
    initial = make_state(hands={0: tuple(Tile(i) for i in range(17))})
    action = Action(ActionKind.KONG_CONCEALED, 0, (0, 1, 2, 3))
    final = apply_action(initial, action).state
    result = SimulationResult(initial, final, (action,))
    data = json.loads(record_to_json(result))
    meld = data["final_state"]["players"][0]["melds"][0]
    assert meld["source"] is meld["claimed_tile"] is None
    assert record_from_json(json.dumps(data)) == result
