from constants import RANK_CLUE, COLOR_CLUE, CardTuple

import os
import json

from collections import Counter
from typing import Dict, List, Optional, Set

variants_file = os.path.join(
    os.path.realpath(os.path.dirname(__file__)), "variants.json"
)
with open(variants_file, "r") as f:
    VARIANT_INFO = json.load(f)

SUITS = {x["name"]: x["suits"] for x in VARIANT_INFO}
DARK_SUIT_NAMES = {
    "Black",
    "Gray",
    "Dark Rainbow",
    "Dark Prism",
    "Dark Pink",
    "Dark Brown",
    "Dark Omni",
    "Gray Pink",
    "Cocoa Rainbow",
    "Dark Null",
    "Black Reversed",
    "Dark Rainbow Reversed",
    "Dark Prism Reversed",
}

def get_available_rank_clues(variant_name: str) -> List[int]:
    for substr in [
        "Pink-Ones",
        "Light-Pink-Ones",
        "Omni-Ones",
        "Brown-Ones",
        "Muddy-Rainbow-Ones",
        "Null-Ones",
        "Deceptive-Ones",
    ]:
        if substr in variant_name:
            return [2, 3, 4, 5]

    for substr in [
        "Pink-Fives",
        "Light-Pink-Fives",
        "Omni-Fives",
        "Brown-Fives",
        "Muddy-Rainbow-Fives",
        "Null-Fives",
        "Deceptive-Fives",
    ]:
        if substr in variant_name:
            return [1, 2, 3, 4]

    if "Odds and Evens" in variant_name:
        return [1, 2]

    return [1, 2, 3, 4, 5]


def get_available_color_clues(variant_name: str) -> List[str]:
    available_color_clues = []

    for suit in [
        "Red",
        "Tomato",
        "Tomato VA",
        "Orange D",
        "Orange D2",
        "Purple D",
        "Cardinal D",
        "Mahogany D",
        "Yellow D",
        "Tangelo AD",
        "Peach AD",
        "Orchid AD",
        "Violet AD",
    ]:
        if suit in SUITS[variant_name]:
            available_color_clues.append("Red")
            break

    for suit in [
        "Yellow",
        "Orange D",
        "Orange D2",
        "Lime D",
        "Green D",
        "Tan D",
        "Yam MD",
        "Tangelo AD",
        "Peach AD",
        "Lime AD",
        "Forest AD",
    ]:
        if suit in SUITS[variant_name]:
            available_color_clues.append("Yellow")
            break

    for suit in ["Green", "Lime", "Lime D", "Teal D", "Yellow D", "Teal D2", "Geas MD"]:
        if suit in SUITS[variant_name]:
            available_color_clues.append("Green")
            break

    for suit in [
        "Blue",
        "Sky",
        "Sky VA",
        "Sky EA",
        "Teal D",
        "Green D",
        "Purple D",
        "Indigo D",
        "Navy D",
        "Teal D2",
        "Beatnik MD",
        "Lime AD",
        "Forest AD",
        "Orchid AD",
        "Violet AD",
    ]:
        if suit in SUITS[variant_name]:
            available_color_clues.append("Blue")
            break

    for suit in ["Purple", "Indigo D", "Cardinal D", "Plum MD"]:
        if suit in SUITS[variant_name]:
            available_color_clues.append("Purple")
            break

    for suit in ["Teal", "Taupe MD"]:
        if suit in SUITS[variant_name]:
            available_color_clues.append("Teal")
            break

    for suit in ["Black", "Mahogany D", "Tan D", "Navy D"]:
        if suit in SUITS[variant_name]:
            available_color_clues.append("Black")
            break

    for color in ["Pink", "Brown", "Dark Pink", "Dark Brown"]:
        if color in SUITS[variant_name]:
            available_color_clues.append(color)

    return available_color_clues


