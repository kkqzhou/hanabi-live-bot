from encoder import EncoderGameState
from game_state import RANK_CLUE, COLOR_CLUE, get_all_touched_cards, SUITS, Card
from test_functions import check_eq
from test_game_state import create_game_states, get_deck_from_tuples
import datetime as dt
from typing import Dict, List


def give_hat_clue(states: Dict[int, EncoderGameState], giver: int):
    state = states[giver]
    legal_clues = state.get_legal_clues()
    clue_value, clue_type, target_index = list(legal_clues)[-1]
    touched_cards = get_all_touched_cards(clue_type, clue_value, state.variant_name)
    touched_orders = [
        x.order for x in state.hands[target_index] if x.to_tuple() in touched_cards
    ]
    for _state in states.values():
        _state.handle_clue(giver, target_index, clue_type, clue_value, touched_orders)
        _state.turn += 1
    return clue_value, clue_type, target_index


def give_clue(
    states: Dict[int, EncoderGameState],
    giver: int,
    clue_type: int,
    clue_value: int,
    target_index: int,
):
    state = states[giver]
    touched_cards = get_all_touched_cards(clue_type, clue_value, state.variant_name)
    touched_orders = [
        x.order for x in state.hands[target_index] if x.to_tuple() in touched_cards
    ]
    for _state in states.values():
        _state.handle_clue(giver, target_index, clue_type, clue_value, touched_orders)
        _state.turn += 1


def discard(states: Dict[int, EncoderGameState], order: int):
    player_index, i = states[0].order_to_index[order]
    another_player = 0 if player_index != 0 else 1
    card_visible = states[another_player].hands[player_index][i]
    assert card_visible.order == order
    for _state in states.values():
        _state.handle_discard(
            player_index, order, card_visible.suit_index, card_visible.rank
        )
        _state.turn += 1
    return player_index


def play(states: Dict[int, EncoderGameState], order: int):
    player_index, i = states[0].order_to_index[order]
    another_player = 0 if player_index != 0 else 1
    card_visible = states[another_player].hands[player_index][i]
    assert card_visible.order == order
    for _state in states.values():
        _state.handle_play(
            player_index, order, card_visible.suit_index, card_visible.rank
        )
        _state.turn += 1
    return player_index


def draw(
    states: Dict[int, EncoderGameState],
    order: int,
    player_index: int,
    suit_index: int,
    rank: int,
):
    for p_index, state in states.items():
        if p_index == player_index:
            state.handle_draw(player_index, order, -1, -1)
        else:
            state.handle_draw(player_index, order, suit_index, rank)


def play_draw(
    states: Dict[int, EncoderGameState],
    order: int,
    draw_order: int,
    draw_suit_index: int,
    draw_rank: int,
):
    player_index = play(states, order)
    draw(states, draw_order, player_index, draw_suit_index, draw_rank)


def discard_draw(
    states: Dict[int, EncoderGameState],
    order: int,
    draw_order: int,
    draw_suit_index: int,
    draw_rank: int,
):
    player_index = discard(states, order)
    draw(states, draw_order, player_index, draw_suit_index, draw_rank)


def construct_test_state(
    variant_name: str, hand_strs: List[List[str]]
) -> Dict[int, EncoderGameState]:
    """
    Accepts a list of lists as follows (as you would see in hanab.live):
    [
        [order_3, order_2, order_1, order_0],
        [order_7, order_6, order_5, order_4],
        ...
    ]

    where order_0 = {suit_str}{rank} and suit_str -> suit is defined in the function.
    """
    suit_str_to_suit = {
        "Red": "r",
        "Yellow": "y",
        "Green": "g",
        "Blue": "b",
        "Purple": "p",
        "Teal": "t",
        "Black": "k",
        "Prism": "i",
        "Rainbow": "m",
        "Pink": "i",
        "Light Pink": "i",
        "Brown": "n",
        "Muddy Rainbow": "m",
        "Omni": "o",
        "Null": "u",
    }
    abbr_to_suit_index = {
        suit_str_to_suit[suit]: suit_index
        for suit_index, suit in enumerate(SUITS[variant_name])
    }
    deck = []
    order = 0
    for hand_str in hand_strs:
        for card_str in reversed(hand_str):
            suit_index = abbr_to_suit_index[card_str[0]]
            rank = int(card_str[1])
            deck.append(Card(order, suit_index, rank))
            order += 1

    return create_game_states(
        len(hand_strs), variant_name, game_state_cls=EncoderGameState, deck=deck
    )


