from card import Card
from constants import CardTuple, COLOR_CLUE, RANK_CLUE
from deck import get_random_deck
from game_state import GameState, ActionableCard
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Union, Tuple
from variants import get_all_touched_cards

import json
import requests
import numpy as np


def all_suit(suit_index: int) -> Set[CardTuple]:
    return {(suit_index, i) for i in range(1, 6)}


def all_rank(rank: int, suit_indices: List[int]) -> Set[CardTuple]:
    return {(suit_index, rank) for suit_index in suit_indices}


def check_eq(actual: Any, expected: Any):
    assert actual == expected, f"\nExpected: {expected}\nActual: {actual}"


def run_simple_test(fn: Callable, tests: Union[Dict, Tuple]):
    _tests = tests.items() if isinstance(tests, dict) else tests
    for input, exp in _tests:
        act = fn(input) if not isinstance(input, tuple) else fn(*input)
        fn_name = fn.__name__
        assert act == exp, f"{fn_name}\nInput: {input}\nExpected: {exp}\nActual: {act}"
    print(f"{len(tests)} tests for {fn_name} passed!")


def get_deck_from_tuples(tups: List[CardTuple]):
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
    states: Dict[int, GameState],
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
    states: Dict[int, GameState],
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


def discard(states: Dict[int, GameState], order: int):
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


def play(states: Dict[int, GameState], order: int):
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
    states: Dict[int, GameState],
    order: int,
    draw_order: int,
    draw_suit_index: int,
    draw_rank: int,
):
    player_index = play(states, order)
    draw(states, draw_order, player_index, draw_suit_index, draw_rank)


def discard_draw(
    states: Dict[int, GameState],
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


def unwrap(result: Dict[Any, Union[ActionableCard, Iterable[ActionableCard]]]):
    return {x: (y.to_tuple() if isinstance(y, ActionableCard) else tuple([z.to_tuple() for z in y])) for x, y in result.items()}