def get_all_cards(variant_name: str) -> Set[CardTuple]:
    cards = set()
    for i, suit in enumerate(SUITS[variant_name]):
        for rank in range(1, 6):
            cards.add((i, rank))

    return cards


def get_all_cards_with_multiplicity(variant_name: str) -> List[CardTuple]:
    cards = []
    for i, suit in enumerate(SUITS[variant_name]):
        for rank in range(1, 6):
            cards.append((i, rank))
            if rank == 1:
                if suit not in DARK_SUIT_NAMES and "Reversed" not in suit:
                    cards.append((i, rank))
                    cards.append((i, rank))
            elif rank in {2, 3}:
                if suit not in DARK_SUIT_NAMES:
                    cards.append((i, rank))
            elif rank == 4:
                if suit not in DARK_SUIT_NAMES and "Critical Fours" not in variant_name:
                    cards.append((i, rank))
            elif rank == 5:
                if suit not in DARK_SUIT_NAMES and "Reversed" in suit:
                    cards.append((i, rank))
                    cards.append((i, rank))

    return cards


def get_card_counts(variant_name: str) -> Dict[CardTuple, int]:
    return Counter(get_all_cards_with_multiplicity(variant_name))


def get_all_touched_cards(clue_type: int, clue_value: int, variant_name: str) -> Set[CardTuple]:
    available_color_clues = get_available_color_clues(variant_name)
    prism_touch = list(zip(available_color_clues * 5, [1, 2, 3, 4, 5]))
    cards = set()
    for i, suit in enumerate(SUITS[variant_name]):
        for rank in range(1, 6):
            if clue_type == COLOR_CLUE:
                if suit in {
                    "Rainbow",
                    "Dark Rainbow",
                    "Muddy Rainbow",
                    "Cocoa Rainbow",
                    "Omni",
                    "Dark Omni",
                }:
                    cards.add((i, rank))

                if (
                    suit
                    in {
                        "Tomato",
                        "Mahogany",
                        "Tomato VA",
                        "Mahogany VA",
                        "Carrot VA",
                        "Orange D",
                        "Orange D2",
                        "Purple D",
                        "Cardinal D",
                        "Mahogany D",
                        "Yellow D",
                        "Yam MD",
                        "Geas MD",
                        "Beatnik MD",
                        "Plum MD",
                        "Taupe MD",
                        "Tangelo AD",
                        "Peach AD",
                        "Orchid AD",
                        "Violet AD",
                    }
                    and available_color_clues[clue_value] == "Red"
                ):
                    cards.add((i, rank))

                if (
                    suit
                    in {
                        "Orange D",
                        "Orange D2",
                        "Lime D",
                        "Green D",
                        "Tan D",
                        "Yam MD",
                        "Geas MD",
                        "Beatnik MD",
                        "Plum MD",
                        "Taupe MD",
                        "Tangelo AD",
                        "Peach AD",
                        "Lime AD",
                        "Forest AD",
                    }
                    and available_color_clues[clue_value] == "Yellow"
                ):
                    cards.add((i, rank))

                if (
                    suit
                    in {
                        "Lime",
                        "Forest",
                        "Lime D",
                        "Teal D",
                        "Yellow D",
                        "Teal D2",
                        "Geas MD",
                        "Beatnik MD",
                        "Plum MD",
                        "Taupe MD",
                    }
                    and available_color_clues[clue_value] == "Green"
                ):
                    cards.add((i, rank))

                if (
                    suit
                    in {
                        "Sky",
                        "Navy",
                        "Sky VA",
                        "Navy VA",
                        "Berry VA",
                        "Sky EA",
                        "Navy EA",
                        "Berry EA",
                        "Ice EA",
                        "Sapphire EA",
                        "Ocean EA",
                        "Teal D",
                        "Green D",
                        "Purple D",
                        "Indigo D",
                        "Navy D",
                        "Teal D2",
                        "Beatnik MD",
                        "Plum MD",
                        "Taupe MD",
                        "Lime AD",
                        "Forest AD",
                        "Orchid AD",
                        "Violet AD",
                    }
                    and available_color_clues[clue_value] == "Blue"
                ):
                    cards.add((i, rank))

                if (
                    suit in {"Indigo D", "Cardinal D", "Plum MD", "Taupe MD"}
                    and available_color_clues[clue_value] == "Purple"
                ):
                    cards.add((i, rank))

                if suit == "Taupe MD" and available_color_clues[clue_value] == "Teal":
                    cards.add((i, rank))

                if (
                    suit in {"Mahogany D", "Tan D", "Navy D"}
                    and available_color_clues[clue_value] == "Black"
                ):
                    cards.add((i, rank))

                if suit in available_color_clues[clue_value] or (
                    suit in {"Prism", "Dark Prism"}
                    and (available_color_clues[clue_value], rank) in prism_touch
                ):
                    if (
                        "White-Ones" in variant_name
                        or "Light-Pink-Ones" in variant_name
                        or "Null-Ones" in variant_name
                    ) and rank == 1:
                        continue
                    elif (
                        "White-Fives" in variant_name
                        or "Light-Pink-Fives" in variant_name
                        or "Null-Fives" in variant_name
                    ) and rank == 5:
                        continue
                    else:
                        cards.add((i, rank))

                if (
                    (
                        "Rainbow-Ones" in variant_name
                        or "Muddy-Rainbow-Ones" in variant_name
                        or "Omni-Ones" in variant_name
                    )
                    and rank == 1
                    and suit
                    not in {
                        "White",
                        "Light Pink",
                        "Null",
                        "Gray",
                        "Gray Pink",
                        "Dark Null",
                    }
                ):
                    cards.add((i, rank))

                if (
                    (
                        "Rainbow-Fives" in variant_name
                        or "Muddy-Rainbow-Fives" in variant_name
                        or "Omni-Fives" in variant_name
                    )
                    and rank == 5
                    and suit
                    not in {
                        "White",
                        "Light Pink",
                        "Null",
                        "Gray",
                        "Gray Pink",
                        "Dark Null",
                    }
                ):
                    cards.add((i, rank))

            elif clue_type == RANK_CLUE:
                if suit in {
                    "Pink",
                    "Dark Pink",
                    "Light Pink",
                    "Gray Pink",
                    "Omni",
                    "Dark Omni",
                }:
                    cards.add((i, rank))
                if suit not in {
                    "Brown",
                    "Dark Brown",
                    "Muddy Rainbow",
                    "Cocoa Rainbow",
                    "Null",
                    "Dark Null",
                }:
                    if "Odds and Evens" in variant_name and (clue_value == rank % 2):
                        cards.add((i, rank))
                    elif "Deceptive-Ones" in variant_name and (rank == 1):
                        if i % 4 == (clue_value - 2):
                            cards.add((i, rank))
                    elif "Deceptive-Fives" in variant_name and (rank == 5):
                        if (i % 4) == (clue_value - 1):
                            cards.add((i, rank))
                    elif "Funnels" in variant_name:
                        if rank <= clue_value:
                            cards.add((i, rank))
                    elif "Chimneys" in variant_name:
                        if rank >= clue_value:
                            cards.add((i, rank))
                    elif clue_value == rank:
                        cards.add((i, rank))
                if (
                    (
                        "Pink-Ones" in variant_name
                        or "Light-Pink-Ones" in variant_name
                        or "Omni-Ones" in variant_name
                    )
                    and rank == 1
                    and suit
                    not in {
                        "Brown",
                        "Muddy Rainbow",
                        "Null",
                        "Dark Brown",
                        "Cocoa Rainbow",
                        "Dark Null",
                    }
                ):
                    cards.add((i, rank))
                if (
                    (
                        "Pink-Fives" in variant_name
                        or "Light-Pink-Fives" in variant_name
                        or "Omni-Fives" in variant_name
                    )
                    and rank == 5
                    and suit
                    not in {
                        "Brown",
                        "Muddy Rainbow",
                        "Null",
                        "Dark Brown",
                        "Cocoa Rainbow",
                        "Dark Null",
                    }
                ):
                    cards.add((i, rank))
    return cards


