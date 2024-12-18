import game_state
from game_state import COLOR_CLUE, RANK_CLUE, Card, GameState, get_all_cards, get_random_deck, get_all_touched_cards
from test_functions import all_rank, all_suit, check_eq
import numpy as np
import datetime as dt
from typing import Dict, Optional, List, Tuple, Union
import requests
import json


def get_deck_from_tuples(tups: List[Tuple[int, int]]):
    return [Card(order, x[0], x[1]) for order, x in enumerate(tups)]


def create_game_states(
    players: Union[int, List[str]],
    variant_name: str,
    game_state_cls=GameState,
    seed: int = 20000,
    deck: Optional[List[Card]] = None,
    stacks: Optional[List[int]] = None,
):
    np.random.seed(seed)
    if isinstance(players, int):
        player_names = [f"test{x}" for x in range(players)]
    else:
        player_names = players
    
    states = {
        player_index: game_state_cls(variant_name, player_names, player_index)
        for player_index, _ in enumerate(player_names)
    }
    if deck is None:
        deck = get_random_deck(variant_name)
    num_cards_per_player = {2: 5, 3: 5, 4: 4, 5: 4, 6: 3}[len(states)]
    order = 0
    for player_index, player_name in enumerate(states):
        for _ in range(num_cards_per_player):
            card = deck.pop(0)
            for player_iterate in states:
                if player_iterate == player_name:
                    states[player_iterate].handle_draw(player_index, order, -1, -1)
                else:
                    states[player_iterate].handle_draw(
                        player_index, order, card.suit_index, card.rank
                    )
                if stacks is not None:
                    states[player_iterate].stacks = stacks
            order += 1

    return states


