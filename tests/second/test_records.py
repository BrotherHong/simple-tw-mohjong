"""Strict v1/v2 JSON shapes, replay consistency and computed settlement."""

import json
from dataclasses import replace
from random import Random

import pytest

from tw_mahjong.engine import create_game
from tw_mahjong.model import MahjongError, SettlementConfig, SimulationResult
from tw_mahjong.records import record_from_json, record_to_json


@pytest.mark.parametrize("version", [1,2])
def test_complete_record_round_trip_is_deterministic(completed_results, version):
    result = completed_results[version]
    text = record_to_json(result)
    assert not text.endswith("\n")
    assert text == json.dumps(json.loads(text),ensure_ascii=False,sort_keys=True,indent=2)
    restored = record_from_json(text)
    assert restored == result
    assert record_to_json(restored) == text
    assert record_from_json(json.dumps(json.loads(text),sort_keys=False)) == result


@pytest.mark.parametrize("version", [1,2])
def test_empty_prefix_exact_versioned_fields(version):
    state = create_game(rng=Random(3),rules_version=version)
    result = SimulationResult(state,state,())
    value = json.loads(record_to_json(result))
    expected = {"version","initial_state","actions","final_state"}
    if version == 2:
        expected |= {"settlement_config","settlement"}
        assert value["settlement"] is None
        assert value["settlement_config"] == {"base":100,"tai_value":20}
    assert set(value) == expected
    assert ("rules_version" in value["initial_state"]) == (version == 2)
    assert value["initial_state"]["phase"] == "DISCARD"
    assert all(type(i) is int for i in value["initial_state"]["wall"])
    assert record_from_json(json.dumps(value)) == result


def test_custom_settlement_settings_and_finished_score_round_trip(winning_state):
    result = SimulationResult(winning_state,winning_state,(),SettlementConfig(0,7))
    text = record_to_json(result)
    value = json.loads(text)
    assert value["settlement_config"] == {"base":0,"tai_value":7}
    assert len(value["settlement"]["payments"]) == 3
    assert sum(value["settlement"]["deltas"]) == 0
    assert record_from_json(text) == result


@pytest.mark.parametrize("text", [None, b"{}", 1, "", "null", "[]", "{}", "{", '{"version":3}',
                                   '{"version":true}', '{"version":2.0}',
                                   '{"version":2,"version":2}', '{"x":NaN}', '{"x":Infinity}'])
def test_malformed_records_have_stable_error(text):
    with pytest.raises(MahjongError) as error:
        record_from_json(text)
    assert error.value.code == "INVALID_RECORD"


@pytest.mark.parametrize("path,value", [
    (("extra",), 0), (("version",), True), (("version",), 1),
    (("initial_state","dealer"), True), (("initial_state","turn"), 0.0),
    (("initial_state","wall",0), 143.0),
    (("initial_state","players",0,"hand",0), True),
    (("initial_state","players",0,"extra"), None),
    (("initial_state","phase"), "discard"),
    (("final_state","rules_version"), 1),
    (("settlement_config","base"), True),
    (("settlement_config","tai_value"), 0),
    (("actions",), {}), (("settlement",), {}),
])
def test_structural_and_type_tampering_rejected(prefix_result, path, value):
    data = json.loads(record_to_json(prefix_result))
    node = data
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    with pytest.raises(MahjongError) as error:
        record_from_json(json.dumps(data))
    assert error.value.code == "INVALID_RECORD"


@pytest.mark.parametrize("field", ["version","actions","settlement","initial_state"])
def test_missing_root_field_rejected(prefix_result, field):
    data = json.loads(record_to_json(prefix_result))
    del data[field]
    with pytest.raises(MahjongError) as error:
        record_from_json(json.dumps(data))
    assert error.value.code == "INVALID_RECORD"


def test_final_state_must_match_actions_even_if_both_states_valid(prefix_result):
    bad = replace(prefix_result,final_state=prefix_result.initial_state)
    with pytest.raises(MahjongError) as error:
        record_to_json(bad)
    assert error.value.code == "INVALID_RECORD"
    data = json.loads(record_to_json(prefix_result))
    data["final_state"] = data["initial_state"]
    with pytest.raises(MahjongError) as error:
        record_from_json(json.dumps(data))
    assert error.value.code == "INVALID_RECORD"


@pytest.mark.parametrize("path,value", [
    (("score","tai"), 999), (("score","tai"), True),
    (("score","tai"), 0.0), (("payments",0,"amount"), 999),
    (("deltas",0), True), (("extra",), None),
])
def test_finished_settlement_is_recomputed_and_type_checked(winning_state, path, value):
    data = json.loads(record_to_json(SimulationResult(winning_state,winning_state,())))
    node = data["settlement"]
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    with pytest.raises(MahjongError) as error:
        record_from_json(json.dumps(data))
    assert error.value.code == "INVALID_RECORD"


def test_duplicate_nested_json_keys_rejected(prefix_result):
    text = record_to_json(prefix_result).replace('"base": 100', '"base": 100, "base": 100',1)
    with pytest.raises(MahjongError) as error:
        record_from_json(text)
    assert error.value.code == "INVALID_RECORD"


@pytest.mark.parametrize("value", [None, (), {}, "record"])
def test_writer_requires_simulation_result(value):
    with pytest.raises(MahjongError) as error:
        record_to_json(value)
    assert error.value.code == "INVALID_RECORD"


def test_v1_refuses_extra_settlement_configuration(completed_results):
    with pytest.raises(MahjongError) as error:
        record_to_json(replace(completed_results[1],settlement_config=SettlementConfig(0,1)))
    assert error.value.code == "INVALID_RECORD"
