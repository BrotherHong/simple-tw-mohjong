"""Policy-driven simulations and deterministic action replay (SPEC SIM/REPLAY)."""

from __future__ import annotations

from random import Random
from typing import Callable, Iterator

from .engine import apply_action, legal_actions, validate_state
from .model import (
    Action,
    ActionKind,
    GameState,
    MahjongError,
    Phase,
    ReplayFrame,
    SettlementConfig,
    SimulationResult,
)

Policy = Callable[[GameState, int], Action]


class SimplePolicy:
    """Take the first preferred action, using randomness only for discards."""

    def __init__(self, rng: Random) -> None:
        if not isinstance(rng, Random):
            raise MahjongError("INVALID_POLICY", "SimplePolicy requires random.Random")
        self.rng = rng

    def __call__(self, state: GameState, player: int) -> Action:
        options = legal_actions(state, player)
        if not options:
            raise MahjongError("INVALID_POLICY", "Player has no legal actions")

        priorities = (ActionKind.HU, ActionKind.PENG, ActionKind.CHI, ActionKind.DRAW)
        if state.rules_version == 2:
            priorities = (
                ActionKind.HU,
                ActionKind.KONG_EXPOSED,
                ActionKind.KONG_CONCEALED,
                ActionKind.KONG_ADDED,
                ActionKind.PENG,
                ActionKind.CHI,
                ActionKind.DRAW,
            )
        for kind in priorities:
            for action in options:
                if action.kind is kind:
                    return action

        discards = tuple(action for action in options if action.kind is ActionKind.DISCARD)
        if discards:
            return self.rng.choice(discards)
        return next(action for action in options if action.kind is ActionKind.PASS)


def simulate(
    initial_state: GameState,
    policies: tuple[Policy, ...],
    *,
    settlement_config: SettlementConfig = SettlementConfig(),
) -> SimulationResult:
    """Run four caller-supplied policies until the hand ends, without delays."""
    validate_state(initial_state)
    if not isinstance(settlement_config, SettlementConfig):
        raise MahjongError("INVALID_SETTLEMENT", "Expected SettlementConfig")
    settlement_config.__post_init__()
    if initial_state.rules_version == 1 and settlement_config != SettlementConfig():
        raise MahjongError("INVALID_SETTLEMENT", "Legacy games have no scoring configuration")
    if (
        not isinstance(policies, tuple)
        or len(policies) != 4
        or not all(callable(policy) for policy in policies)
    ):
        raise MahjongError("INVALID_POLICY", "Expected a tuple of four callable policies")

    state = initial_state
    actions = []

    # Visit eligible players in a stable order, including pending responders.
    while state.phase is not Phase.ENDED:
        for player in range(4):
            if legal_actions(state, player):
                # Exceptions from user policy code propagate unchanged.
                chosen = policies[player](state, player)
                try:
                    if not isinstance(chosen, Action) or chosen.player != player:
                        raise MahjongError("INVALID_ACTION", "Policy chose a different player")
                    transition = apply_action(state, chosen)
                except MahjongError as exc:
                    raise MahjongError("INVALID_POLICY", "Policy returned an illegal action") from exc

                state = transition.state
                actions.append(chosen)
                break
        else:
            raise MahjongError("INVALID_STATE", "Unfinished game has no legal actions")

    return SimulationResult(initial_state, state, tuple(actions), settlement_config)


def replay(initial_state: GameState, actions: tuple[Action, ...]) -> GameState:
    """Return the final snapshot after replaying every recorded action."""
    state = initial_state
    for frame in iter_replay(initial_state, actions):
        state = frame.state
    return state


def iter_replay(initial_state: GameState, actions: tuple[Action, ...]) -> Iterator[ReplayFrame]:
    """Yield the initial snapshot followed by one frame per accepted action."""
    validate_state(initial_state)
    if not isinstance(actions, tuple):
        raise MahjongError("INVALID_ACTION", "Replay requires a tuple of actions")

    state = initial_state
    yield ReplayFrame(0, state, None, ())

    # Keep raw response frames here; presentation may choose to hide them.
    for index, action in enumerate(actions, 1):
        transition = apply_action(state, action)
        state = transition.state
        yield ReplayFrame(index, state, action, transition.events)
