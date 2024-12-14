from variants import get_all_cards
from game_state import COLOR_CLUE, RANK_CLUE
from tes_helpers import all_rank, all_suit, check_eq, create_game_states
import datetime as dt


def test_criticals():
    variant_name = "Black (5 Suits)"
    STATES_3P = create_game_states(3, variant_name)
    state = STATES_3P[0]
    basecrits = {(0, 5), (1, 5), (2, 5), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5)}
    check_eq(state.criticals, basecrits)
    state.stacks = [0, 0, 2, 0, 2]
    state.discards = {(2, 1): 2, (2, 4): 1, (1, 2): 1, (3, 1): 2, (4, 5): 1}
    check_eq(
        state.criticals,
        basecrits.union({(1, 2), (2, 4), (3, 1)}).difference({(4, 1), (4, 2), (4, 5)}),
    )
    check_eq(state.non_5_criticals, {(1, 2), (2, 4), (3, 1), (4, 3), (4, 4)})


def test_process_visible_cards_1():
    # p0: p3 [ 4], g1 [ 3], y2 [ 2], k1 [ 1], p1 [ 0]
    # p1: k4 [ 9], y4 [ 8], b3 [ 7], r5 [ 6], k2 [ 5]
    # p2: p2 [14], b1 [13], g3 [12], r2 [11], b5 [10]
    BLACK_6 = create_game_states(3, "Black (6 Suits)")
    all_cards = get_all_cards(BLACK_6[0].variant_name)
    for player_index in range(3):
        for rich_card in BLACK_6[player_index].our_hand:
            candidates = rich_card.empathy.candidates
            if player_index == 0:
                check_eq(
                    candidates,
                    all_cards.difference({(0, 5), (3, 5), (5, 2), (5, 4)}),
                )
            elif player_index == 1:
                check_eq(candidates, all_cards.difference({(3, 5), (5, 1)}))
            else:
                check_eq(
                    candidates,
                    all_cards.difference({(0, 5), (5, 2), (5, 4), (5, 1)}),
                )

def test_process_visible_cards_2():
    BLACK_6 = create_game_states(3, "Black (6 Suits)")
    state0 = BLACK_6[0]
    state0.discards[(3, 1)] = 2
    state0.process_visible_cards()

    all_cards = get_all_cards(BLACK_6[0].variant_name)
    our_hand = state0.hands[0].rich_cards
    check_eq(
        our_hand[0].empathy.candidates,
        all_cards.difference({(0, 5), (3, 5), (5, 2), (5, 4), (3, 1)}),
    )
    state0.discards[(4, 5)] = 1
    state0.process_visible_cards()
    check_eq(
        our_hand[0].empathy.candidates,
        all_cards.difference({(0, 5), (3, 5), (5, 2), (5, 4), (3, 1), (4, 5)}),
    )

    our_hand[1].empathy.restrict_empathy({(5, 1)})
    state0.process_visible_cards()
    check_eq(
        our_hand[2].empathy.candidates,
        all_cards.difference({(0, 5), (3, 5), (5, 2), (5, 4), (3, 1), (4, 5), (5, 1)}),
    )

    our_hand[0].empathy.restrict_empathy({(1, 2)})
    our_hand[2].empathy.restrict_empathy({(1, 2)})
    state0.process_visible_cards()
    check_eq(
        our_hand[3].empathy.candidates,
        all_cards.difference(
            {(0, 5), (3, 5), (5, 2), (5, 4), (3, 1), (4, 5), (5, 1), (1, 2)}
        ),
    )

    our_hand[3].empathy.restrict_empathy({(1, 5)})
    state0.process_visible_cards()
    check_eq(
        our_hand[4].empathy.candidates,
        all_cards.difference(
            {(0, 5), (3, 5), (5, 2), (5, 4), (3, 1), (4, 5), (5, 1), (1, 2), (1, 5)}
        ),
    )

def test_process_visible_cards_3():
    BLACK_6 = create_game_states(3, "Black (6 Suits)")
    # test doubletons - self elim
    state1 = BLACK_6[0]
    all_cards = get_all_cards(BLACK_6[0].variant_name)
    our_hand = state1.hands[0].rich_cards
    bob_hand = state1.hands[1].rich_cards
    cathy_hand = state1.hands[2].rich_cards

    our_hand[0].empathy.restrict_empathy({(1, 3), (5, 4)})
    our_hand[1].empathy.restrict_empathy({(1, 3), (5, 4)})
    state1.process_visible_cards()
    check_eq(our_hand[0].empathy.candidates, {(1, 3)})
    check_eq(our_hand[3].empathy.candidates, all_cards.difference({(1,3), (5,4), (0,5), (3,5), (5,2)}))

    state1.discards[(4,4)] = 1
    state1.discards[(4,3)] = 1

    our_hand[2].empathy.restrict_empathy({(4, 4), (4, 3)})
    our_hand[3].empathy.restrict_empathy({(4, 4), (4, 3)})
    state1.process_visible_cards()
    check_eq(
        our_hand[4].empathy.candidates,
        all_cards.difference({(1,3), (5,4), (0,5), (3,5), (5,2), (4,4), (4,3)}),
    )
    # cross elim
    check_eq(
        bob_hand[0].empathy.candidates,
        all_cards.difference({(1,3), (4,3), (4,4), (3,5)}),
    )
    check_eq(
        cathy_hand[0].empathy.candidates,
        all_cards.difference({(1,3), (4,3), (4,4), (0,5), (5,2), (5,4)}),
    )