def test_evaluate_clue_score():
    variant_name = "Omni (5 Suits)"
    # fmt: off
    deck = get_deck_from_tuples(
        [
            (4, 2), (2, 2), (1, 2), (0, 2),
            (4, 3), (2, 3), (1, 3), (0, 3),
            (4, 4), (2, 4), (1, 4), (0, 4),
            (4, 5), (2, 1), (1, 1), (0, 1),
            (4, 1), (1, 1), (2, 1), (0, 1),
        ]
    )
    # fmt: on
    STATES_5P: Dict[int, EncoderGameState] = create_game_states(
        5, variant_name, game_state_cls=EncoderGameState, deck=deck
    )
    STATES_5P[0].stacks = [2, 1, 1, 0, 0]
    check_eq(STATES_5P[0].evaluate_clue_score(2, RANK_CLUE, 4), 8)
    check_eq(STATES_5P[0].evaluate_clue_score(0, COLOR_CLUE, 4), 9)
    check_eq(STATES_5P[0].evaluate_clue_score(3, COLOR_CLUE, 4), 9)
    check_eq(STATES_5P[0].evaluate_clue_score(4, RANK_CLUE, 2), 8**4)
    check_eq(STATES_5P[0].evaluate_clue_score(2, RANK_CLUE, 2), 8 * 16**3)
    check_eq(STATES_5P[0].evaluate_clue_score(3, COLOR_CLUE, 2), 9 * 15**3)
    check_eq(STATES_5P[0].evaluate_clue_score(2, COLOR_CLUE, 2), 9**2 * 15**2)


def test_superposition():
    hand_strs = [
        ["r2", "y2", "g2", "o2"],
        ["r3", "y3", "g3", "o3"],
        ["r4", "y4", "g4", "o4"],
        ["r1", "y1", "g1", "o5"],
        ["r1", "g1", "y1", "o1"],
    ]
    STATES_5P = construct_test_state("Omni (5 Suits)", hand_strs)

    give_hat_clue(STATES_5P, 0)
    for i in range(5):
        check_eq(STATES_5P[i].identities_called_to_play, {(0, 1)})

    check_eq(STATES_5P[1].superpositions[7].triggering_orders, {15, 19})
    check_eq(STATES_5P[1].superpositions[7].unexpected_trash, 0)
    check_eq(STATES_5P[1].superpositions[7].get_sp_identities(), {(0, 3)})
    check_eq(STATES_5P[2].superpositions[11].triggering_orders, {15, 19})
    check_eq(STATES_5P[2].superpositions[11].unexpected_trash, 0)
    check_eq(
        STATES_5P[2].superpositions[11].get_sp_identities(), {(0, 4), (2, 5), (4, 4)}
    )
    check_eq(STATES_5P[3].superpositions[15].triggering_orders, {19})
    check_eq(STATES_5P[3].superpositions[15].unexpected_trash, 0)
    check_eq(STATES_5P[3].superpositions[15].get_sp_identities(), {(0, 1)})
    check_eq(STATES_5P[3].our_candidates[-1], {(0, 1)})
    check_eq(STATES_5P[4].superpositions[19].triggering_orders, {15})
    check_eq(STATES_5P[4].superpositions[19].unexpected_trash, 0)
    check_eq(STATES_5P[4].superpositions[19].get_sp_identities(), {(0, 1)})
    check_eq(STATES_5P[4].our_candidates[-1], {(0, 1)})

    give_hat_clue(STATES_5P, 1)
    give_hat_clue(STATES_5P, 2)
    for i in range(5):
        check_eq(STATES_5P[i].identities_called_to_play, {(0, 1), (1, 1), (2, 1)})

    check_eq(STATES_5P[0].superpositions[3].triggering_orders, {14, 18})
    check_eq(STATES_5P[0].superpositions[3].unexpected_trash, 0)
    check_eq(STATES_5P[0].superpositions[3].get_sp_identities(), {(0, 2)})
    check_eq(STATES_5P[0].superpositions[2].triggering_orders, {13, 17})
    check_eq(STATES_5P[0].superpositions[2].unexpected_trash, 0)
    check_eq(STATES_5P[0].superpositions[2].get_sp_identities(), {(1, 2)})
    check_eq(STATES_5P[1].superpositions[6].triggering_orders, {13, 17})
    check_eq(STATES_5P[1].superpositions[6].unexpected_trash, 0)
    check_eq(STATES_5P[1].superpositions[6].get_sp_identities(), {(1, 3)})
    check_eq(STATES_5P[2].superpositions[10].triggering_orders, {14, 18})
    check_eq(STATES_5P[2].superpositions[10].unexpected_trash, 0)
    check_eq(STATES_5P[2].superpositions[10].get_sp_identities(), {(1, 4), (3, 5)})
    check_eq(STATES_5P[3].superpositions[14].triggering_orders, {18})
    check_eq(STATES_5P[3].superpositions[14].unexpected_trash, 0)
    check_eq(
        STATES_5P[3].superpositions[14].get_sp_identities(),
        {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)},
    )

    check_eq(STATES_5P[3].superpositions[13].triggering_orders, {17})
    check_eq(STATES_5P[3].superpositions[13].unexpected_trash, 0)
    check_eq(
        STATES_5P[3].superpositions[13].get_sp_identities(), {(3, 4), (0, 5), (1, 5)}
    )

    check_eq(STATES_5P[4].superpositions[18].triggering_orders, {14})
    check_eq(STATES_5P[4].superpositions[18].unexpected_trash, 0)
    check_eq(
        STATES_5P[4].superpositions[18].get_sp_identities(),
        {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)},
    )
    check_eq(STATES_5P[4].superpositions[17].triggering_orders, {13})
    check_eq(STATES_5P[4].superpositions[17].unexpected_trash, 0)
    check_eq(
        STATES_5P[4].superpositions[17].get_sp_identities(), {(3, 4), (0, 5), (1, 5)}
    )

    discard(STATES_5P, 15)
    for i in range(5):
        check_eq(STATES_5P[i].identities_called_to_play, {(0, 1), (1, 1), (2, 1)})

    check_eq(STATES_5P[4].superpositions[19].triggering_orders, set())
    check_eq(STATES_5P[4].superpositions[19].unexpected_trash, 1)
    check_eq(
        STATES_5P[4].superpositions[19].get_sp_identities(),
        {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)},
    )
    check_eq(STATES_5P[4].our_candidates[-1], {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)})

    play(STATES_5P, 14)
    for i in range(5):
        check_eq(STATES_5P[i].identities_called_to_play, {(0, 1), (2, 1)})

    check_eq(STATES_5P[3].superpositions[13].triggering_orders, set())
    check_eq(STATES_5P[3].superpositions[13].unexpected_trash, 1)
    check_eq(
        STATES_5P[3].superpositions[13].get_sp_identities(),
        {(0, 1), (1, 1), (2, 1)},
    )
    check_eq(STATES_5P[3].our_candidates[1], {(0, 1), (1, 1), (2, 1)})

    play(STATES_5P, 18)
    for i in range(5):
        check_eq(STATES_5P[i].identities_called_to_play, {(0, 1)})

    check_eq(STATES_5P[4].superpositions[17].triggering_orders, set())
    check_eq(STATES_5P[4].superpositions[17].unexpected_trash, 1)
    check_eq(
        STATES_5P[4].superpositions[17].get_sp_identities(),
        {(0, 1), (1, 1), (2, 1)},
    )
    check_eq(STATES_5P[4].our_candidates[1], {(0, 1), (1, 1), (2, 1)})


