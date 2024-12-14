from constants import CardTuple, TextInt, COLOR_CLUE, RANK_CLUE
from variants import SUITS, get_all_cards, get_all_touched_cards, get_all_cards_with_multiplicity
import variants

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Union, Tuple


@dataclass
class Card:
    order: int
    suit_index: int
    rank: int

    def __eq__(self, other):
        return (self.suit_index == other.suit_index) and (self.rank == other.rank)

    def __str__(self):
        if self.suit_index == -1:
            return "Unknown"
        return str(self.to_tuple())

    def __repr__(self):
        return self.__str__()

    def to_tuple(self) -> CardTuple:
        return (self.suit_index, self.rank)


class Empathy:
    def __init__(
        self,
        variant_name: str,
        actual: Union[Card, CardTuple] = (-1, -1),
        inferences: Optional[Set[CardTuple]] = None,
    ):
        self.variant_name = variant_name
        self.num_suits = len(SUITS[variant_name])
        self.all_card_counts: Counter[CardTuple] = Counter(get_all_cards_with_multiplicity(self.variant_name))
        if isinstance(actual, Card):
            self.actual = actual.to_tuple()
        else:
            self.actual = actual
        
        self.reset_empathy()
        if inferences:
            self.inferences = inferences
    
    def __str__(self):
        result = ""
        for rank in range(1, 6):
            for si in range(self.num_suits):
                if (si, rank) == self.actual:
                    result += "O"
                elif (si, rank) in self.inferences:
                    result += "*"
                elif (si, rank) in self.candidates:
                    result += "-"
                else:
                    result += "."
            result += "\n"
        return result[:-1]

    def __repr__(self):
        return self.__str__()
    
    def reset_empathy(self):
        self.candidates: Set[CardTuple] = get_all_cards(self.variant_name)
        self.inferences: Set[CardTuple] = get_all_cards(self.variant_name)
    
    def set_empathy(self, card_tuples: Set[CardTuple], reset_inferences: bool):
        self.candidates = card_tuples
        if reset_inferences:
            self.inferences = card_tuples
        else:
            self.update_inferences(card_tuples)

    def restrict_empathy(self, card_tuples: Set[CardTuple]):
        self.candidates = self.candidates.intersection(card_tuples)
        self.update_inferences(card_tuples)
    
    def remove(self, card_tuple: CardTuple):
        if card_tuple in self.candidates:
            self.candidates.remove(card_tuple)
        if card_tuple in self.inferences:
            self.inferences.remove(card_tuple)

    def update_inferences(self, new_inferences: Set[CardTuple]):
        self.inferences = self.inferences.intersection(new_inferences)
    
    def handle_clue(self, clue_type: TextInt, clue_value: int, touched: bool, commit: bool = True):
        card_tuples_touched = get_all_touched_cards(clue_type, clue_value, self.variant_name)
        if touched:
            new_candidates = self.candidates.intersection(card_tuples_touched)
            new_inferences = self.inferences.intersection(card_tuples_touched)
        else:
            new_candidates = self.candidates.difference(card_tuples_touched)
            new_inferences = self.inferences.difference(card_tuples_touched)

        if commit:
            self.candidates = new_candidates
            self.inferences = new_inferences
        return (new_candidates, new_inferences)

    def sees_cards(self, card_counts: Dict[CardTuple, int]):
        for card_tuple, count in card_counts.items():
            if count == self.all_card_counts[card_tuple]:
                if card_tuple in self.candidates:
                    self.candidates.remove(card_tuple)
                    self.inferences.remove(card_tuple)
    
    def is_playable(self, stacks: List[int]) -> bool:
        return variants.is_playable(self.inferences, self.variant_name, stacks)
    
    def is_trash(self, stacks: List[int]) -> bool:
        return variants.is_trash(self.inferences, self.variant_name, stacks)


