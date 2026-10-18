"""Pure initialization, legal actions, validation and transitions (SPEC STATE/TURN)."""

from __future__ import annotations

from dataclasses import replace
from itertools import combinations, product
from random import Random
from typing import Optional

from .hand import analyze_hand
from .model import (
    Action,
    ActionKind,
    DrawSource,
    EndReason,
    Event,
    EventKind,
    GameState,
    MahjongError,
    Meld,
    MeldKind,
    PendingDiscard,
    PendingKong,
    Phase,
    PlayerState,
    Tile,
    Transition,
    check_player,
    full_deck,
    is_int,
    is_sequence,
)
from .wall import Wall

_PRIORITY = {
    ActionKind.HU: 0,
    ActionKind.KONG_EXPOSED: 1,
    ActionKind.PENG: 1,
    ActionKind.CHI: 2,
    ActionKind.KONG_CONCEALED: 3,
    ActionKind.KONG_ADDED: 4,
    ActionKind.DRAW: 5,
    ActionKind.DISCARD: 6,
    ActionKind.PASS: 7,
}


def _action_key(action: Action) -> tuple[int, str, tuple[int, ...]]:
    return _PRIORITY[action.kind], action.kind.value, action.tiles


def _check_action(action: object) -> None:
    if not isinstance(action, Action) or not isinstance(action.kind, ActionKind):
        raise MahjongError("INVALID_ACTION", "Expected Action and ActionKind")
    if not is_int(action.player) or not 0 <= action.player < 4:
        raise MahjongError("INVALID_ACTION", "Invalid action player")
    if not isinstance(action.tiles, tuple) or not all(
        is_int(i) and 0 <= i < 144 for i in action.tiles
    ):
        raise MahjongError("INVALID_ACTION", "Action tiles must be physical tile ids")
    if action.tiles != tuple(sorted(set(action.tiles))):
        raise MahjongError("INVALID_ACTION", "Action tiles must be unique and sorted")

    size = {
        ActionKind.DISCARD: 1,
        ActionKind.CHI: 2,
        ActionKind.PENG: 2,
        ActionKind.KONG_EXPOSED: 3,
        ActionKind.KONG_CONCEALED: 4,
        ActionKind.KONG_ADDED: 1,
    }.get(action.kind, 0)
    if len(action.tiles) != size:
        raise MahjongError("INVALID_ACTION", "Wrong number of tiles for action")


def _response_options(state: GameState, player: int) -> tuple[Action, ...]:
    pending = state.pending_kong if state.phase is Phase.ROB_KONG else state.pending
    if pending is None or player == pending.player:
        return ()

    own = state.players[player]
    discarded = pending.tile
    actions = [Action(ActionKind.PASS, player)]
    if analyze_hand(own.hand + (discarded,), own.melds).winning:
        actions.append(Action(ActionKind.HU, player))
    if state.phase is Phase.ROB_KONG:
        return tuple(sorted(actions, key=_action_key))

    # Ordinary discards also allow matching melds and a next-player sequence.
    matching = [tile.id for tile in own.hand if tile.kind == discarded.kind]
    for pair in combinations(matching, 2):
        actions.append(Action(ActionKind.PENG, player, pair))
    if state.rules_version == 2 and len(matching) == 3:
        actions.append(Action(ActionKind.KONG_EXPOSED, player, tuple(matching)))

    if player == (pending.player + 1) % 4 and discarded.kind < 27:
        for start in range(discarded.kind - 2, discarded.kind + 1):
            group = (start, start + 1, start + 2)
            if not is_sequence(group) or discarded.kind not in group:
                continue
            others = tuple(kind for kind in group if kind != discarded.kind)
            choices = tuple(
                tuple(t.id for t in own.hand if t.kind == kind)
                for kind in others
            )
            for pair in product(*choices):
                actions.append(Action(ActionKind.CHI, player, tuple(sorted(pair))))
    return tuple(sorted(actions, key=_action_key))


