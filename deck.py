from card import Card
from constants import CardTuple
from variants import SUITS, get_all_cards_with_multiplicity

import numpy as np
from typing import List


def get_random_deck(variant_name: str) -> List[Card]:
    # usually used for testing purposes
    cards = get_all_cards_with_multiplicity(variant_name)
    perm = np.random.permutation(cards)
    return [Card(order, x[0], x[1]) for order, x in enumerate(perm)]


def get_deck_from_tuples(tuples: List[CardTuple]) -> List[Card]:
    return [Card(order, x[0], x[1]) for order, x in enumerate(tuples)]


def get_starting_pace(num_players: int, variant_name: str) -> int:
    num_suits = len(SUITS[variant_name])
    all_cards = get_all_cards_with_multiplicity(variant_name)
    num_cards_dealt = {2: 10, 3: 15, 4: 16, 5: 20, 6: 18}[num_players]
    return len(all_cards) - num_cards_dealt + num_players - num_suits * 5


def get_starting_efficiency(num_players: int, variant_name: str) -> float:
    num_suits = len(SUITS[variant_name])
    starting_pace = get_starting_pace(num_players, variant_name)
    clue_factor = 0.5 if "Clue Starved" in variant_name else 1
    if num_players >= 5:
        return 5 * num_suits / (8 + int((starting_pace + num_suits - 2) * clue_factor))
    return 5 * num_suits / (8 + int((starting_pace + num_suits - 1) * clue_factor))