def is_brownish(variant_name: str) -> bool:
    num_ranks_touching_card = {x: 0 for x in get_all_cards(variant_name)}
    for rank in get_available_rank_clues(variant_name):
        cards_touched = get_all_touched_cards(RANK_CLUE, rank, variant_name)
        for x in cards_touched:
            num_ranks_touching_card[x] += 1

    for _, num_ranks in num_ranks_touching_card.items():
        if num_ranks < 1:
            return True
    return False


def is_pinkish(variant_name: str) -> bool:
    num_ranks_touching_card = {x: 0 for x in get_all_cards(variant_name)}
    for rank in get_available_rank_clues(variant_name):
        cards_touched = get_all_touched_cards(RANK_CLUE, rank, variant_name)
        for x in cards_touched:
            num_ranks_touching_card[x] += 1

    for _, num_ranks in num_ranks_touching_card.items():
        if num_ranks > 1:
            return True
    return False


def is_whiteish(variant_name: str) -> bool:
    available_color_clues = get_available_color_clues(variant_name)
    num_colors_touching_card = {x: 0 for x in get_all_cards(variant_name)}
    for color in range(len(available_color_clues)):
        cards_touched = get_all_touched_cards(COLOR_CLUE, color, variant_name)
        for x in cards_touched:
            num_colors_touching_card[x] += 1

    for _, num_colors in num_colors_touching_card.items():
        if num_colors < 1:
            return True
    return False