def give_clue(
    states: Dict[int, game_state.GameState],
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
        _state.clue_tokens -= 1


def draw(
    states: Dict[int, game_state.GameState],
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


def discard(states: Dict[int, game_state.GameState], order: int):
    player_index, i = states[0].order_to_index[order]
    another_player = 0 if player_index != 0 else 1
    card_visible = states[another_player].hands[player_index][i]
    assert card_visible.order == order
    for _state in states.values():
        _state.handle_discard(
            player_index, order, card_visible.suit_index, card_visible.rank
        )
        _state.turn += 1
        _state.clue_tokens += 1
    return player_index


def play(states: Dict[int, game_state.GameState], order: int):
    player_index, i = states[0].order_to_index[order]
    another_player = 0 if player_index != 0 else 1
    dummy_state = states[another_player]
    dummy_state_playables = dummy_state.playables
    card_visible = dummy_state.hands[player_index][i]
    assert card_visible.order == order
    for _state in states.values():
        if (card_visible.suit_index, card_visible.rank) in dummy_state_playables:
            _state.handle_play(
                player_index, order, card_visible.suit_index, card_visible.rank
            )
        else:
            _state.handle_discard(
                player_index, order, card_visible.suit_index, card_visible.rank
            )
            _state.bombs += 1
        _state.turn += 1
    return player_index


def play_draw(
    states: Dict[int, game_state.GameState],
    order: int,
    draw_order: int,
    draw_suit_index: int,
    draw_rank: int,
):
    player_index = play(states, order)
    draw(states, draw_order, player_index, draw_suit_index, draw_rank)


def discard_draw(
    states: Dict[int, game_state.GameState],
    order: int,
    draw_order: int,
    draw_suit_index: int,
    draw_rank: int,
):
    player_index = discard(states, order)
    draw(states, draw_order, player_index, draw_suit_index, draw_rank)


def get_game_state_from_replay(id_, turn, game_state_cls: GameState):
    var_id_to_name = {x["id"]: x["name"] for x in json.load(open("variants.json", "r"))}
    blob = requests.get(f"https://hanab.live/export/{id_}").json()
    variant_name = var_id_to_name[int(blob["seed"].split("v")[-1].split("s")[0])]
    deck = get_deck_from_tuples([(x["suitIndex"], x["rank"]) for x in blob["deck"]])
    states = create_game_states(
        blob["players"],
        variant_name,
        game_state_cls=game_state_cls,
        deck=deck
    )
    next_card_order = len(states) * len(states[0].hands[0])
    for i in range(turn-1):
        # type 0 = play, target = order
        # type 1 = discard, target = order
        # type 2 = clue color, target = player index, value = clue value
        # type 3 = clue rank, target = player index, value = clue value
        draw_rank, draw_suit_index = None, None
        giver = i % len(states)
        x = blob["actions"][i]

        if x["type"] == 0:
            if len(deck):
                draw_suit_index, draw_rank = deck.pop(0).to_tuple()
                play_draw(states, x["target"], next_card_order, draw_suit_index, draw_rank)
                next_card_order += 1
            else:
                play(states, x["target"])
        elif x["type"] == 1:
            if len(deck):
                draw_suit_index, draw_rank = deck.pop(0).to_tuple()
                discard_draw(states, x["target"], next_card_order, draw_suit_index, draw_rank)
                next_card_order += 1
            else:
                discard(states, x["target"])
        elif x["type"] == 2:
            give_clue(states, giver, COLOR_CLUE, x["value"], x["target"])
        elif x["type"] == 3:
            give_clue(states, giver, RANK_CLUE, x["value"], x["target"])
        else:
            raise NotImplementedError(x["type"])

    return states


def test_max_num_cards():
    expected_max_num_cards = {
        (suit_index, rank): (
            3
            if (suit_index < 4 and rank == 1)
            else (2 if suit_index < 4 and rank in {2, 3, 4} else 1)
        )
        for suit_index in range(6)
        for rank in range(1, 6)
    }
    state0 = create_game_states(3, "Black & Dark Rainbow (6 Suits)")[0]
    state1 = create_game_states(3, "Dark Pink & Dark Omni (6 Suits)")[0]
    state2 = create_game_states(3, "Gray & Cocoa Rainbow (6 Suits)")[0]
    state3 = create_game_states(3, "Dark Brown & Gray Pink (6 Suits)")[0]
    state4 = create_game_states(3, "Dark Null & Dark Prism (6 Suits)")[0]
    for state in [state0, state1, state2, state3, state4]:
        check_eq(state.max_num_cards, expected_max_num_cards)


def test_trash():
    variant_name = "Black (6 Suits)"
    STATES_3P = create_game_states(3, variant_name)
    state = STATES_3P[0]
    check_eq(state.trash, set())
    state.stacks = [1, 0, 0, 3, 0, 0]
    check_eq(state.trash, {(0, 1), (3, 1), (3, 2), (3, 3)})
    state.discards[(2, 3)] = 2
    check_eq(state.trash, {(0, 1), (3, 1), (3, 2), (3, 3), (2, 4), (2, 5)})
    state.discards[(5, 4)] = 1
    check_eq(state.trash, {(0, 1), (3, 1), (3, 2), (3, 3), (2, 4), (2, 5), (5, 5)})
    state.discards[(5, 2)] = 1
    check_eq(
        state.trash,
        {(0, 1), (3, 1), (3, 2), (3, 3), (2, 4), (2, 5), (5, 3), (5, 4), (5, 5)},
    )


def test_reversed():
    variant_name = "White Reversed (5 Suits)"
    STATES_3P = create_game_states(3, variant_name)
    state = STATES_3P[0]
    check_eq(state.stacks, [0, 0, 0, 0, 6])
    check_eq(state.trash, set())
    check_eq(state.criticals, {(0, 5), (1, 5), (2, 5), (3, 5), (4, 1)})
    check_eq(state.playables, {(0, 1), (1, 1), (2, 1), (3, 1), (4, 5)})
    state.discards[(4, 5)] = 2
    check_eq(state.criticals, {(0, 5), (1, 5), (2, 5), (3, 5), (4, 1), (4, 5)})
    state.stacks = [0, 0, 0, 0, 4]
    state.discards[(4, 2)] = 1
    check_eq(state.trash, {(4, 4), (4, 5)})
    check_eq(state.criticals, {(0, 5), (1, 5), (2, 5), (3, 5), (4, 1), (4, 2)})
    check_eq(state.playables, {(0, 1), (1, 1), (2, 1), (3, 1), (4, 3)})
    state.discards[(4, 3)] = 2
    check_eq(state.trash, {(4, 4), (4, 5), (4, 2), (4, 1)})


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
    all_cards = game_state.get_all_cards(variant_name)
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
    test_max_num_cards()
    test_trash()
    test_reversed()
    test_criticals()
    test_process_visible_cards()
    test_handle_clue()
    t1 = dt.datetime.now()
    print(f"All tests passed in {(t1 - t0).total_seconds():.2f}s!")


if __name__ == "__main__":
    test_all()