def test_superposition2():
    # https://hanab.live/replay/1024839
    hand_strs = [
        ["b1", "p5", "r3", "b2"],
        ["y1", "y5", "p4", "p3"],
        ["g2", "p1", "g5", "r4"],
        ["b3", "p2", "y3", "p4"],
        ["g1", "g1", "g1", "g4"],
    ]
    STATES_5P = construct_test_state("No Variant", hand_strs)

    give_clue(STATES_5P, 0, RANK_CLUE, 3, 1)
    play_draw(STATES_5P, 7, 20, 0, 2)
    give_clue(STATES_5P, 2, RANK_CLUE, 1, 0)
    give_clue(STATES_5P, 3, RANK_CLUE, 4, 2)

    # check
    check_eq(STATES_5P[2].superpositions[11].triggering_orders, {19})
    check_eq(STATES_5P[2].superpositions[11].unexpected_trash, 0)
    check_eq(
        STATES_5P[2].superpositions[11].get_sp_identities(),
        {(2, 2)},
    )
    check_eq(STATES_5P[2].our_candidates[-1], {(2, 2)})
    play(STATES_5P, 17)

    check_eq(STATES_5P[2].superpositions[11].triggering_orders, set())
    check_eq(STATES_5P[2].superpositions[11].unexpected_trash, 0)
    check_eq(
        STATES_5P[2].superpositions[11].get_sp_identities(),
        {(2, 2)},
    )
    check_eq(STATES_5P[2].our_candidates[-1], {(2, 2)})