def is_rainbowy(variant_name: str) -> bool:
    available_color_clues = get_available_color_clues(variant_name)
    num_colors_touching_card = {x: 0 for x in get_all_cards(variant_name)}
    for color in range(len(available_color_clues)):
        cards_touched = get_all_touched_cards(COLOR_CLUE, color, variant_name)
        for x in cards_touched:
            num_colors_touching_card[x] += 1

    for _, num_colors in num_colors_touching_card.items():
        if num_colors > 1:
            return True
    return False


def get_playables(
    variant_name: str, stacks: List[int], distance: int = 1
 ) -> Set[CardTuple]:
    assert len(stacks) == len(SUITS[variant_name])
    playables = set()
    for si, stack in enumerate(stacks):
        if "Reversed" in SUITS[variant_name][si]:
            playables.add((si, stack - distance))
        else:
            playables.add((si, stack + distance))
    return playables


def get_trash(variant_name: str, stacks: List[int], discards: Optional[Dict[CardTuple, int]] = None) -> Set[CardTuple]:
    if discards is None:
        discards = {}
    trash_cards = set()
    card_counts = get_card_counts(variant_name)
    for si, stack in enumerate(stacks):
        if "Reversed" in SUITS[variant_name][si]:
            for i in range(stack, 6):
                trash_cards.add((si, i))
        else:
            for i in range(stack):
                trash_cards.add((si, i + 1))

    dead_cards = {x for x in discards if discards[x] == card_counts[x]}
    lowest_dead = {}
    for si, rank in dead_cards:
        if si not in lowest_dead:
            lowest_dead[si] = rank
        else:
            if "Reversed" in SUITS[variant_name][si]:
                lowest_dead[si] = max(lowest_dead[si], rank)
            else:
                lowest_dead[si] = min(lowest_dead[si], rank)
    
    dead_trash = set()
    for si, dead_rank in lowest_dead.items():
        if "Reversed" in SUITS[variant_name][si]:
            dead_trash = dead_trash.union({(si, x) for x in range(dead_rank, 0, -1)})
        else:
            dead_trash = dead_trash.union({(si, x) for x in range(dead_rank, 6)})

    return trash_cards.union(dead_trash.difference(dead_cards))
