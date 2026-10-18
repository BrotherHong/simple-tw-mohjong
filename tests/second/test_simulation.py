"""Policy validation, natural termination and lazy deterministic replay."""

from random import Random

import pytest

from tw_mahjong.engine import apply_action, create_game, legal_actions, validate_state
from tw_mahjong.model import Action, ActionKind, MahjongError, Phase, SettlementConfig
from tw_mahjong.simulation import SimplePolicy, iter_replay, replay, simulate


@pytest.mark.parametrize("version", [1,2])
def test_seeded_simulation_terminates_and_every_action_replays(completed_results, version, capsys):
    result = completed_results[version]
    assert result.final_state.phase is Phase.ENDED
    assert result.actions and isinstance(result.actions,tuple)
    assert replay(result.initial_state,result.actions) == result.final_state
    validate_state(result.final_state)
    assert capsys.readouterr().out == ""


def test_same_injected_seeds_give_same_simulation(completed_results):
    initial = create_game(rng=Random(17),rules_version=2)
    result = simulate(initial,tuple(SimplePolicy(Random(80+p)) for p in range(4)))
    assert result == completed_results[2]


def test_ended_input_does_not_call_policies(exhausted_state):
    def forbidden(*args):
        pytest.fail("An ended game must not consult a policy")
    result = simulate(exhausted_state,(forbidden,)*4,settlement_config=SettlementConfig(0,1))
    assert result.initial_state is exhausted_state and result.final_state is exhausted_state
    assert result.actions == () and result.settlement_config == SettlementConfig(0,1)


@pytest.mark.parametrize("policies", [None, [], (), (lambda s,p:None,)*3,
                                      (lambda s,p:None,)*5, (None,)*4])
def test_policy_container_must_be_four_callables(initial_state, policies):
    with pytest.raises(MahjongError) as error:
        simulate(initial_state,policies)
    assert error.value.code == "INVALID_POLICY"


@pytest.mark.parametrize("chosen", [None, "PASS", Action(ActionKind.PASS,0),
                                   Action(ActionKind.DRAW,1), Action(ActionKind.DISCARD,0,(143,))])
def test_illegal_policy_outputs_are_wrapped(initial_state, chosen):
    with pytest.raises(MahjongError) as error:
        simulate(initial_state,(lambda s,p:chosen,)*4)
    assert error.value.code == "INVALID_POLICY"
    assert isinstance(error.value.__cause__,MahjongError)


def test_policy_exceptions_propagate_unchanged(initial_state):
    failure = RuntimeError("caller policy failure")
    def broken(state,player):
        raise failure
    with pytest.raises(RuntimeError) as error:
        simulate(initial_state,(broken,)*4)
    assert error.value is failure


def test_custom_policy_mahjong_error_is_not_wrapped(initial_state):
    failure = MahjongError("CUSTOM_POLICY_ERROR","caller failure")
    def broken(state,player):
        raise failure
    with pytest.raises(MahjongError) as error:
        simulate(initial_state,(broken,)*4)
    assert error.value is failure


def test_responders_are_consulted_in_seat_order(initial_state):
    visited = []
    class StopAfterResponses(Exception):
        pass
    def policy(state, player):
        visited.append((state.phase,player))
        if state.phase is Phase.DISCARD:
            return next(a for a in legal_actions(state,player) if a.kind is ActionKind.DISCARD)
        if state.phase is Phase.RESPONSE:
            return Action(ActionKind.PASS,player)
        raise StopAfterResponses
    with pytest.raises(StopAfterResponses):
        simulate(initial_state,(policy,)*4)
    assert visited[:4] == [(Phase.DISCARD,0),(Phase.RESPONSE,1),(Phase.RESPONSE,2),(Phase.RESPONSE,3)]
    assert visited[4] == (Phase.DRAW,1)


def test_iter_replay_exact_frames_and_events(prefix_result):
    result = prefix_result
    frames = tuple(iter_replay(result.initial_state,result.actions))
    assert [f.index for f in frames] == list(range(len(result.actions)+1))
    assert frames[0].state is result.initial_state
    assert frames[0].action is None and frames[0].events == ()
    for before,after,action in zip(frames,frames[1:],result.actions):
        expected = apply_action(before.state,action)
        assert after.action == action
        assert (after.state,after.events) == (expected.state,expected.events)
    assert frames[-1].state == result.final_state


def test_empty_and_prefix_replay_need_not_end(initial_state, prefix_result):
    assert replay(initial_state,()) is initial_state
    assert replay(prefix_result.initial_state,prefix_result.actions) == prefix_result.final_state
    assert prefix_result.final_state.phase is not Phase.ENDED


def test_illegal_later_action_raises_only_when_reached(initial_state):
    discard = next(a for a in legal_actions(initial_state,0) if a.kind is ActionKind.DISCARD)
    iterator = iter_replay(initial_state,(discard,Action(ActionKind.DRAW,0)))
    assert next(iterator).index == 0
    assert next(iterator).action == discard
    with pytest.raises(MahjongError) as error:
        next(iterator)
    assert error.value.code == "INVALID_ACTION"


@pytest.mark.parametrize("actions", [[], [None], None, ""])
def test_replay_requires_tuple(initial_state, actions):
    with pytest.raises(MahjongError) as error:
        replay(initial_state,actions)
    assert error.value.code == "INVALID_ACTION"


@pytest.mark.parametrize("rng", [None, 17, object()])
def test_simple_policy_requires_random_instance(rng):
    with pytest.raises(MahjongError) as error:
        SimplePolicy(rng)
    assert error.value.code == "INVALID_POLICY"


def test_simple_policy_chooses_once_from_all_legal_discards(initial_state):
    class ChoiceSpy(Random):
        def __init__(self):
            super().__init__(0)
            self.choices = []
        def choice(self, seq):
            self.choices.append(tuple(seq))
            return seq[-1]
    rng = ChoiceSpy()
    discards = tuple(a for a in legal_actions(initial_state,0) if a.kind is ActionKind.DISCARD)
    assert SimplePolicy(rng)(initial_state,0) == discards[-1]
    assert rng.choices == [discards]


@pytest.mark.parametrize("config", [None, {}, 0])
def test_simulate_rejects_invalid_settlement_config(initial_state, config):
    with pytest.raises(MahjongError) as error:
        simulate(initial_state,(SimplePolicy(Random(0)),)*4,settlement_config=config)
    assert error.value.code == "INVALID_SETTLEMENT"


def test_legacy_simulation_rejects_nondefault_settlement_config():
    state = create_game(rng=Random(0),rules_version=1)
    with pytest.raises(MahjongError) as error:
        simulate(state,(SimplePolicy(Random(0)),)*4,settlement_config=SettlementConfig(0,1))
    assert error.value.code == "INVALID_SETTLEMENT"
