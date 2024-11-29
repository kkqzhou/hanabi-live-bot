from constants import COLOR_CLUE, RANK_CLUE
from card import Card
from conventions.reactor import ReactorGameState, get_reactive_playable_human_slot, get_reactive_trash_human_slot
from tes_helpers import create_game_states, give_clue, get_deck_from_tuples, get_game_state_from_replay
import datetime as dt


def test_basic_reactive_clue():
    card_tuples = [
        (4,5), (3,4), (2,5), (1,5), (0,5),
        (4,1), (3,5), (2,1), (1,1), (0,1),
        (0,4), (4,3), (3,1), (2,4), (2,1)
    ]
    GAME_STATES = create_game_states(3, "No Variant", ReactorGameState, deck=get_deck_from_tuples(card_tuples))
    alice: ReactorGameState = GAME_STATES[0]
    reactive_clues = alice.get_reactive_clues()
    assert (1,1,2) in reactive_clues and reactive_clues[(1,1,2)] == ["2P0D_PLAY", (1,1), (2,1)]
    assert (4,1,2) in reactive_clues and reactive_clues[(4,1,2)] == ["2P0D_PLAY", (0,1), (2,1)]
    assert (3,1,2) not in reactive_clues   # leads to two duped cards playing
    assert (2,0,2) in reactive_clues and reactive_clues[(2,0,2)] == ["1P1D_DISCARD", (0,1), (2,1)]
    assert (3,0,2) in reactive_clues and reactive_clues[(3,0,2)] == ["1P1D_DISCARD", (1,1), (2,1)]
    assert (4,0,2) in reactive_clues and reactive_clues[(4,0,2)] == ["1P1D_DISCARD", (2,1), (2,1)]
    assert (0,0,2) not in reactive_clues   # leads to crit b5 discarding


def test_reactive_finesse():
    card_tuples = [
        (4,5), (3,5), (2,5), (1,5), (0,5),
        (4,1), (3,1), (0,1), (1,1), (0,1),
        (4,2), (3,2), (2,3), (1,4), (0,2)
    ]
    GAME_STATES = create_game_states(3, "No Variant", ReactorGameState, deck=get_deck_from_tuples(card_tuples))
    alice: ReactorGameState = GAME_STATES[0]
    reactive_clues = alice.get_reactive_clues()
    assert (4,1,2) in reactive_clues and reactive_clues[(4,1,2)] == ["2P0D_FINESSE", (0,1), (0,2)]
    assert (3,1,2) in reactive_clues and reactive_clues[(3,1,2)] == ["2P0D_FINESSE", (3,1), (3,2)]
    assert (2,1,2) not in reactive_clues


def test_reactive_trash_1():
    card_tuples = [
        (4,5), (3,5), (2,5), (1,5), (0,5),
        (4,1), (3,1), (2,1), (1,1), (1,1),
        (4,2), (0,2), (1,4), (1,4), (0,2)
    ]
    GAME_STATES = create_game_states(3, "No Variant", ReactorGameState, deck=get_deck_from_tuples(card_tuples))
    alice: ReactorGameState = GAME_STATES[0]
    reactive_clues = alice.get_reactive_clues()
    assert (0,0,2) in reactive_clues and reactive_clues[(0,0,2)] == ["1P1D_PLAY", (2,1), (0,2)]
    assert (1,0,2) in reactive_clues and reactive_clues[(1,0,2)] == ["1P1D_PLAY", (1,1), (0,2)]
    assert (4,0,2) in reactive_clues and reactive_clues[(4,0,2)] == ["1P1D_PLAY", (3,1), (0,2)]


def test_reactive_trash_2():
    card_tuples = [
        (4,5), (3,5), (2,5), (1,5), (0,5),
        (4,1), (3,1), (2,1), (1,1), (1,1),
        (4,2), (1,2), (1,4), (1,4), (0,1)
    ]
    GAME_STATES = create_game_states(3, "No Variant", ReactorGameState, deck=get_deck_from_tuples(card_tuples), stacks=[1,0,0,0,0])
    alice: ReactorGameState = GAME_STATES[0]
    reactive_clues = alice.get_reactive_clues()
    assert (0,0,2) in reactive_clues and reactive_clues[(0,0,2)] == ["1P1D_PLAY", (4,1), (0,1)]
    assert (1,0,2) in reactive_clues and reactive_clues[(1,0,2)] == ["1P1D_PLAY", (1,1), (0,1)]
    assert (4,0,2) in reactive_clues and reactive_clues[(4,0,2)] == ["1P1D_PLAY", (3,1), (0,1)]


