"""Strict versioned JSON records, verified by actual replay (SPEC RECORD)."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from .engine import validate_state
from .model import (
    Action,
    ActionKind,
    DrawSource,
    EndReason,
    GameState,
    MahjongError,
    Meld,
    MeldKind,
    PendingDiscard,
    PendingKong,
    Phase,
    PlayerState,
    SettlementConfig,
    SimulationResult,
    Tile,
    is_int,
)
from .simulation import replay
from .wall import Wall
from .scoring import settle_hand


def _encode_action(action: Action) -> dict[str, Any]:
    return {"kind": action.kind.value, "player": action.player, "tiles": list(action.tiles)}


def _encode_state(state: GameState) -> dict[str, Any]:
    value = {
        "wall": [tile.id for tile in state.wall.tiles],
        "players": [
            {
                "hand": [tile.id for tile in own.hand],
                "melds": [
                    {
                        "kind": meld.kind.value,
                        "tiles": [tile.id for tile in meld.tiles],
                        "source": meld.source,
                        "claimed_tile": meld.claimed_tile,
                    }
                    for meld in own.melds
                ],
                "flowers": [tile.id for tile in own.flowers],
            }
            for own in state.players
        ],
        "discards": [[tile.id for tile in river] for river in state.discards],
        "dealer": state.dealer,
        "turn": state.turn,
        "phase": state.phase.value,
        "pending": None if state.pending is None else {
            "player": state.pending.player,
            "tile": state.pending.tile.id,
        },
        "responses": [_encode_action(action) for action in state.responses],
        "last_drawn": state.last_drawn,
        "winner": state.winner,
        "win_source": state.win_source,
        "winning_tile": state.winning_tile,
        "end_reason": None if state.end_reason is None else state.end_reason.value,
    }

    # Keep the legacy snapshot shape unchanged when writing v1 records.
    if state.rules_version == 2:
        value.update({
            "rules_version": 2,
            "round_wind": state.round_wind,
            "draw_source": None if state.draw_source is None else state.draw_source.value,
            "pending_kong": None if state.pending_kong is None else {
                "player": state.pending_kong.player,
                "tile": state.pending_kong.tile.id,
                "meld_index": state.pending_kong.meld_index,
            },
            "robbed_tile": None if state.robbed_tile is None else state.robbed_tile.id,
            "last_discard_last": state.last_discard_last,
        })

    return value


def _check_result(result: SimulationResult) -> None:
    if not isinstance(result, SimulationResult):
        raise MahjongError("INVALID_RECORD", "Expected SimulationResult")

    validate_state(result.initial_state)
    validate_state(result.final_state)
    if not isinstance(result.settlement_config, SettlementConfig):
        raise MahjongError("INVALID_RECORD", "Expected SettlementConfig")
    result.settlement_config.__post_init__()
    if result.initial_state.rules_version == 1 and result.settlement_config != SettlementConfig():
        raise MahjongError("INVALID_RECORD", "v1 cannot contain settlement settings")

    # A stored final snapshot must match the actual sequence of transitions.
    if replay(result.initial_state, result.actions) != result.final_state:
        raise MahjongError("INVALID_RECORD", "Recorded final state differs from replay")


def record_to_json(result: SimulationResult) -> str:
    """Serialize a verified result, including recomputed v2 settlement data."""
    try:
        _check_result(result)

        value = {
            "version": result.initial_state.rules_version,
            "initial_state": _encode_state(result.initial_state),
            "actions": [_encode_action(action) for action in result.actions],
            "final_state": _encode_state(result.final_state),
        }
        if result.initial_state.rules_version == 2:
            value["settlement_config"] = asdict(result.settlement_config)
            value["settlement"] = _settlement_data(result)

        return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    except MahjongError as exc:
        raise MahjongError("INVALID_RECORD", str(exc)) from exc


def _keys(value: Any, expected: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(expected.split()):
        raise MahjongError("INVALID_RECORD", "JSON object has missing or extra fields")
    return value


def _array(value: Any) -> list[Any]:
    if type(value) is not list:
        raise MahjongError("INVALID_RECORD", "Expected JSON array")
    return value


def _decode_action(value: Any) -> Action:
    value = _keys(value, "kind player tiles")
    # apply_action or state validation checks integer ranges and action shape.
    return Action(
        ActionKind(value["kind"]),
        value["player"],
        tuple(_array(value["tiles"])),
    )


def _decode_meld(value: Any) -> Meld:
    value = _keys(value, "kind tiles source claimed_tile")
    return Meld(
        MeldKind(value["kind"]),
        tuple(Tile(i) for i in _array(value["tiles"])),
        value["source"],
        value["claimed_tile"],
    )


def _decode_player(value: Any) -> PlayerState:
    value = _keys(value, "hand melds flowers")
    return PlayerState(
        tuple(Tile(i) for i in _array(value["hand"])),
        tuple(_decode_meld(meld) for meld in _array(value["melds"])),
        tuple(Tile(i) for i in _array(value["flowers"])),
    )


def _decode_state(value: Any, version: int) -> GameState:
    fields = (
        "wall players discards dealer turn phase pending responses "
        "last_drawn winner win_source winning_tile end_reason"
    )
    if version == 2:
        fields += " rules_version round_wind draw_source pending_kong robbed_tile last_discard_last"
    value = _keys(value, fields)

    # Decode v2 context only when the record explicitly supplies it.
    extra = {"rules_version": version}
    if version == 2:
        if not is_int(value["rules_version"]) or value["rules_version"] != 2:
            raise MahjongError("INVALID_RECORD", "State rules version differs from record")
        kong = value["pending_kong"]
        if kong is not None:
            kong = _keys(kong, "player tile meld_index")
            kong = PendingKong(kong["player"], Tile(kong["tile"]), kong["meld_index"])
        extra.update({
            "round_wind": value["round_wind"],
            "draw_source": None if value["draw_source"] is None else DrawSource(value["draw_source"]),
            "pending_kong": kong,
            "robbed_tile": None if value["robbed_tile"] is None else Tile(value["robbed_tile"]),
            "last_discard_last": value["last_discard_last"],
        })

    pending = value["pending"]
    if pending is not None:
        pending = _keys(pending, "player tile")
        pending = PendingDiscard(pending["player"], Tile(pending["tile"]))

    return GameState(
        wall=Wall(tuple(Tile(i) for i in _array(value["wall"]))),
        players=tuple(_decode_player(own) for own in _array(value["players"])),
        discards=tuple(
            tuple(Tile(i) for i in _array(river))
            for river in _array(value["discards"])
        ),
        dealer=value["dealer"],
        turn=value["turn"],
        phase=Phase(value["phase"]),
        pending=pending,
        responses=tuple(_decode_action(action) for action in _array(value["responses"])),
        last_drawn=value["last_drawn"],
        winner=value["winner"],
        win_source=value["win_source"],
        winning_tile=value["winning_tile"],
        end_reason=None if value["end_reason"] is None else EndReason(value["end_reason"]),
        **extra,
    )


def _settlement_data(result: SimulationResult) -> Any:
    if result.final_state.phase is not Phase.ENDED:
        return None
    return asdict(settle_hand(result.final_state, result.settlement_config))


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise MahjongError("INVALID_RECORD", "Duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise MahjongError("INVALID_RECORD", f"Non-finite JSON number: {value}")


def record_from_json(text: str) -> SimulationResult:
    """Load strict JSON, replay the actions, and verify the recorded settlement."""
    if not isinstance(text, str):
        raise MahjongError("INVALID_RECORD", "Expected JSON text")

    try:
        value = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        if (
            type(value) is not dict
            or not is_int(value.get("version"))
            or value["version"] not in (1, 2)
        ):
            raise MahjongError("INVALID_RECORD", "Unsupported record version")

        version = value["version"]
        fields = "version initial_state actions final_state"
        config = SettlementConfig()
        if version == 2:
            fields += " settlement_config settlement"
        value = _keys(value, fields)

        if version == 2:
            settings = _keys(value["settlement_config"], "base tai_value")
            config = SettlementConfig(settings["base"], settings["tai_value"])

        result = SimulationResult(
            _decode_state(value["initial_state"], version),
            _decode_state(value["final_state"], version),
            tuple(_decode_action(action) for action in _array(value["actions"])),
            config,
        )
        _check_result(result)

        # Compare serialized values so altered number types are rejected as well.
        if version == 2:
            expected = json.dumps(_settlement_data(result), sort_keys=True, separators=(",", ":"))
            recorded = json.dumps(value["settlement"], sort_keys=True, separators=(",", ":"))
            if expected != recorded:
                raise MahjongError("INVALID_RECORD", "Settlement differs from recomputed result")

        return result
    except (ValueError, TypeError, RecursionError) as exc:
        raise MahjongError("INVALID_RECORD", str(exc)) from exc
