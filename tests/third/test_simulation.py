"""Deterministic simulations, policy failures and incremental raw replay."""

from random import Random

import pytest

from tw_mahjong.engine import apply_action, create_game, legal_actions, validate_state
from tw_mahjong.model import Action, ActionKind as A, MahjongError, Phase, SettlementConfig
from tw_mahjong.simulation import SimplePolicy, iter_replay, replay, simulate


@pytest.mark.parametrize("version,seed", [(1, 17), (2, 17), (2, 42)])
def test_seeded_simulation_is_reproducible_and_replayable(version, seed, capsys):
    def run():
        state = create_game(rng=Random(seed), rules_version=version, dealer=2)
        result = simulate(state, tuple(SimplePolicy(Random(seed * 4 + p + 1)) for p in range(4)))
        return result
    result = run()
    assert result == run()
    assert result.final_state.phase is Phase.ENDED
    assert result.actions
    assert replay(result.initial_state, result.actions) == result.final_state
    state = result.initial_state
    for action in result.actions:
        assert action in legal_actions(state, action.player)
        state = apply_action(state, action).state
        assert validate_state(state) is None
    assert capsys.readouterr().out == ""


def test_simulate_calls_lowest_eligible_player_and_preserves_config(initial):
    seen = []
    def policy(state, player):
        eligible = [p for p in range(4) if legal_actions(state, p)]
        assert player == eligible[0]
        seen.append(player)
        options = legal_actions(state, player)
        # Avoid claims; this deterministic path must eventually exhaust the wall.
        return next((a for a in options if a.kind is A.PASS), options[0])
    config = SettlementConfig(0, 7)
    result = simulate(initial, (policy,) * 4, settlement_config=config)
    assert len(seen) == len(result.actions)
    assert result.settlement_config == config
    assert result.initial_state == initial


def test_ended_simulation_never_calls_policies(won):
    def fail(*args):
        pytest.fail("ended simulations must not request an action")
    result = simulate(won, (fail,) * 4)
    assert result.initial_state == result.final_state == won
    assert result.actions == ()


@pytest.mark.parametrize("policies", [None, (), (None,) * 4, (lambda s, p: None,) * 3, [lambda s, p: None] * 4])
def test_policy_container_validation(initial, policies):
    with pytest.raises(MahjongError) as exc:
        simulate(initial, policies)
    assert exc.value.code == "INVALID_POLICY"


@pytest.mark.parametrize("choice", [None, 1, Action(A.PASS, 0), Action(A.DISCARD, 1, (1,)), Action(A.DISCARD, 0, (True,))])
def test_invalid_policy_return_is_normalized(initial, choice):
    with pytest.raises(MahjongError) as exc:
        simulate(initial, (lambda s, p: choice,) * 4)
    assert exc.value.code == "INVALID_POLICY"


@pytest.mark.parametrize("error", [RuntimeError("policy failed"), MahjongError("CUSTOM", "policy failed")])
def test_user_policy_exceptions_propagate_unchanged(initial, error):
    def fail(state, player):
        raise error
    with pytest.raises(type(error)) as exc:
        simulate(initial, (fail,) * 4)
    assert exc.value is error


def test_simulation_rejects_bad_settlement_settings(initial):
    policies = tuple(SimplePolicy(Random(p)) for p in range(4))
    with pytest.raises(MahjongError) as exc:
        simulate(initial, policies, settlement_config=None)
    assert exc.value.code == "INVALID_SETTLEMENT"
    legacy = create_game(rng=Random(0), rules_version=1)
    with pytest.raises(MahjongError) as exc:
        simulate(legacy, policies, settlement_config=SettlementConfig(0, 1))
    assert exc.value.code == "INVALID_SETTLEMENT"


def test_iter_replay_has_initial_and_one_frame_per_raw_action(prefix):
    frames = tuple(iter_replay(prefix.initial_state, prefix.actions))
    assert tuple(f.index for f in frames) == tuple(range(len(prefix.actions) + 1))
    assert frames[0].state == prefix.initial_state
    assert frames[0].action is None and frames[0].events == ()
    for previous, frame, action in zip(frames, frames[1:], prefix.actions):
        expected = apply_action(previous.state, action)
        assert frame.action == action
        assert frame.state == expected.state and frame.events == expected.events
    assert frames[-1].state == prefix.final_state
    assert replay(prefix.initial_state, ()) == prefix.initial_state


def test_iter_replay_raises_only_when_reaching_bad_step(initial):
    action = Action(A.DISCARD, 0, (0,))
    stream = iter_replay(initial, (action, action))
    assert next(stream).index == 0
    assert next(stream).index == 1
    with pytest.raises(MahjongError) as exc:
        next(stream)
    assert exc.value.code == "INVALID_ACTION"
    assert initial.discards[0] == ()


@pytest.mark.parametrize("actions", [[], None, iter(())])
def test_replay_requires_tuple(initial, actions):
    with pytest.raises(MahjongError) as exc:
        replay(initial, actions)
    assert exc.value.code == "INVALID_ACTION"


@pytest.mark.parametrize("rng", [None, 1, "seed", object()])
def test_simple_policy_requires_random(rng):
    with pytest.raises(MahjongError) as exc:
        SimplePolicy(rng)
    assert exc.value.code == "INVALID_POLICY"


def test_simple_policy_selects_hu_without_consuming_random(make_state, winning_tiles):
    rng = Random(17)
    before = rng.getstate()
    state = make_state(hands={0: winning_tiles})
    assert SimplePolicy(rng)(state, 0) == Action(A.HU, 0)
    assert rng.getstate() == before


def test_simple_policy_random_discard_uses_one_choice(initial):
    rng, control = Random(61), Random(61)
    choices = tuple(a for a in legal_actions(initial, 0) if a.kind is A.DISCARD)
    assert SimplePolicy(rng)(initial, 0) == control.choice(choices)
    assert rng.getstate() == control.getstate()


def test_simple_policy_rejects_ineligible_player(initial):
    with pytest.raises(MahjongError) as exc:
        SimplePolicy(Random(0))(initial, 1)
    assert exc.value.code == "INVALID_POLICY"