def test_reactive_trash_3():
    card_tuples = [
        (4,5), (3,5), (2,5), (1,5), (0,5),
        (4,1), (3,1), (2,1), (1,1), (1,1),
        (4,2), (3,3), (1,4), (1,4), (3,3)
    ]
    GAME_STATES = create_game_states(3, "No Variant", ReactorGameState, deck=get_deck_from_tuples(card_tuples))
    alice: ReactorGameState = GAME_STATES[0]
    alice.rank_clued_card_orders = {14}
    reactive_clues = alice.get_reactive_clues()
    assert (1,0,2) in reactive_clues and reactive_clues[(1,0,2)] == ["1P1D_PLAY", (4,1), (1,4)]
    assert (3,0,2) in reactive_clues and reactive_clues[(3,0,2)] == ["1P1D_PLAY", (1,1), (1,4)]
    assert (4,0,2) in reactive_clues and reactive_clues[(4,0,2)] == ["1P1D_PLAY", (2,1), (1,4)]


def test_reactive_trash_4():
    card_tuples = [
        (4,5), (3,5), (2,5), (1,5), (0,5),
        (4,1), (3,1), (2,1), (1,1), (1,1),
        (4,2), (3,3), (1,4), (1,4), (3,3)
    ]
    GAME_STATES = create_game_states(3, "No Variant", ReactorGameState, deck=get_deck_from_tuples(card_tuples))
    alice: ReactorGameState = GAME_STATES[0]
    alice.rank_clued_card_orders = {14}
    reactive_clues = alice.get_reactive_clues()
    assert (1,0,2) in reactive_clues and reactive_clues[(1,0,2)] == ["1P1D_PLAY", (4,1), (1,4)]
    assert (3,0,2) in reactive_clues and reactive_clues[(3,0,2)] == ["1P1D_PLAY", (1,1), (1,4)]
    assert (4,0,2) in reactive_clues and reactive_clues[(4,0,2)] == ["1P1D_PLAY", (2,1), (1,4)]


def test_rank_1_to_cathy_causing_bomb():
    # hanab.live/shared-replay/1328351
    card_tuples = [
        (4,3), (0,1), (1,1), (3,1), (2,4),
        (4,1), (0,2), (2,2), (3,1), (2,3),
        (4,3), (3,5), (1,2), (1,1), (1,3)
    ]
    GAME_STATES = create_game_states(3, "No Variant", ReactorGameState, deck=get_deck_from_tuples(card_tuples))
    bob: ReactorGameState = GAME_STATES[1]
    give_clue(GAME_STATES, 0, RANK_CLUE, 1, 2)
    # bob.print()
    ur = bob.unresolved_reactions[1]
    pslot = ur.get_reactive_playable_human_slot()
    assert pslot == 2


def test_bad_stable_1_clue():
    # hanab.live/shared-replay/1328406
    card_tuples = [
        (1,1), (4,1), (0,4), (0,3), (3,3),
        (2,3), (4,4), (0,2), (4,1), (2,1),
        (4,5), (2,5), (4,3), (0,5), (4,4)
    ]
    GAME_STATES = create_game_states(3, "No Variant", ReactorGameState, deck=get_deck_from_tuples(card_tuples), stacks=[0,2,1,3,1])
    alice: ReactorGameState = GAME_STATES[0]
    assert (1, 1, 1) not in alice.get_stable_clues()


def test_bad_rank_trash_push_clue():
    # hanab.live/shared-replay/1331975#23
    GAME_STATES = get_game_state_from_replay(1331975, 23, ReactorGameState)
    bob: ReactorGameState = GAME_STATES[1]
    stable_clues = bob.get_stable_clues()
    assert (1, 1, 2) not in stable_clues


def test_recognize_stable_rank_1_clue():
    # in reactor, 1 stable clue should be allowed to be given to yagami_white even though it bad touches
    GAME_STATES = get_game_state_from_replay(1332466, 4, ReactorGameState)
    alice: ReactorGameState = GAME_STATES[0]
    alice.print()
    stable_clues = alice.get_stable_clues(clue_types=[RANK_CLUE], clue_values=[1])
    assert(1, 1, 1) in stable_clues


def test_use_filtration_1():
    # purple 2 should not be marked as a pending play because its nonglobal. state:
    GAME_STATES = get_game_state_from_replay(1332466, 10, ReactorGameState)
    bob: ReactorGameState = GAME_STATES[1]
    assert 9 not in bob.all_play_orders


def test_all():
    t0 = dt.datetime.now()
    test_basic_reactive_clue()
    test_reactive_finesse()
    test_reactive_trash_1()
    test_reactive_trash_2()
    test_reactive_trash_3()
    test_reactive_trash_4()
    test_rank_1_to_cathy_causing_bomb()
    test_bad_stable_1_clue()
    test_bad_rank_trash_push_clue()
    test_recognize_stable_rank_1_clue()
    test_use_filtration_1()
    t1 = dt.datetime.now()
    print(f"All tests passed in {(t1 - t0).total_seconds():.2f}s!")

if __name__ == '__main__':
    test_all()