def test_superposition3():
    # https://hanab.live/shared-replay/1024885
    hand_strs = [
        ["g5", "r4", "b4", "y2"],
        ["g2", "y2", "g3", "r1"],
        ["b1", "b1", "b3", "r2"],
        ["r2", "r1", "g1", "y1"],
        ["i1", "r1", "g3", "r3"],
    ]
    STATES_5P = construct_test_state("Prism (5 Suits)", hand_strs)

    give_clue(STATES_5P, 0, RANK_CLUE, 1, 3)  # t1
    give_clue(STATES_5P, 1, RANK_CLUE, 4, 0)  # t2
    play_draw(STATES_5P, 11, 20, 4, 4)  # t3
    give_clue(STATES_5P, 3, RANK_CLUE, 2, 0)  # t4
    play_draw(STATES_5P, 19, 21, 1, 1)  # t5
    discard(STATES_5P, 14)

    check_eq(STATES_5P[4].superpositions[18].triggering_orders, set())
    check_eq(STATES_5P[4].superpositions[18].unexpected_trash, 1)
    check_eq(
        STATES_5P[4].superpositions[18].get_sp_identities(),
        {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)},
    )
    check_eq(STATES_5P[4].our_candidates[-2], {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)})


def test_superposition4():
    # https://hanab.live/shared-replay/1025222
    hand_strs = [
        ["y1", "g1", "g4", "g2"],
        ["r4", "r1", "b3", "r3"],
        ["r1", "y3", "y2", "i1"],
        ["g1", "r3", "i1", "y1"],
        ["y2", "y3", "r4", "y4"],
    ]
    STATES_5P = construct_test_state("Prism (5 Suits)", hand_strs)

    give_clue(STATES_5P, 0, RANK_CLUE, 1, 1)  # t1

    check_eq(STATES_5P[3].superpositions[15].triggering_orders, {11})
    check_eq(STATES_5P[3].superpositions[15].unexpected_trash, 0)
    check_eq(
        STATES_5P[3].superpositions[15].get_sp_identities(),
        {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)},
    )
    check_eq(STATES_5P[3].our_candidates[-1], {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)})

    play_draw(STATES_5P, 6, 20, 4, 3)  # t2
    check_eq(STATES_5P[3].superpositions[15].triggering_orders, set())
    check_eq(STATES_5P[3].superpositions[15].unexpected_trash, 0)
    check_eq(
        STATES_5P[3].superpositions[15].get_sp_identities(),
        {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)},
    )
    check_eq(STATES_5P[3].our_candidates[-1], {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)})

    discard(STATES_5P, 11)  # t3
    check_eq(STATES_5P[3].superpositions[15].triggering_orders, set())
    check_eq(STATES_5P[3].superpositions[15].unexpected_trash, 0)
    check_eq(
        STATES_5P[3].superpositions[15].get_sp_identities(),
        {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)},
    )
    check_eq(STATES_5P[3].our_candidates[-1], {(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)})


def test_superpositionx():
    # https://hanab.live/shared-replay/1025753
    hand_strs = [
        ["r5", "i2", "b2", "i3"],
        ["y1", "r3", "i1", "y4"],
        ["g3", "b4", "r1", "y1"],
        ["y5", "b5", "g4", "r3"],
        ["g1", "b4", "g1", "y2"],
    ]
    STATES_5P = construct_test_state("Prism (5 Suits)", hand_strs)
    give_clue(STATES_5P, 0, COLOR_CLUE, 0, 3)
    play_draw(STATES_5P, 7, 20, 3, 2)
    give_clue(STATES_5P, 2, RANK_CLUE, 3, 3)
    give_clue(STATES_5P, 3, RANK_CLUE, 1, 2)
    play_draw(STATES_5P, 19, 21, 1, 1)  # t5
    give_clue(STATES_5P, 0, COLOR_CLUE, 1, 3)
    play_draw(STATES_5P, 5, 22, 4, 4)
    play_draw(STATES_5P, 9, 23, 0, 2)
    give_clue(STATES_5P, 3, COLOR_CLUE, 1, 4)
    play_draw(STATES_5P, 16, 24, 2, 4)  # t10
    play_draw(STATES_5P, 2, 25, 1, 4)
    give_clue(STATES_5P, 1, COLOR_CLUE, 2, 0)
    play_draw(STATES_5P, 23, 26, 0, 2)
    play_draw(STATES_5P, 12, 27, 3, 3)
    give_clue(STATES_5P, 4, COLOR_CLUE, 2, 3)  # t15
    play_draw(STATES_5P, 0, 28, 4, 1)
    play_draw(STATES_5P, 22, 29, 2, 1)
    discard_draw(STATES_5P, 26, 30, 0, 1)
    give_clue(STATES_5P, 3, RANK_CLUE, 1, 4)
    discard_draw(STATES_5P, 21, 31, 1, 3)  # t20
    discard_draw(STATES_5P, 28, 32, 0, 1)
    discard_draw(STATES_5P, 29, 33, 0, 4)
    give_clue(STATES_5P, 2, COLOR_CLUE, 3, 3)
    STATES_5P[0].print()