def _tile_tuple(value: object, *, flower: bool, sorted_ids: bool) -> tuple[Tile, ...]:
    if not isinstance(value, tuple) or not all(
        isinstance(t, Tile) and t.is_flower == flower for t in value
    ):
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
    if not is_int(state.rules_version) or state.rules_version not in (1, 2):
        raise MahjongError("INVALID_STATE", "Unsupported rules version")
    if (
        not is_int(state.round_wind)
        or not 27 <= state.round_wind <= 30
        or type(state.last_discard_last) is not bool
    ):
        raise MahjongError("INVALID_STATE", "Invalid round wind or last-discard flag")
    if state.rules_version == 1 and (
        state.round_wind != 27
        or state.draw_source is not None
        or state.pending_kong is not None
        or state.robbed_tile is not None
        or state.last_discard_last
        or state.phase is Phase.ROB_KONG
    ):
        raise MahjongError("INVALID_STATE", "v1 snapshot contains v2 features")

    state.wall.__post_init__()
    check_player(state.dealer)
    check_player(state.turn)
    if not isinstance(state.phase, Phase):
        raise MahjongError("INVALID_STATE", "Invalid phase")
    if not isinstance(state.players, tuple) or len(state.players) != 4:
        raise MahjongError("INVALID_STATE", "Expected four players")
    if not isinstance(state.discards, tuple) or len(state.discards) != 4:
        raise MahjongError("INVALID_STATE", "Expected four discard rivers")

    # Count every owning zone once; pending decisions only reference these tiles.
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
            if state.rules_version == 1 and meld.kind not in (MeldKind.CHI, MeldKind.PENG):
                raise MahjongError("INVALID_STATE", "v1 cannot contain kongs")
            if meld.source == player or (
                meld.kind is MeldKind.CHI and player != (meld.source + 1) % 4
            ):
                raise MahjongError("INVALID_STATE", "Meld source does not match owner")
            tiles.extend(meld.tiles)
        equivalents.append(len(own.hand) + 3 * len(own.melds))
        tiles.extend(_tile_tuple(state.discards[player], flower=False, sorted_ids=False))
    if state.robbed_tile is not None:
        if (
            not isinstance(state.robbed_tile, Tile)
            or state.robbed_tile.is_flower
            or state.end_reason is not EndReason.ROB_KONG
            or state.phase is not Phase.ENDED
        ):
            raise MahjongError("INVALID_STATE", "Robbed tile is only owned by a finished robbed kong")
        tiles.append(state.robbed_tile)
    if len(tiles) != 144 or {tile.id for tile in tiles} != set(range(144)):
        raise MahjongError("INVALID_STATE", "Physical tiles must be conserved exactly once")

    # Check transient draw and response metadata separately from tile ownership.
    if not isinstance(state.responses, tuple) or len(state.responses) > 2:
        raise MahjongError("INVALID_STATE", "Responses must be an unresolved tuple of at most two")
    if state.last_drawn is not None and (
        not is_int(state.last_drawn)
        or state.last_drawn not in tuple(t.id for t in state.players[state.turn].hand)
    ):
        raise MahjongError("INVALID_STATE", "Last drawn tile must be in current player's hand")
    if state.rules_version == 2:
        if (state.last_drawn is None) != (state.draw_source is None) or (
            state.draw_source is not None
            and not isinstance(state.draw_source, DrawSource)
        ):
            raise MahjongError("INVALID_STATE", "Draw source must accompany last_drawn")
    if (
        state.last_discard_last
        and state.phase is not Phase.RESPONSE
        and not (state.phase is Phase.ENDED and state.end_reason is EndReason.DISCARD_WIN)
    ):
        raise MahjongError("INVALID_STATE", "Last-discard context outside discard response")
    if state.last_discard_last and state.wall.tiles:
        raise MahjongError("INVALID_STATE", "Last discard requires an empty wall")

    if state.phase is not Phase.ENDED:
        if any(
            value is not None
            for value in (state.winner, state.win_source, state.winning_tile, state.end_reason)
        ):
            raise MahjongError("INVALID_STATE", "Unfinished game has an outcome")
        expected = tuple(
            17 if state.phase in (Phase.DISCARD, Phase.ROB_KONG) and p == state.turn else 16
            for p in range(4)
        )
        if tuple(equivalents) != expected:
            raise MahjongError("INVALID_STATE", "Hand counts do not match phase")

    # A pending claim remains unresolved until all three opponents respond.
    if state.phase in (Phase.RESPONSE, Phase.ROB_KONG):
        pending = state.pending if state.phase is Phase.RESPONSE else state.pending_kong
        pending_type = PendingDiscard if state.phase is Phase.RESPONSE else PendingKong
        if not isinstance(pending, pending_type) or pending.player != state.turn:
            raise MahjongError("INVALID_STATE", "Response phase requires current player's discard")
        check_player(pending.player)
        if not isinstance(pending.tile, Tile) or pending.tile.is_flower:
            raise MahjongError("INVALID_STATE", "Pending tile must be ordinary")
        if state.phase is Phase.RESPONSE and (
            not state.discards[pending.player]
            or state.discards[pending.player][-1] != pending.tile
        ):
            raise MahjongError("INVALID_STATE", "Pending tile must be last discard")
        if state.phase is Phase.RESPONSE and state.last_drawn is not None:
            raise MahjongError("INVALID_STATE", "Response phase has no last draw")

        responders = []
        for action in state.responses:
            _check_action(action)
            if action not in _response_options(state, action.player):
                raise MahjongError("INVALID_STATE", "Stored response is not legal")
            responders.append(action.player)
        if responders != sorted(set(responders)):
            raise MahjongError("INVALID_STATE", "Responses must be unique and sorted by player")
        if state.phase is Phase.ROB_KONG:
            own = state.players[state.turn]
            if (
                state.pending is not None
                or state.last_drawn is None
                or not is_int(pending.meld_index)
                or not 0 <= pending.meld_index < len(own.melds)
            ):
                raise MahjongError("INVALID_STATE", "Invalid pending kong")
            meld = own.melds[pending.meld_index]
            if (
                meld.kind is not MeldKind.PENG
                or pending.tile not in own.hand
                or meld.tiles[0].kind != pending.tile.kind
            ):
                raise MahjongError("INVALID_STATE", "Added tile does not match original peng")
    elif state.pending is not None or state.responses:
        raise MahjongError("INVALID_STATE", "Only response phase can store pending responses")
    if state.phase is not Phase.ROB_KONG and state.pending_kong is not None:
        raise MahjongError("INVALID_STATE", "Pending kong outside rob phase")
    if state.phase is Phase.DRAW and state.last_drawn is not None:
        raise MahjongError("INVALID_STATE", "Draw phase has no last draw")

    # Finished states must explain both the outcome and the winning tile location.
    if state.phase is Phase.ENDED:
        if state.end_reason is EndReason.WALL_EXHAUSTED:
            if state.wall.tiles or any(n > 16 for n in equivalents):
                raise MahjongError("INVALID_STATE", "Exhaustion requires empty wall and no extra tile")
            if any(
                value is not None
                for value in (state.winner, state.win_source, state.winning_tile, state.last_drawn)
            ):
                raise MahjongError("INVALID_STATE", "Exhaustion cannot have a winning tile")
        elif state.end_reason in (EndReason.SELF_DRAW, EndReason.DISCARD_WIN, EndReason.ROB_KONG):
            check_player(state.winner)
            check_player(state.win_source)
            if (
                state.turn != state.winner
                or not is_int(state.winning_tile)
                or not 0 <= state.winning_tile < 136
            ):
                raise MahjongError("INVALID_STATE", "Invalid winning metadata")
            own = state.players[state.winner]
            if state.end_reason is EndReason.SELF_DRAW:
                expected = tuple(17 if p == state.winner else 16 for p in range(4))
                if (
                    state.win_source != state.winner
                    or state.winning_tile != state.last_drawn
                    or tuple(equivalents) != expected
                ):
                    raise MahjongError("INVALID_STATE", "Invalid self draw")
                winning_hand = own.hand
            else:
                river = state.discards[state.win_source]
                claimed = (
                    state.robbed_tile
                    if state.end_reason is EndReason.ROB_KONG
                    else (river[-1] if river else None)
                )
                if (
                    state.win_source == state.winner
                    or claimed is None
                    or claimed.id != state.winning_tile
                ):
                    raise MahjongError("INVALID_STATE", "Invalid winning discard")
                if state.end_reason is EndReason.ROB_KONG and not any(
                    meld.kind is MeldKind.PENG and meld.tiles[0].kind == claimed.kind
                    for meld in state.players[state.win_source].melds
                ):
                    raise MahjongError("INVALID_STATE", "Robbed kong must preserve its original peng")
                if tuple(equivalents) != (16, 16, 16, 16) or state.last_drawn is not None:
                    raise MahjongError("INVALID_STATE", "Invalid discard win counts")
                winning_hand = own.hand + (claimed,)
            if not analyze_hand(winning_hand, own.melds).winning:
                raise MahjongError("INVALID_STATE", "Winner does not have a winning hand")
        else:
            raise MahjongError("INVALID_STATE", "Ended game requires a known end reason")


