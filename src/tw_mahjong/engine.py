"""Pure initialization, legal actions, validation and transitions (SPEC STATE/TURN)."""

from __future__ import annotations

from dataclasses import replace
from itertools import combinations, product
from random import Random
from typing import Optional

from .hand import analyze_hand
from .model import (
    Action, ActionKind, EndReason, Event, EventKind, GameState, MahjongError,
    Meld, MeldKind, PendingDiscard, Phase, PlayerState, Tile, Transition,
    check_player, full_deck, is_int, is_sequence,
)
from .wall import Wall

_PRIORITY = {kind: i for i, kind in enumerate((
    ActionKind.HU, ActionKind.PENG, ActionKind.CHI, ActionKind.DRAW,
    ActionKind.DISCARD, ActionKind.PASS,
))}


def _action_key(action: Action) -> tuple[int, tuple[int, ...]]:
    return _PRIORITY[action.kind], action.tiles


def _check_action(action: object) -> None:
    if not isinstance(action, Action) or not isinstance(action.kind, ActionKind):
        raise MahjongError("INVALID_ACTION", "Expected Action and ActionKind")
    if not is_int(action.player) or not 0 <= action.player < 4:
        raise MahjongError("INVALID_ACTION", "Invalid action player")
    if not isinstance(action.tiles, tuple) or not all(is_int(i) and 0 <= i < 144 for i in action.tiles):
        raise MahjongError("INVALID_ACTION", "Action tiles must be physical tile ids")
    if action.tiles != tuple(sorted(set(action.tiles))):
        raise MahjongError("INVALID_ACTION", "Action tiles must be unique and sorted")
    size = {ActionKind.DISCARD: 1, ActionKind.CHI: 2, ActionKind.PENG: 2}.get(action.kind, 0)
    if len(action.tiles) != size:
        raise MahjongError("INVALID_ACTION", "Wrong number of tiles for action")


def _response_options(state: GameState, player: int) -> tuple[Action, ...]:
    pending = state.pending
    if pending is None or player == pending.player:
        return ()
    own = state.players[player]
    discarded = pending.tile
    actions = [Action(ActionKind.PASS, player)]
    if analyze_hand(own.hand + (discarded,), own.melds).winning:
        actions.append(Action(ActionKind.HU, player))
    matching = [tile.id for tile in own.hand if tile.kind == discarded.kind]
    for pair in combinations(matching, 2):
        actions.append(Action(ActionKind.PENG, player, pair))
    if player == (pending.player + 1) % 4 and discarded.kind < 27:
        for start in range(discarded.kind - 2, discarded.kind + 1):
            group = (start, start + 1, start + 2)
            if not is_sequence(group) or discarded.kind not in group:
                continue
            others = tuple(kind for kind in group if kind != discarded.kind)
            choices = tuple(tuple(t.id for t in own.hand if t.kind == kind) for kind in others)
            for pair in product(*choices):
                actions.append(Action(ActionKind.CHI, player, tuple(sorted(pair))))
    return tuple(sorted(actions, key=_action_key))


def _tile_tuple(value: object, *, flower: bool, sorted_ids: bool) -> tuple[Tile, ...]:
    if not isinstance(value, tuple) or not all(isinstance(t, Tile) and t.is_flower == flower for t in value):
        raise MahjongError("INVALID_STATE", "Invalid tile zone")
    if sorted_ids and tuple(t.id for t in value) != tuple(sorted(t.id for t in value)):
        raise MahjongError("INVALID_STATE", "Hand and flowers must be sorted")
    return value


def validate_state(state: GameState) -> None:
    """Validate public snapshots without mutating them; errors use INVALID_STATE."""
    try:
        _validate_state(state)
    except MahjongError as exc:
        if exc.code == "INVALID_STATE":
            raise
        raise MahjongError("INVALID_STATE", str(exc)) from exc