def test_superposition5():
    # https://hanab.live/shared-replay/1025781
    hand_strs = [
        ["i4", "b5", "r1", "r5"],
        ["i1", "r2", "r4", "r1"],
        ["g3", "b3", "i1", "b1"],
        ["b3", "y3", "r4", "g1"],
        ["b2", "b4", "b2", "b4"],
    ]
    STATES_5P = construct_test_state("Prism (5 Suits)", hand_strs)
    give_clue(STATES_5P, 0, RANK_CLUE, 3, 3)
    play_draw(STATES_5P, 7, 20, 2, 4)
    give_clue(STATES_5P, 2, RANK_CLUE, 1, 3)
    give_clue(STATES_5P, 3, COLOR_CLUE, 3, 2)
    give_clue(STATES_5P, 4, RANK_CLUE, 3, 2)  # t5
    play_draw(STATES_5P, 1, 21, 4, 1)
    play_draw(STATES_5P, 6, 22, 1, 1)
    give_clue(STATES_5P, 2, RANK_CLUE, 1, 3)
    play_draw(STATES_5P, 12, 23, 1, 1)
    give_clue(STATES_5P, 4, RANK_CLUE, 1, 2)  # t10
    discard_draw(STATES_5P, 21, 24, 4, 4)

    check_eq(STATES_5P[1].superpositions[4].triggering_orders, {8, 23})
    check_eq(STATES_5P[1].our_candidates[0], {(1, 5)})
    play_draw(STATES_5P, 22, 25, 1, 4)

    check_eq(STATES_5P[0].superpositions[0].triggering_orders, {8})
    check_eq(STATES_5P[0].superpositions[0].unexpected_trash, 0)
    check_eq(STATES_5P[0].our_candidates[0], {(0, 5)})
    check_eq(STATES_5P[1].superpositions[4].triggering_orders, {8})
    check_eq(STATES_5P[1].superpositions[4].unexpected_trash, 1)
    check_eq(4 in STATES_5P[1].trashy_orders, True)
    check_eq(STATES_5P[2].superpositions[8].triggering_orders, set())
    check_eq(STATES_5P[2].superpositions[8].unexpected_trash, 0)
    check_eq(STATES_5P[2].our_candidates[0], {(3, 1)})


def test_superposition6():
    # https://hanab.live/shared-replay/1025834
    hand_strs = [
        ["k1", "p4", "p3", "g5"],
        ["g3", "k3", "y3", "k4"],
        ["r3", "p1", "g4", "g2"],
        ["k2", "p1", "p2", "g4"],
        ["p3", "r4", "b1", "b1"],
    ]
    STATES_5P = construct_test_state("Black (6 Suits)", hand_strs)

    give_clue(STATES_5P, 0, COLOR_CLUE, 5, 1)
    give_clue(STATES_5P, 1, RANK_CLUE, 4, 0)
    give_clue(STATES_5P, 2, RANK_CLUE, 4, 3)
    give_clue(STATES_5P, 3, COLOR_CLUE, 4, 2)
    play_draw(STATES_5P, 17, 20, 0, 1)  # t5
    play_draw(STATES_5P, 3, 21, 1, 1)
    give_clue(STATES_5P, 1, COLOR_CLUE, 0, 2)

    check_eq(STATES_5P[4].superpositions[18].triggering_orders, {10, 14})
    check_eq(STATES_5P[4].superpositions[18].unexpected_trash, 0)
    check_eq(STATES_5P[4].our_candidates[1], {(0, 4), (3, 5)})
    discard_draw(STATES_5P, 10, 22, 0, 1)

    check_eq(STATES_5P[4].superpositions[18].triggering_orders, {14})
    check_eq(STATES_5P[4].superpositions[18].unexpected_trash, 0)
    check_eq(STATES_5P[4].our_candidates[1], {(0, 4), (3, 5)})


def test_all():
    t0 = dt.datetime.now()
    test_evaluate_clue_score()
    test_superposition()
    test_superposition2()
    test_superposition3()
    test_superposition4()
    test_superposition5()
    test_superposition6()
    t1 = dt.datetime.now()
    print(f"All tests passed in {(t1 - t0).total_seconds():.2f}s!")


if __name__ == "__main__":
    test_all()
    # test_superposition6()