def legal_actions(state: GameState, player: int) -> tuple[Action, ...]:
    """List legal choices without changing the supplied snapshot."""
    validate_state(state)
    check_player(player)

    return _legal_actions(state, player)


def _legal_actions(state: GameState, player: int) -> tuple[Action, ...]:
    if state.phase is Phase.ENDED:
        return ()
    if state.phase in (Phase.RESPONSE, Phase.ROB_KONG):
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

    # Claiming a meld does not count as drawing, so it cannot unlock a kong.
    if state.rules_version == 2 and state.last_drawn is not None:
        for kind in sorted({tile.kind for tile in own.hand}):
            matching = tuple(tile.id for tile in own.hand if tile.kind == kind)
            if len(matching) == 4:
                actions.append(Action(ActionKind.KONG_CONCEALED, player, matching))
        for meld in own.melds:
            if meld.kind is MeldKind.PENG:
                for tile in own.hand:
                    if tile.kind == meld.tiles[0].kind:
                        actions.append(Action(ActionKind.KONG_ADDED, player, (tile.id,)))
    return tuple(sorted(actions, key=_action_key))


def _with_player(state: GameState, player: int, own: PlayerState) -> GameState:
    players = list(state.players)
    players[player] = own
    return replace(state, players=tuple(players))


def _draw_ordinary(
    state: GameState,
    player: int,
    action: Optional[Action] = None,
    *,
    source: DrawSource = DrawSource.NORMAL,
) -> tuple[GameState, Optional[Tile], tuple[Event, ...]]:
    """Draw through flowers while keeping the original kong context."""
    events = []
    from_back = source is DrawSource.KONG
    while state.wall.tiles:
        tile, wall = state.wall.draw_back() if from_back else state.wall.draw_front()
        state = replace(state, wall=wall)
        own = state.players[player]
        if tile.is_flower:
            own = replace(own, flowers=tuple(sorted(own.flowers + (tile,))))
            state = _with_player(state, player, own)
            events.append(Event(EventKind.FLOWER, player, tile.id, action))
            from_back = True
            if source is not DrawSource.KONG:
                source = DrawSource.FLOWER
        else:
            own = replace(own, hand=tuple(sorted(own.hand + (tile,))))
            state = _with_player(state, player, own)
            events.append(Event(EventKind.DRAWN, player, tile.id, action))
            state = replace(state, draw_source=source if state.rules_version == 2 else None)
            return state, tile, tuple(events)

    # A required replacement draw can also end the hand with an empty wall.
    state = replace(
        state,
        phase=Phase.ENDED,
        end_reason=EndReason.WALL_EXHAUSTED,
        last_drawn=None,
        draw_source=None,
        last_discard_last=False,
    )
    events.append(Event(EventKind.EXHAUSTED))
    return state, None, tuple(events)