def _validate_state(state: GameState) -> None:
    if not isinstance(state, GameState) or not isinstance(state.wall, Wall):
        raise MahjongError("INVALID_STATE", "Expected GameState with a Wall")
    state.wall.__post_init__()
    check_player(state.dealer)
    check_player(state.turn)
    if not isinstance(state.phase, Phase):
        raise MahjongError("INVALID_STATE", "Invalid phase")
    if not isinstance(state.players, tuple) or len(state.players) != 4:
        raise MahjongError("INVALID_STATE", "Expected four players")
    if not isinstance(state.discards, tuple) or len(state.discards) != 4:
        raise MahjongError("INVALID_STATE", "Expected four discard rivers")
    tiles = list(state.wall.tiles)
    equivalents = []
    for player, own in enumerate(state.players):
        if not isinstance(own, PlayerState):
            raise MahjongError("INVALID_STATE", "Invalid player snapshot")
        tiles.extend(_tile_tuple(own.hand, flower=False, sorted_ids=True))
        tiles.extend(_tile_tuple(own.flowers, flower=True, sorted_ids=True))
        if not isinstance(own.melds, tuple) or len(own.melds) > 5:
            raise MahjongError("INVALID_STATE", "Invalid meld collection")
        for meld in own.melds:
            if not isinstance(meld, Meld):
                raise MahjongError("INVALID_STATE", "Expected meld")
            meld.__post_init__()
            if meld.source == player or (meld.kind is MeldKind.CHI and player != (meld.source + 1) % 4):
                raise MahjongError("INVALID_STATE", "Meld source does not match owner")
            tiles.extend(meld.tiles)
        equivalents.append(len(own.hand) + 3 * len(own.melds))
        tiles.extend(_tile_tuple(state.discards[player], flower=False, sorted_ids=False))
    if len(tiles) != 144 or {tile.id for tile in tiles} != set(range(144)):
        raise MahjongError("INVALID_STATE", "Physical tiles must be conserved exactly once")
    if not isinstance(state.responses, tuple) or len(state.responses) > 2:
        raise MahjongError("INVALID_STATE", "Responses must be an unresolved tuple of at most two")
    if state.last_drawn is not None and (
        not is_int(state.last_drawn) or state.last_drawn not in tuple(t.id for t in state.players[state.turn].hand)
    ):
        raise MahjongError("INVALID_STATE", "Last drawn tile must be in current player's hand")
    if state.phase is not Phase.ENDED:
        if any(value is not None for value in (state.winner, state.win_source, state.winning_tile, state.end_reason)):
            raise MahjongError("INVALID_STATE", "Unfinished game has an outcome")
        expected = tuple(17 if state.phase is Phase.DISCARD and p == state.turn else 16 for p in range(4))
        if tuple(equivalents) != expected:
            raise MahjongError("INVALID_STATE", "Hand counts do not match phase")
    if state.phase is Phase.RESPONSE:
        pending = state.pending
        if not isinstance(pending, PendingDiscard) or pending.player != state.turn:
            raise MahjongError("INVALID_STATE", "Response phase requires current player's discard")
        check_player(pending.player)
        if not isinstance(pending.tile, Tile) or not state.discards[pending.player] or state.discards[pending.player][-1] != pending.tile:
            raise MahjongError("INVALID_STATE", "Pending tile must be last discard")
        if state.last_drawn is not None:
            raise MahjongError("INVALID_STATE", "Response phase has no last draw")
        responders = []
        for action in state.responses:
            _check_action(action)
            if action not in _response_options(state, action.player):
                raise MahjongError("INVALID_STATE", "Stored response is not legal")
            responders.append(action.player)
        if responders != sorted(set(responders)):
            raise MahjongError("INVALID_STATE", "Responses must be unique and sorted by player")
    elif state.pending is not None or state.responses:
        raise MahjongError("INVALID_STATE", "Only response phase can store pending responses")
    if state.phase is Phase.DRAW and state.last_drawn is not None:
        raise MahjongError("INVALID_STATE", "Draw phase has no last draw")
    if state.phase is Phase.ENDED:
        if state.end_reason is EndReason.WALL_EXHAUSTED:
            if state.wall.tiles or any(n > 16 for n in equivalents):
                raise MahjongError("INVALID_STATE", "Exhaustion requires empty wall and no extra tile")
            if any(value is not None for value in (state.winner, state.win_source, state.winning_tile, state.last_drawn)):
                raise MahjongError("INVALID_STATE", "Exhaustion cannot have a winning tile")
        elif state.end_reason in (EndReason.SELF_DRAW, EndReason.DISCARD_WIN):
            check_player(state.winner)
            check_player(state.win_source)
            if state.turn != state.winner or not is_int(state.winning_tile) or not 0 <= state.winning_tile < 136:
                raise MahjongError("INVALID_STATE", "Invalid winning metadata")
            own = state.players[state.winner]
            if state.end_reason is EndReason.SELF_DRAW:
                expected = tuple(17 if p == state.winner else 16 for p in range(4))
                if state.win_source != state.winner or state.winning_tile != state.last_drawn or tuple(equivalents) != expected:
                    raise MahjongError("INVALID_STATE", "Invalid self draw")
                winning_hand = own.hand
            else:
                river = state.discards[state.win_source]
                if state.win_source == state.winner or not river or river[-1].id != state.winning_tile:
                    raise MahjongError("INVALID_STATE", "Invalid winning discard")
                if tuple(equivalents) != (16, 16, 16, 16) or state.last_drawn is not None:
                    raise MahjongError("INVALID_STATE", "Invalid discard win counts")
                winning_hand = own.hand + (river[-1],)
            if not analyze_hand(winning_hand, own.melds).winning:
                raise MahjongError("INVALID_STATE", "Winner does not have a winning hand")
        else:
            raise MahjongError("INVALID_STATE", "Ended game requires a known end reason")


