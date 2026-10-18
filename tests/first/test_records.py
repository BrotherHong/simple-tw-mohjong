from dataclasses import replace
import json

import pytest

from tw_mahjong.engine import apply_action, create_game
from tw_mahjong.model import Action, ActionKind, MahjongError, SettlementConfig, SimulationResult, full_deck
from tw_mahjong.records import record_from_json, record_to_json


@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize("prefix", [False, True])
def test_record_round_trip_and_exact_version_fields(version, prefix):
    initial = create_game(tile_order=full_deck(), rules_version=version)
    action = Action(ActionKind.DISCARD, 0, (0,))
    final = apply_action(initial, action).state if prefix else initial
    config = SettlementConfig(0, 7) if version == 2 else SettlementConfig()
    result = SimulationResult(initial, final, (action,) if prefix else (), config)
    text = record_to_json(result)
    assert record_from_json(text) == result
    assert record_to_json(record_from_json(text)) == text
    assert not text.endswith("\n")
    data = json.loads(text)
    fields = {"version", "initial_state", "final_state", "actions"}
    if version == 2:
        fields |= {"settlement_config", "settlement"}
        assert data["settlement"] is None
        assert data["initial_state"]["rules_version"] == 2
    else:
        assert "rules_version" not in data["initial_state"]
        assert "draw_source" not in data["initial_state"]
    assert set(data) == fields
    # JSON whitespace and object-key order are not significant.
    reordered = {key: data[key] for key in reversed(list(data))}
    assert record_from_json(json.dumps(reordered, separators=(",", ":"))) == result


def test_finished_record_contains_recomputed_settlement(winning_state):
    result = SimulationResult(winning_state, winning_state, (), SettlementConfig(5, 3))
    text = record_to_json(result)
    data = json.loads(text)
    assert len(data["settlement"]["payments"]) == 3
    assert sum(data["settlement"]["deltas"]) == 0
    assert record_from_json(text) == result


@pytest.mark.parametrize("text", [None, 1, "", "{", "[]", "null", "NaN",
                                      '{"version":1,"version":2}', '{"version":true}',
                                      '{"version":3}', '{"version":2.0}'])
def test_malformed_records(text):
    with pytest.raises(MahjongError) as caught:
        record_from_json(text)
    assert caught.value.code == "INVALID_RECORD"


@pytest.mark.parametrize("mutation", ["extra", "missing", "tile_bool", "tile_float",
                                      "player_bool", "phase", "version", "actions",
                                      "final_state", "settlement"])
def test_record_tampering_is_rejected(initial, mutation):
    data = json.loads(record_to_json(SimulationResult(initial, initial, ())))
    if mutation == "extra":
        data["seed"] = 17
    elif mutation == "missing":
        del data["initial_state"]["pending"]
    elif mutation in ("tile_bool", "tile_float"):
        data["initial_state"]["players"][0]["hand"][0] = False if mutation == "tile_bool" else 0.0
    elif mutation == "player_bool":
        data["initial_state"]["dealer"] = False
    elif mutation == "phase":
        data["initial_state"]["phase"] = "discard"
    elif mutation == "version":
        data["final_state"]["rules_version"] = 1
    elif mutation == "actions":
        data["actions"] = [{"kind": "PASS", "player": 0, "tiles": []}]
    elif mutation == "final_state":
        data["final_state"]["round_wind"] = 28
    else:
        data["settlement"] = {}
    with pytest.raises(MahjongError) as caught:
        record_from_json(json.dumps(data))
    assert caught.value.code == "INVALID_RECORD"


@pytest.mark.parametrize("mutation", ["tai", "bool", "payment", "delta"])
def test_settlement_tampering_including_numeric_types(winning_state, mutation):
    data = json.loads(record_to_json(SimulationResult(winning_state, winning_state, ())))
    if mutation == "tai":
        data["settlement"]["score"]["tai"] += 1
    elif mutation == "bool":
        data["settlement"]["payments"][0]["payee"] = False
    elif mutation == "payment":
        data["settlement"]["payments"][0]["amount"] += 1
    else:
        data["settlement"]["deltas"][0] += 1
    with pytest.raises(MahjongError) as caught:
        record_from_json(json.dumps(data))
    assert caught.value.code == "INVALID_RECORD"


def test_writer_rejects_final_snapshot_not_explained_by_actions(initial):
    final = apply_action(initial, Action(ActionKind.DISCARD, 0, (0,))).state
    with pytest.raises(MahjongError) as caught:
        record_to_json(SimulationResult(initial, final, ()))
    assert caught.value.code == "INVALID_RECORD"


def test_writer_rejects_invalid_result_type():
    with pytest.raises(MahjongError) as caught:
        record_to_json(None)
    assert caught.value.code == "INVALID_RECORD"