def test_process_visible_cards_4():
    BLACK_6 = create_game_states(3, "Black (6 Suits)")
    # test tripletons - self elim
    state2 = BLACK_6[0]
    all_cards = get_all_cards(BLACK_6[0].variant_name)
    our_hand = state2.hands[0].rich_cards
    bob_hand = state2.hands[1].rich_cards
    cathy_hand = state2.hands[2].rich_cards
    
    our_hand[0].empathy.restrict_empathy({(4, 2), (5, 3), (2, 5)})
    our_hand[1].empathy.restrict_empathy({(4, 2), (5, 3), (2, 5)})
    our_hand[2].empathy.restrict_empathy({(4, 2), (5, 3), (2, 5)})
    state2.process_visible_cards()
    check_eq(
        our_hand[3].empathy.candidates,
        all_cards.difference({(4,2), (5,3), (2,5), (0,5), (5,4), (3,5), (5,2)}),
    )
    # cross elim
    check_eq(
        bob_hand[0].empathy.candidates,
        all_cards.difference({(4,2), (5,3), (2,5), (3,5)}),
    )
    check_eq(
        cathy_hand[0].empathy.candidates,
        all_cards.difference({(5,3), (2,5), (5,2), (0,5), (5,4)}),
    )

def test_process_visible_cards_5():
    SUITS_6 = create_game_states(3, "6 Suits", seed=2)
    # test quads - self elim
    state2 = SUITS_6[0]
    all_cards = get_all_cards(SUITS_6[0].variant_name)
    our_hand = state2.hands[0].rich_cards
    bob_hand = state2.hands[1].rich_cards
    cathy_hand = state2.hands[2].rich_cards
    
    our_hand[0].empathy.restrict_empathy({(x,5) for x in range(6)})
    our_hand[1].empathy.restrict_empathy({(x,5) for x in range(6)})
    our_hand[2].empathy.restrict_empathy({(x,5) for x in range(6)})
    our_hand[3].empathy.restrict_empathy({(x,5) for x in range(6)})
    bob_hand[3].empathy.restrict_empathy({(x,5) for x in range(6)})
    cathy_hand[4].empathy.restrict_empathy({(x,5) for x in range(6)})
    state2.process_visible_cards()
    check_eq(
        our_hand[4].empathy.candidates,
        all_cards.difference({(2,4), (0,5), (1,5), (2,5), (3,5), (4,5), (5,5)}),
    )
    check_eq(bob_hand[3].empathy.candidates, {(4,5)})
    check_eq(cathy_hand[4].empathy.candidates, {(0,5)})


def test_handle_clue():
    variant_name = "Black (6 Suits)"
    STATES_3P = create_game_states(3, variant_name)
    # p0: p3 [ 4], g1 [ 3], y2 [ 2], k1 [ 1], p1 [ 0]
    # p1: k4 [ 9], y4 [ 8], b3 [ 7], r5 [ 6], k2 [ 5]
    # p2: p2 [14], b1 [13], g3 [12], r2 [11], b5 [10]
    state = STATES_3P[1]
    state.handle_clue(0, 1, COLOR_CLUE, 5, [5, 9])
    state.handle_clue(0, 1, RANK_CLUE, 4, [8, 9])
    print(state)

    check_eq(state.our_hand[0].empathy.candidates, {(5, 2), (5, 3), (5, 5)})
    check_eq(
        state.our_hand[1].empathy.candidates,
        get_all_cards(variant_name).difference(
            all_suit(5).union(all_rank(4, range(6))).union({(3, 5)})
        ),
    )
    check_eq(
        state.our_hand[2].empathy.candidates,
        get_all_cards(variant_name).difference(
            all_suit(5).union(all_rank(4, range(6))).union({(3, 5)})
        ),
    )
    check_eq(state.our_hand[3].empathy.candidates, {(0, 4), (1, 4), (2, 4), (3, 4), (4, 4)})
    check_eq(state.our_hand[4].empathy.candidates, {(5, 4)})
    rank_clued = state.get_clued_cards(type_=RANK_CLUE)
    color_clued = state.get_clued_cards(type_=COLOR_CLUE)
    check_eq({x.card.order for x in rank_clued}, {8, 9})
    check_eq({x.card.order for x in color_clued}, {5, 9})


def test_all():
    t0 = dt.datetime.now()
    test_criticals()
    test_process_visible_cards_1()
    test_process_visible_cards_2()
    test_process_visible_cards_3()
    test_process_visible_cards_4()
    test_process_visible_cards_5()
    test_handle_clue()
    t1 = dt.datetime.now()
    print(f"All tests passed in {(t1 - t0).total_seconds():.2f}s!")


if __name__ == "__main__":
    test_all()