def legal_actions(state: GameState, player: int) -> tuple[Action, ...]:
    validate_state(state)
    check_player(player)
    return _legal_actions(state, player)


def _legal_actions(state: GameState, player: int) -> tuple[Action, ...]:
    if state.phase is Phase.ENDED:
        return ()
    if state.phase is Phase.RESPONSE:
        if any(response.player == player for response in state.responses):
            return ()
        return _response_options(state, player)
    if player != state.turn:
        return ()
    if state.phase is Phase.DRAW:
        return (Action(ActionKind.DRAW, player),)
    own = state.players[player]
    actions = [Action(ActionKind.DISCARD, player, (t.id,)) for t in own.hand]
    if state.last_drawn is not None and analyze_hand(own.hand, own.melds).winning:
        actions.append(Action(ActionKind.HU, player))
    return tuple(sorted(actions, key=_action_key))


def _with_player(state: GameState, player: int, own: PlayerState) -> GameState:
    players = list(state.players)
    players[player] = own
    return replace(state, players=tuple(players))


def _draw_ordinary(state: GameState, player: int, action: Optional[Action] = None) -> tuple[GameState, Optional[Tile], tuple[Event, ...]]:
    events = []
    from_back = False
    while state.wall.tiles:
        tile, wall = state.wall.draw_back() if from_back else state.wall.draw_front()
        state = replace(state, wall=wall)
        own = state.players[player]
        if tile.is_flower:
            own = replace(own, flowers=tuple(sorted(own.flowers + (tile,))))
            state = _with_player(state, player, own)
            events.append(Event(EventKind.FLOWER, player, tile.id, action))
            from_back = True
        else:
            own = replace(own, hand=tuple(sorted(own.hand + (tile,))))
            state = _with_player(state, player, own)
            events.append(Event(EventKind.DRAWN, player, tile.id, action))
            return state, tile, tuple(events)
    state = replace(state, phase=Phase.ENDED, end_reason=EndReason.WALL_EXHAUSTED, last_drawn=None)
    events.append(Event(EventKind.EXHAUSTED))
    return state, None, tuple(events)


