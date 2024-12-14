from constants import COLOR_CLUE, RANK_CLUE, ACTION, P, D
from card import RichCard
from conventions import ref_sieve
from hand import Hand
from tes_helpers import run_simple_test, check_eq, get_deck_from_tuples, unwrap
import datetime as dt

from typing import Dict, Tuple

def test_is_direct_rank_playable():
    tests = [
        (("No Variant", 1, [0,0,0,0,0]), True),
        (("No Variant", 1, [1,0,0,0,0]), True),
        (("No Variant", 1, [1,1,1,0,1]), True),
        (("No Variant", 1, [1,1,1,1,1]), False),
        (("No Variant", 2, [1,2,1,2,1]), True),
        (("No Variant", 2, [1,2,0,2,1]), False),
        (("Reversed (5 Suits)", 1, [1,0,0,0,4]), False),
        (("Reversed (5 Suits)", 1, [1,0,0,0,2]), True),
        (("Reversed (5 Suits)", 4, [3,3,4,3,2]), True),
    ]
    run_simple_test(ref_sieve.is_direct_rank_playable, tests)


def test_is_direct_rank_trash():
    tests = [
        (("No Variant", 1, [0,0,0,0,0]), False),
        (("No Variant", 1, [1,1,1,0,1]), False),
        (("No Variant", 1, [1,1,1,1,1]), True),
        (("No Variant", 2, [4,3,3,4,3]), True),
        (("Reversed (5 Suits)", 1, [1,1,2,2,4]), False),
        (("Reversed (5 Suits)", 3, [3,3,4,3,2]), True),
    ]
    run_simple_test(ref_sieve.is_direct_rank_trash, tests)


def test_get_direct_play_clues():
    v = "No Variant"
    hand = Hand(v, get_deck_from_tuples([(4,1), (3,1), (2,5), (0,1), (0,2)]))
    check_eq(
        unwrap(ref_sieve.get_direct_play_clues(hand, [0,0,0,0,0], [])),
        {(RANK_CLUE, 1): ((0,1,P), (4,1,P), (3,1,P))}
    )
    check_eq(
        unwrap(ref_sieve.get_direct_play_clues(hand, [1,0,0,0,0], [])), {}
    )
    check_eq(
        unwrap(ref_sieve.get_direct_play_clues(hand, [1,0,0,0,0], [3])),
        {(RANK_CLUE, 1): ((4,1,P), (3,1,P))}
    )
    check_eq(
        unwrap(ref_sieve.get_direct_play_clues(hand, [0,1,1,0,0], [])),
        {(RANK_CLUE, 1): ((0,1,P), (4,1,P), (3,1,P))}
    )
    check_eq(
        unwrap(ref_sieve.get_direct_play_clues(hand, [0,1,1,1,0], [])),
        {(RANK_CLUE, 1): ((0,1,P), (4,1,P))}
    )
    check_eq(
        unwrap(ref_sieve.get_direct_play_clues(hand, [0,1,1,1,1], [])),
        {(RANK_CLUE, 1): ((0,1,P),)}
    )
    check_eq(
        unwrap(ref_sieve.get_direct_play_clues(hand, [0,0,1,1,0], [3])), {}
    )
    check_eq(
        unwrap(ref_sieve.get_direct_play_clues(hand, [0,0,1,1,0], [3,1])),
        {(RANK_CLUE, 1): ((4,1,P),)}
    )
    check_eq(
        unwrap(ref_sieve.get_direct_play_clues(hand, [0,0,1,1,0], [1])),
        {(RANK_CLUE, 1): ((0,1,P),(4,1,P))}
    )


def test_get_ref_play_clues_1():
    v = "No Variant"
    hand = Hand(v, get_deck_from_tuples([(0,1), (0,1), (2,5), (3,1), (4,1)]))
    check_eq(
        unwrap(ref_sieve.get_ref_play_clues(hand, [0,0,0,0,0], [])),
        {(COLOR_CLUE, 4): (0,1,P), (COLOR_CLUE, 3): (4,1,P), (COLOR_CLUE, 2): (3,1,P)}
    )
    check_eq(
        unwrap(ref_sieve.get_ref_play_clues(hand, [0,0,4,0,0], [])),
        {(COLOR_CLUE, 4): (0,1,P), (COLOR_CLUE, 3): (4,1,P), (COLOR_CLUE, 2): (3,1,P), (COLOR_CLUE, 0): (2,5,P)}
    )
    check_eq(
        unwrap(ref_sieve.get_ref_play_clues(hand, [0,0,4,0,0], [3,4])),
        {(COLOR_CLUE, 4): (0,1,P), (COLOR_CLUE, 0): (2,5,P)}
    )


def test_get_ref_play_clues_2():
    v = "No Variant"
    hand = Hand(v, get_deck_from_tuples([(0,1), (3,1), (2,5), (4,2), (4,1)]))
    check_eq(
        unwrap(ref_sieve.get_ref_play_clues(hand, [0,0,0,0,0], [])),
        {(COLOR_CLUE, 4): (4,1,P), (COLOR_CLUE, 0): (3,1,P)}
    )
    check_eq(
        unwrap(ref_sieve.get_ref_play_clues(hand, [0,0,0,0,1], [])),
        {(COLOR_CLUE, 2): (4,2,P), (COLOR_CLUE, 0): (3,1,P)}
    )
    check_eq(
        unwrap(ref_sieve.get_ref_play_clues(hand, [0,0,0,0,0], [4])),
        {(COLOR_CLUE, 2): (4,2,P), (COLOR_CLUE, 0): (3,1,P)}
    )