def create_game(
    *,
    dealer: int = 0,
    tile_order: Optional[tuple[Tile, ...]] = None,
    rng: Optional[Random] = None,
    rules_version: int = 2,
    round_wind: int = 27,
) -> GameState:
    """Deal sixteen ordinary tiles each, then one extra tile to the dealer."""
    check_player(dealer)
    if (
        not is_int(rules_version)
        or rules_version not in (1, 2)
        or not is_int(round_wind)
        or not 27 <= round_wind <= 30
        or (rules_version == 1 and round_wind != 27)
    ):
        raise MahjongError("INVALID_STATE", "Invalid rule version or round wind")
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

    state = GameState(
        wall,
        tuple(PlayerState() for _ in range(4)),
        ((), (), (), ()),
        dealer,
        dealer,
        Phase.DRAW,
        rules_version=rules_version,
        round_wind=round_wind,
    )
    order = tuple((dealer + offset) % 4 for offset in range(4))
    for player in order * 16 + (dealer,):
        state, tile, _ = _draw_ordinary(state, player, source=DrawSource.INITIAL)
        if tile is None:
            validate_state(state)
            return state

    state = replace(state, phase=Phase.DISCARD, last_drawn=tile.id)
    validate_state(state)
    return state


def apply_action(state: GameState, action: Action) -> Transition:
    """Validate both sides of a transition; the original state stays unchanged."""
    validate_state(state)
    _check_action(action)
    if action not in _legal_actions(state, action.player):
        raise MahjongError("INVALID_ACTION", "Action is not legal in current state")

    result = _apply_action(state, action)
    validate_state(result.state)
    return result