def create_game(*, dealer: int = 0, tile_order: Optional[tuple[Tile, ...]] = None, rng: Optional[Random] = None) -> GameState:
    check_player(dealer)
    if (tile_order is None) == (rng is None):
        raise MahjongError("INVALID_WALL", "Provide exactly one of tile_order and rng")
    if tile_order is None:
        if not isinstance(rng, Random):
            raise MahjongError("INVALID_WALL", "Expected random.Random")
        shuffled = list(full_deck())
        rng.shuffle(shuffled)
        tile_order = tuple(shuffled)
    wall = Wall(tile_order)
    if len(wall.tiles) != 144:
        raise MahjongError("INVALID_WALL", "Initialization requires all 144 tiles")
    state = GameState(wall, tuple(PlayerState() for _ in range(4)), ((), (), (), ()), dealer, dealer, Phase.DRAW)
    order = tuple((dealer + offset) % 4 for offset in range(4))
    for player in order * 16 + (dealer,):
        state, tile, _ = _draw_ordinary(state, player)
        if tile is None:
            validate_state(state)
            return state
    state = replace(state, phase=Phase.DISCARD, last_drawn=tile.id)
    validate_state(state)
    return state


def apply_action(state: GameState, action: Action) -> Transition:
    validate_state(state)
    _check_action(action)
    if action not in _legal_actions(state, action.player):
        raise MahjongError("INVALID_ACTION", "Action is not legal in current state")
    result = _apply_action(state, action)
    validate_state(result.state)
    return result


def _apply_action(state: GameState, action: Action) -> Transition:
    player = action.player
    if state.phase is Phase.RESPONSE:
        responses = tuple(sorted(state.responses + (action,), key=lambda response: response.player))
        state = replace(state, responses=responses)
        events = (Event(EventKind.RESPONSE, player, action=action),)
        if len(responses) < 3:
            return Transition(state, events)
        pending = state.pending
        candidates = tuple(response for response in responses if response.kind is not ActionKind.PASS)
        state = replace(state, responses=(), pending=None)
        if not candidates:
            next_player = (pending.player + 1) % 4
            state = replace(state, phase=Phase.DRAW, turn=next_player)
            return Transition(state, events + (Event(EventKind.TURN, next_player),))
        selected = min(candidates, key=lambda response: (
            _PRIORITY[response.kind], (response.player - pending.player) % 4,
        ))
        player = selected.player
        if selected.kind is ActionKind.HU:
            state = replace(state, phase=Phase.ENDED, turn=player, winner=player,
                            win_source=pending.player, winning_tile=pending.tile.id, end_reason=EndReason.DISCARD_WIN)
            return Transition(state, events + (Event(EventKind.WON, player, pending.tile.id, selected),))
        own = state.players[player]
        consumed = tuple(t for t in own.hand if t.id in selected.tiles)
        meld = Meld(MeldKind(selected.kind.value), tuple(sorted(consumed + (pending.tile,))), pending.player, pending.tile.id)
        own = replace(own, hand=tuple(t for t in own.hand if t.id not in selected.tiles), melds=own.melds + (meld,))
        state = _with_player(state, player, own)
        discards = list(state.discards)
        discards[pending.player] = discards[pending.player][:-1]
        state = replace(state, discards=tuple(discards), phase=Phase.DISCARD, turn=player)
        return Transition(state, events + (
            Event(EventKind.CLAIMED, player, pending.tile.id, selected), Event(EventKind.TURN, player),
        ))
    if action.kind is ActionKind.DRAW:
        state, tile, events = _draw_ordinary(state, player, action)
        if tile is not None:
            state = replace(state, phase=Phase.DISCARD, last_drawn=tile.id)
        return Transition(state, events)
    if action.kind is ActionKind.HU:
        state = replace(state, phase=Phase.ENDED, winner=player, win_source=player,
                        winning_tile=state.last_drawn, end_reason=EndReason.SELF_DRAW)
        return Transition(state, (Event(EventKind.WON, player, state.last_drawn, action),))
    tile = next(t for t in state.players[player].hand if t.id == action.tiles[0])
    own = replace(state.players[player], hand=tuple(t for t in state.players[player].hand if t != tile))
    state = _with_player(state, player, own)
    discards = list(state.discards)
    discards[player] += (tile,)
    state = replace(state, discards=tuple(discards), phase=Phase.RESPONSE,
                    pending=PendingDiscard(player, tile), last_drawn=None)
    return Transition(state, (Event(EventKind.DISCARDED, player, tile.id, action),))
