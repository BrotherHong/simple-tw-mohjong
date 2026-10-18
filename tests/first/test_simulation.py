from dataclasses import replace
from random import Random

import pytest

from tw_mahjong.engine import apply_action, create_game, legal_actions
from tw_mahjong.model import Action, ActionKind, MahjongError, Phase, SettlementConfig
from tw_mahjong.simulation import SimplePolicy, iter_replay, replay, simulate


@pytest.mark.parametrize("version,seed", [(1, 17), (2, 17), (2, 42)])
def test_simulation_terminates_is_reproducible_and_replays(version, seed, capsys):
    state = create_game(rng=Random(seed), rules_version=version)
    def run():
        return simulate(state, tuple(SimplePolicy(Random(seed * 4 + p + 1)) for p in range(4)))
    result = run()
    assert result == run()
    assert result.initial_state == state
    assert result.final_state.phase is Phase.ENDED
    assert replay(state, result.actions) == result.final_state
    assert capsys.readouterr().out == ""


def test_finished_simulation_never_calls_policies(exhausted):
    def forbidden(*args):
        pytest.fail("Finished games must not call policies")
    result = simulate(exhausted, (forbidden,) * 4)
    assert result.actions == ()
    assert result.final_state == exhausted


@pytest.mark.parametrize("policies", [[], (), (None,) * 4, (lambda s, p: None,) * 3])
def test_invalid_policy_collection(initial, policies):
    with pytest.raises(MahjongError) as caught:
        simulate(initial, policies)
    assert caught.value.code == "INVALID_POLICY"


@pytest.mark.parametrize("choice", [None, Action(ActionKind.PASS, 0), Action(ActionKind.DISCARD, 1, (0,))])
def test_invalid_policy_output(initial, choice):
    with pytest.raises(MahjongError) as caught:
        simulate(initial, (lambda s, p: choice,) * 4)
    assert caught.value.code == "INVALID_POLICY"


def test_policy_exception_propagates_same_object(initial):
    error = RuntimeError("policy failed")
    def broken(state, player):
        raise error
    with pytest.raises(RuntimeError) as caught:
        simulate(initial, (broken,) * 4)
    assert caught.value is error


def test_replay_prefix_and_events(initial):
    action = Action(ActionKind.DISCARD, 0, (0,))
    frames = tuple(iter_replay(initial, (action,)))
    assert frames[0].index == 0
    assert frames[0].state is initial
    assert frames[0].action is None
    assert frames[0].events == ()
    assert frames[1].index == 1
    assert frames[1].action == action
    assert frames[1].events == apply_action(initial, action).events
    assert replay(initial, (action,)) == frames[1].state
    assert replay(initial, ()) is initial


def test_replay_rejects_illegal_step_lazily(initial):
    action = Action(ActionKind.DISCARD, 0, (0,))
    frames = iter_replay(initial, (action, action))
    assert next(frames).index == 0
    assert next(frames).index == 1
    with pytest.raises(MahjongError) as caught:
        next(frames)
    assert caught.value.code == "INVALID_ACTION"


def test_replay_requires_tuple(initial):
    with pytest.raises(MahjongError) as caught:
        replay(initial, [])
    assert caught.value.code == "INVALID_ACTION"


@pytest.mark.parametrize("rng", [None, 0, object()])
def test_simple_policy_requires_rng(rng):
    with pytest.raises(MahjongError) as caught:
        SimplePolicy(rng)
    assert caught.value.code == "INVALID_POLICY"


def test_simple_policy_uses_exactly_one_choice_for_discard(initial):
    rng = Random(71)
    control = Random(71)
    options = tuple(a for a in legal_actions(initial, 0) if a.kind is ActionKind.DISCARD)
    assert SimplePolicy(rng)(initial, 0) == control.choice(options)
    assert rng.getstate() == control.getstate()


def test_simple_policy_prioritizes_win_without_randomness(winning_state):
    active = replace(winning_state, phase=Phase.DISCARD, winner=None, win_source=None,
                     winning_tile=None, end_reason=None)
    rng = Random(0)
    before = rng.getstate()
    assert SimplePolicy(rng)(active, 0) == Action(ActionKind.HU, 0)
    assert rng.getstate() == before


def test_policy_cannot_act_for_ineligible_player(initial):
    with pytest.raises(MahjongError) as caught:
        SimplePolicy(Random(0))(initial, 1)
    assert caught.value.code == "INVALID_POLICY"


def test_v1_disallows_custom_settlement(initial):
    legacy = replace(initial, rules_version=1, draw_source=None)
    with pytest.raises(MahjongError) as caught:
        simulate(legacy, (SimplePolicy(Random(0)),) * 4,
                 settlement_config=SettlementConfig(0, 1))
    assert caught.value.code == "INVALID_SETTLEMENT"