def _apply_action(state: GameState, action: Action) -> Transition:
    player = action.player
    if state.phase in (Phase.RESPONSE, Phase.ROB_KONG):
        # Collect everyone first so call order cannot decide the winning claim.
        responses = tuple(sorted(state.responses + (action,), key=lambda response: response.player))
        state = replace(state, responses=responses)
        events = (Event(EventKind.RESPONSE, player, action=action),)
        if len(responses) < 3:
            return Transition(state, events)

        robbing = state.phase is Phase.ROB_KONG
        pending = state.pending_kong if robbing else state.pending
        candidates = tuple(response for response in responses if response.kind is not ActionKind.PASS)
        state = replace(state, responses=(), pending=None, pending_kong=None)
        if not candidates:
            if robbing:
                return _complete_kong(
                    state,
                    Action(ActionKind.KONG_ADDED, pending.player, (pending.tile.id,)),
                    events,
                )
            next_player = (pending.player + 1) % 4
            state = replace(state, phase=Phase.DRAW, turn=next_player, last_discard_last=False)
            return Transition(state, events + (Event(EventKind.TURN, next_player),))

        # Resolve by claim priority, then by distance from the source player.
        selected = min(
            candidates,
            key=lambda response: (
                _PRIORITY[response.kind],
                (response.player - pending.player) % 4,
            ),
        )
        player = selected.player
        if selected.kind is ActionKind.HU:
            if robbing:
                # The robbed tile gets its own zone; the original peng stays intact.
                own = state.players[pending.player]
                state = _with_player(
                    state,
                    pending.player,
                    replace(own, hand=tuple(tile for tile in own.hand if tile != pending.tile)),
                )
            state = replace(
                state,
                phase=Phase.ENDED,
                turn=player,
                winner=player,
                win_source=pending.player,
                winning_tile=pending.tile.id,
                end_reason=EndReason.ROB_KONG if robbing else EndReason.DISCARD_WIN,
                robbed_tile=pending.tile if robbing else None,
                last_drawn=None,
                draw_source=None,
            )
            return Transition(state, events + (Event(EventKind.WON, player, pending.tile.id, selected),))
        if selected.kind is ActionKind.KONG_EXPOSED:
            return _complete_kong(state, selected, events, pending)

        # Move a claimed discard from the river into the new meld exactly once.
        own = state.players[player]
        consumed = tuple(t for t in own.hand if t.id in selected.tiles)
        meld = Meld(
            MeldKind(selected.kind.value),
            tuple(sorted(consumed + (pending.tile,))),
            pending.player,
            pending.tile.id,
        )
        own = replace(
            own,
            hand=tuple(t for t in own.hand if t.id not in selected.tiles),
            melds=own.melds + (meld,),
        )
        state = _with_player(state, player, own)
        discards = list(state.discards)
        discards[pending.player] = discards[pending.player][:-1]
        state = replace(
            state,
            discards=tuple(discards),
            phase=Phase.DISCARD,
            turn=player,
            last_discard_last=False,
        )
        return Transition(
            state,
            events + (
                Event(EventKind.CLAIMED, player, pending.tile.id, selected),
                Event(EventKind.TURN, player),
            ),
        )

    # Concealed kongs complete immediately; added kongs first allow robbery.
    if action.kind is ActionKind.KONG_CONCEALED:
        return _complete_kong(state, action)
    if action.kind is ActionKind.KONG_ADDED:
        tile = next(tile for tile in state.players[player].hand if tile.id == action.tiles[0])
        index = next(
            index
            for index, meld in enumerate(state.players[player].melds)
            if meld.kind is MeldKind.PENG and meld.tiles[0].kind == tile.kind
        )
        state = replace(state, phase=Phase.ROB_KONG, pending_kong=PendingKong(player, tile, index))
        return Transition(state, (Event(EventKind.KONG_DECLARED, player, tile.id, action),))

    if action.kind is ActionKind.DRAW:
        state, tile, events = _draw_ordinary(state, player, action)
        if tile is not None:
            state = replace(state, phase=Phase.DISCARD, last_drawn=tile.id)
        return Transition(state, events)

    if action.kind is ActionKind.HU:
        state = replace(
            state,
            phase=Phase.ENDED,
            winner=player,
            win_source=player,
            winning_tile=state.last_drawn,
            end_reason=EndReason.SELF_DRAW,
        )
        return Transition(state, (Event(EventKind.WON, player, state.last_drawn, action),))

    # Discarding clears draw context and opens a new response window.
    tile = next(t for t in state.players[player].hand if t.id == action.tiles[0])
    own = replace(
        state.players[player],
        hand=tuple(t for t in state.players[player].hand if t != tile),
    )
    state = _with_player(state, player, own)
    discards = list(state.discards)
    discards[player] += (tile,)
    state = replace(
        state,
        discards=tuple(discards),
        phase=Phase.RESPONSE,
        pending=PendingDiscard(player, tile),
        last_discard_last=(
            state.rules_version == 2
            and state.last_drawn is not None
            and not state.wall.tiles
        ),
        last_drawn=None,
        draw_source=None,
    )
    return Transition(state, (Event(EventKind.DISCARDED, player, tile.id, action),))


