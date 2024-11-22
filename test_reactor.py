from conventions.reactor import ReactorGameState, get_reactive_playable_human_slot, get_reactive_trash_human_slot
from test_game_state import create_game_states, give_clue, get_deck_from_tuples, get_game_state_from_replay
from game_state import COLOR_CLUE, RANK_CLUE, Card
import datetime as dt
import requests

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

# TODO: implement endgame

def test_all():
    t0 = dt.datetime.now()
    test_rank_1_to_cathy_causing_bomb()
    test_bad_stable_1_clue()
    test_bad_rank_trash_push_clue()
    t1 = dt.datetime.now()
    print(f"All tests passed in {(t1 - t0).total_seconds():.2f}s!")

if __name__ == '__main__':
    test_all()