class RichCard:
    def __init__(self, card: Card, variant_name: str):
        self.card = card
        self.is_rank_clued = False
        self.is_color_clued = False
        self.empathy = Empathy(variant_name, actual=card)

    @property
    def is_clued(self) -> bool:
        return self.is_rank_clued or self.is_color_clued
    
    def to_tuple(self) -> CardTuple:
        return self.card.to_tuple()

    def __str__(self):
        if self.is_rank_clued and self.is_color_clued:
            cluedness_char = "+"
        elif self.is_rank_clued:
            cluedness_char = "-"
        elif self.is_color_clued:
            cluedness_char = "|"
        else:
            cluedness_char = " "
        padding = " " * (len(SUITS[self.empathy.variant_name]) - 3)
        return str(self.empathy) + "\n" + str(100 + self.card.order)[-2:] + cluedness_char + padding
    
    def __repr__(self):
        return str(self.to_tuple())
    
    def handle_clue(self, clue_type: TextInt, clue_value: int, touched: bool, commit: bool = True):
        if clue_type == COLOR_CLUE and touched and commit:
            self.is_color_clued = True
        if clue_type == RANK_CLUE and touched and commit:
            self.is_rank_clued = True
        return self.empathy.handle_clue(clue_type, clue_value, touched, commit=commit)


class LockedIdentity:
    def __init__(self, indices: List[int], counts: Dict[CardTuple, int]):
        self.indices: List[int] = indices
        self.counts: Dict[CardTuple, int] = counts
    
    def __str__(self):
        return str((self.indices, self.counts))

    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        return self.indices == other.indices and self.counts == other.counts


def get_locked_identities(empathies: List[Empathy], cards_seen: Dict[CardTuple, int]) -> List[LockedIdentity]:
    # say the hand had these empathies, with one copy of y2 seen elsewhere:
    #
    # .....  .....  ..... ..... .....
    # .*.*.  .*.*.  ..... .*.*. .....
    # .....  .....  ..... ..... *****
    # .....  .....  ..... ..... .....
    # .*...  .*...  .*... ..... .....
    # 
    # we want: [([2], {(1,5): 1}), ([0,1,3], {(1,2): 1, (3,2): 2})]
    # and also delete the y5 empathies from index 0 and index 1
    if not len(empathies):
        return []

    result = []
    n = len(empathies)
    processed_idxs = set()
    all_remaining_seen = {x for x in cards_seen if empathies[0].all_card_counts[x] == cards_seen[x]}
    for empathy in empathies:
        for card_tuple in all_remaining_seen:
            empathy.remove(card_tuple)

    for _ in range(2):
        for id_length in range(1, 6):
            locked_n = [i for i in range(n) if len(empathies[i].candidates) <= id_length and i not in processed_idxs]
            if len(locked_n) < id_length:
                continue
            
            filtered_idxs: Dict[int, Counter] = {}
            for idx in locked_n:
                empathy = empathies[idx]
                num_needed = Counter({
                    x: empathy.all_card_counts[x] - cards_seen.get(x, 0) for x in empathy.candidates
                })
                if num_needed.total() > id_length:
                    continue
                filtered_idxs[idx] = num_needed

            groupings: List[Counter] = []
            grouping_idxs: List[List[int]] = []
            for idx, ctr in filtered_idxs.items():
                needs_new_grouping = True
                for i in range(len(groupings)):
                    if (groupings[i] | ctr).total() <= id_length:
                        groupings[i] = groupings[i] | ctr
                        grouping_idxs[i].append(idx)
                        needs_new_grouping = False
                        break
                
                if needs_new_grouping:
                    groupings.append(ctr)
                    grouping_idxs.append([idx])

            for i, grouping in enumerate(groupings):
                if len(grouping_idxs[i]) >= id_length:
                    processed_idxs = processed_idxs.union(set(grouping_idxs[i]))
                    result.append(LockedIdentity(grouping_idxs[i], grouping))
                    for j in range(len(empathies)):
                        if j in grouping_idxs[i]:
                            continue
                        for card_tuple in grouping:
                            empathies[j].remove(card_tuple)

    return sorted(result, key=lambda x: (len(x.indices) * 10000, x.indices))