def _complete_kong(
    state: GameState,
    action: Action,
    events: tuple[Event, ...] = (),
    pending: Optional[PendingDiscard] = None,
) -> Transition:
    """Transfer kong tiles, then draw a replacement from the back of the wall."""
    player = action.player
    own = state.players[player]
    taken = tuple(tile for tile in own.hand if tile.id in action.tiles)
    melds = list(own.melds)

    if action.kind is ActionKind.KONG_ADDED:
        index = next(
            i for i, meld in enumerate(melds)
            if meld.kind is MeldKind.PENG and meld.tiles[0].kind == taken[0].kind
        )
        melds[index] = replace(
            melds[index],
            kind=MeldKind.KONG_ADDED,
            tiles=tuple(sorted(melds[index].tiles + taken)),
        )
        tile_id = taken[0].id
    else:
        external = () if pending is None else (pending.tile,)
        melds.append(Meld(
            MeldKind(action.kind.value),
            tuple(sorted(taken + external)),
            None if pending is None else pending.player,
            None if pending is None else pending.tile.id,
        ))
        tile_id = taken[0].id if pending is None else pending.tile.id

    if pending is not None:
        rivers = list(state.discards)
        rivers[pending.player] = rivers[pending.player][:-1]
        state = replace(state, discards=tuple(rivers))
    own = replace(
        own,
        hand=tuple(tile for tile in own.hand if tile.id not in action.tiles),
        melds=tuple(melds),
    )
    state = _with_player(state, player, own)
    state = replace(
        state,
        turn=player,
        phase=Phase.DRAW,
        last_drawn=None,
        draw_source=None,
        last_discard_last=False,
    )
    events += (Event(EventKind.KONG_COMPLETED, player, tile_id, action),)

    state, tile, drawn = _draw_ordinary(state, player, action, source=DrawSource.KONG)
    if tile is not None:
        state = replace(state, phase=Phase.DISCARD, last_drawn=tile.id)
    return Transition(state, events + drawn)
