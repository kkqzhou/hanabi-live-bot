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


def test_process_visible_cards():
    variant_name = "Black (6 Suits)"
    STATES_3P = create_game_states(3, variant_name)
    # p0: p3 [ 4], g1 [ 3], y2 [ 2], k1 [ 1], p1 [ 0]
    # p1: k4 [ 9], y4 [ 8], b3 [ 7], r5 [ 6], k2 [ 5]
    # p2: p2 [14], b1 [13], g3 [12], r2 [11], b5 [10]
    all_cards = get_all_cards(variant_name)
    for player_index in range(3):
        for possibilities in STATES_3P[player_index].our_possibilities:
            if player_index == 0:
                check_eq(
                    possibilities,
                    all_cards.difference({(0, 5), (3, 5), (5, 2), (5, 4)}),
                )
            elif player_index == 1:
                check_eq(possibilities, all_cards.difference({(3, 5), (5, 1)}))
            else:
                check_eq(
                    possibilities,
                    all_cards.difference({(0, 5), (5, 2), (5, 4), (5, 1)}),
                )

    state0 = STATES_3P[0]
    state0.discards[(3, 1)] = 2
    state0.process_visible_cards()
    check_eq(
        state0.our_possibilities[0],
        all_cards.difference({(0, 5), (3, 5), (5, 2), (5, 4), (3, 1)}),
    )
    state0.discards[(4, 5)] = 1
    state0.process_visible_cards()
    check_eq(
        state0.our_possibilities[0],
        all_cards.difference({(0, 5), (3, 5), (5, 2), (5, 4), (3, 1), (4, 5)}),
    )

    state0.our_possibilities[1] = {(5, 1)}
    state0.process_visible_cards()
    check_eq(
        state0.our_possibilities[2],
        all_cards.difference({(0, 5), (3, 5), (5, 2), (5, 4), (3, 1), (4, 5), (5, 1)}),
    )
    state0.our_possibilities[0] = {(1, 2)}
    state0.our_possibilities[2] = {(1, 2)}
    state0.process_visible_cards()
    check_eq(
        state0.our_possibilities[3],
        all_cards.difference(
            {(0, 5), (3, 5), (5, 2), (5, 4), (3, 1), (4, 5), (5, 1), (1, 2)}
        ),
    )
    state0.our_possibilities[3] = {(1, 5)}
    state0.process_visible_cards()
    check_eq(
        state0.our_possibilities[4],
        all_cards.difference(
            {(0, 5), (3, 5), (5, 2), (5, 4), (3, 1), (4, 5), (5, 1), (1, 2), (1, 5)}
        ),
    )

    # test doubletons
    state1 = STATES_3P[1]
    state1.our_possibilities[0] = {(3, 3), (5, 4)}
    state1.our_possibilities[1] = {(3, 3), (5, 4)}
    state1.process_visible_cards()
    check_eq(state1.our_possibilities[3], all_cards.difference({(3, 5), (5, 1)}))

    state1.our_possibilities[2] = {(3, 3), (5, 4)}
    state1.process_visible_cards()
    check_eq(
        state1.our_possibilities[3],
        all_cards.difference({(3, 5), (5, 1), (3, 3), (5, 4)}),
    )
    state1.our_possibilities[0] = {(5, 4)}
    state1.process_visible_cards()
    check_eq(state1.our_possibilities[1], {(3, 3)})
    check_eq(state1.our_possibilities[2], {(3, 3)})

    # test tripletons
    state2 = STATES_3P[2]
    state2.our_possibilities[0] = {(4, 2), (5, 3), (2, 5)}
    state2.our_possibilities[1] = {(4, 2), (5, 3), (2, 5)}
    state2.our_possibilities[2] = {(4, 2), (5, 3), (2, 5)}
    state2.process_visible_cards()
    check_eq(
        state2.our_possibilities[3],
        all_cards.difference({(0, 5), (5, 2), (5, 4), (5, 1)}),
    )

    state2.discards[(4, 2)] = 1
    state2.process_visible_cards()
    check_eq(
        state2.our_possibilities[3],
        all_cards.difference({(0, 5), (5, 2), (5, 4), (5, 1), (4, 2), (5, 3), (2, 5)}),
    )


def test_handle_clue():
    variant_name = "Black (6 Suits)"
    STATES_3P = create_game_states(3, variant_name)
    # p0: p3 [ 4], g1 [ 3], y2 [ 2], k1 [ 1], p1 [ 0]
    # p1: k4 [ 9], y4 [ 8], b3 [ 7], r5 [ 6], k2 [ 5]
    # p2: p2 [14], b1 [13], g3 [12], r2 [11], b5 [10]
    state = STATES_3P[1]
    state.handle_clue(0, 1, COLOR_CLUE, 5, [5, 9])
    state.handle_clue(0, 1, RANK_CLUE, 4, [8, 9])

    check_eq(state.our_possibilities[0], {(5, 2), (5, 3), (5, 5)})
    check_eq(
        state.our_possibilities[1],
        get_all_cards(variant_name).difference(
            all_suit(5).union(all_rank(4, range(6))).union({(3, 5)})
        ),
    )
    check_eq(
        state.our_possibilities[2],
        get_all_cards(variant_name).difference(
            all_suit(5).union(all_rank(4, range(6))).union({(3, 5)})
        ),
    )
    check_eq(state.our_possibilities[3], {(0, 4), (1, 4), (2, 4), (3, 4), (4, 4)})
    check_eq(state.our_possibilities[4], {(5, 4)})
    check_eq(state.rank_clued_card_orders, {8: [4], 9: [4]})
    check_eq(state.color_clued_card_orders, {5: [5], 9: [5]})


def test_all():
    t0 = dt.datetime.now()
    test_criticals()
    test_process_visible_cards()
    test_handle_clue()
    t1 = dt.datetime.now()
    print(f"All tests passed in {(t1 - t0).total_seconds():.2f}s!")


if __name__ == "__main__":
    test_all()