def test_get_ref_discard_clues_1():
    v = "No Variant"
    hand = Hand(v, get_deck_from_tuples([(0,3), (3,4), (2,5), (4,2), (4,1)]))
    check_eq(
        unwrap(ref_sieve.get_ref_discard_clues(hand, [0,0,0,0,0], [])),
        {(RANK_CLUE, 2): (2,5,D), (RANK_CLUE, 5): (3,4,D), (RANK_CLUE, 4): (0,3,D)}
    )
    check_eq(
        unwrap(ref_sieve.get_ref_discard_clues(hand, [1,0,0,0,0], [])),
        {(RANK_CLUE, 2): (2,5,D), (RANK_CLUE, 5): (3,4,D), (RANK_CLUE, 4): (0,3,D)}
    )
    check_eq(
        unwrap(ref_sieve.get_ref_discard_clues(hand, [1,1,1,1,0], [])),
        {(RANK_CLUE, 2): (2,5,D), (RANK_CLUE, 5): (3,4,D), (RANK_CLUE, 4): (0,3,D)}
    )
    check_eq(
        unwrap(ref_sieve.get_ref_discard_clues(hand, [1,1,1,1,1], [])),
        {(RANK_CLUE, 5): (3,4,D), (RANK_CLUE, 4): (0,3,D)}
    )

    hand(5).handle_clue(COLOR_CLUE, 0, True)
    check_eq(
        unwrap(ref_sieve.get_ref_discard_clues(hand, [0,0,0,0,0], [])),
        {(RANK_CLUE, 2): (2,5,D), (RANK_CLUE, 5): (3,4,D)}
    )


def test_get_ref_discard_clues_2():
    v = "No Variant"
    hand = Hand(v, get_deck_from_tuples([(0,3), (3,4), (2,4), (3,5), (4,5)]))
    check_eq(
        unwrap(ref_sieve.get_ref_discard_clues(hand, [0,0,0,0,0], [])),
        {(RANK_CLUE, 4): (0,3,D), (RANK_CLUE, 5): (2,4,D)}
    )

    hand(2).handle_clue(COLOR_CLUE, 3, True)
    check_eq(
        unwrap(ref_sieve.get_ref_discard_clues(hand, [0,0,0,0,0], [])),
        {(RANK_CLUE, 4): (0,3,D), (RANK_CLUE, 5): (2,4,D)}
    )

    hand(1).handle_clue(RANK_CLUE, 5, True)
    check_eq(
        unwrap(ref_sieve.get_ref_discard_clues(hand, [0,0,0,0,0], [])),
        {(RANK_CLUE, 4): (0,3,D)}
    )
    
    hand(5).handle_clue(RANK_CLUE, 3, True)
    check_eq(
        unwrap(ref_sieve.get_ref_discard_clues(hand, [0,0,0,0,0], [])), {}
    )


def test_get_safe_action_clues_1():
    v = "No Variant"
    hand = Hand(v, get_deck_from_tuples([(0,1), (3,4), (2,4), (2,4), (4,1)]))
    check_eq(
        unwrap(ref_sieve.get_safe_action_clues(hand, [0,0,0,0,0], False)), {}
    )

    hand(5).handle_clue(RANK_CLUE, 1, True)
    check_eq(
        unwrap(ref_sieve.get_safe_action_clues(hand, [0,0,0,0,0], False)), {}
    )

    hand(5).empathy.reset_empathy()
    hand(5).is_rank_clued = False
    hand(5).handle_clue(COLOR_CLUE, 0, True)
    check_eq(
        unwrap(ref_sieve.get_safe_action_clues(hand, [0,0,0,0,0], False)),
        {(RANK_CLUE, 1): ((0,1,P),)}
    )
    check_eq(
        unwrap(ref_sieve.get_safe_action_clues(hand, [0,0,0,0,1], False)), {}
    )
    check_eq(
        unwrap(ref_sieve.get_safe_action_clues(hand, [1,0,0,0,0], False)),
        {(RANK_CLUE, 1): ((0,1,D),)}
    )

    hand(2).handle_clue(COLOR_CLUE, 2, True)
    hand(3).handle_clue(COLOR_CLUE, 2, True)
    check_eq(
        unwrap(ref_sieve.get_safe_action_clues(hand, [0,0,0,0,0], False)),
        {(RANK_CLUE, 1): ((0,1,P),), (RANK_CLUE, 4): ((2,4,D), (2,4,D))}
    )


def test_get_safe_action_clues_2():
    v = "No Variant"
    hand = Hand(v, get_deck_from_tuples([(0,1), (3,4), (2,4), (2,4), (4,1)]))
    check_eq(
        unwrap(ref_sieve.get_safe_action_clues(hand, [0,0,0,0,0], False)), {}
    )


def test_all():
    t0 = dt.datetime.now()
    test_is_direct_rank_playable()
    test_is_direct_rank_trash()
    test_get_direct_play_clues()
    test_get_ref_play_clues_1()
    test_get_ref_play_clues_2()
    test_get_ref_discard_clues_1()
    test_get_ref_discard_clues_2()
    test_get_safe_action_clues_1()
    test_get_safe_action_clues_2()
    t1 = dt.datetime.now()
    print(f"All tests passed in {(t1 - t0).total_seconds():.2f}s!")

if __name__ == "__main__":
    test_all()