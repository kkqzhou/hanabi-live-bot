from constants import CardTuple, TextInt, COLOR_CLUE, RANK_CLUE
from variants import SUITS, get_all_cards, get_all_touched_cards, get_all_cards_with_multiplicity

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
        self.all_card_counts: Dict[CardTuple, int] = Counter(get_all_cards_with_multiplicity(self.variant_name))
        self.candidates: Set[CardTuple] = get_all_cards(self.variant_name)
        if isinstance(actual, Card):
            self.actual = actual.to_tuple()
        else:
            self.actual = actual
        self.inferences: Set[CardTuple] = inferences or get_all_cards(self.variant_name)
    
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
    
    def set_empathy(self, card_tuples: Set[CardTuple]):
        self.candidates = card_tuples
        self.update_inferences(card_tuples)
    
    def remove(self, card_tuple: CardTuple):
        if card_tuple in self.candidates:
            self.candidates.remove(card_tuple)
        if card_tuple in self.inferences:
            self.inferences.remove(card_tuple)

    def update_inferences(self, new_inferences: Set[CardTuple]):
        self.inferences = self.inferences.intersection(new_inferences)
    
    def handle_clue(self, clue_type: TextInt, clue_value: int, touched: bool):
        card_tuples_touched = get_all_touched_cards(clue_type, clue_value, self.variant_name)
        if touched:
            self.candidates = self.candidates.intersection(card_tuples_touched)
            self.inferences = self.inferences.intersection(card_tuples_touched)
        else:
            self.candidates = self.candidates.difference(card_tuples_touched)
            self.inferences = self.inferences.difference(card_tuples_touched)

    def sees_cards(self, card_counts: Dict[CardTuple, int]):
        for card_tuple, count in card_counts.items():
            if count == self.all_card_counts[card_tuple]:
                if card_tuple in self.candidates:
                    self.candidates.remove(card_tuple)
                    self.inferences.remove(card_tuple)


class RichCard(Card):
    def __init__(self, card: Card, variant_name: str):
        self.card = card
        self.is_rank_clued = False
        self.is_color_clued = False
        self.empathy = Empathy(variant_name, actual=card)

    def __str__(self):
        if self.is_rank_clued and self.is_color_clued:
            cluedness_char = "+"
        elif self.is_rank_clued:
            cluedness_char = "-"
        elif self.is_color_clued:
            cluedness_char = "|"
        else:
            cluedness_char = " "
        return str(self.empathy) + "\n" + cluedness_char
    
    def handle_clue(self, clue_type: TextInt, clue_value: int, touched: bool):
        self.empathy.handle_clue(clue_type, clue_value, touched)
        if clue_type == COLOR_CLUE and touched:
            self.is_color_clued = True
        if clue_type == RANK_CLUE and touched:
            self.is_rank_clued = True


def get_locked_identities(empathies: List[Empathy], cards_seen: Dict[CardTuple, int]) -> Tuple[int, List[CardTuple]]:
    # say the hand had these empathies, with one copy of y2 seen elsewhere:
    #
    # .....  .....  ..... ..... .....
    # .*.*.  .*.*.  ..... .*.*. .....
    # .....  .....  ..... ..... *****
    # .....  .....  ..... ..... .....
    # .*...  .*...  .*... ..... .....
    # 
    # we want: [(0, [(1,1), (3,1), (3,1)]), (1, [(1,1), (3,1), (3,1)]), (2, [(1,5)]), (3, [(1,1), (3,1), (3,1)])]
    # and also delete the y5 empathies from index 0 and index 1
    result = []
    n = len(empathies)
    processed_idxs = set()
    for id_length in range(1, 6):
        locked_n = [i for i in range(n) if len(empathies[i].candidates) <= id_length and i not in processed_idxs]
        if len(locked_n) < id_length:
            continue
        
        filtered_idxs: Dict[int] = {}
        for idx in locked_n:
            empathy = empathies[idx]
            num_needed = Counter({
                x: empathy.all_card_counts[x] - cards_seen.get(x, 0) for x in empathy.candidates
            })
            if num_needed.total() > id_length:
                continue
            filtered_idxs[idx] = num_needed

        if len(filtered_idxs):
            print(filtered_idxs)
            1/0

        groupings: List[Set[CardTuple]] = []
        grouping_idxs: List[List[int]] = []
        for idx in filtered_idxs:
            empathy = empathies[idx]
            needs_new_grouping = True
            for i in range(len(groupings)):
                if len(groupings[i].union(empathy.candidates)) <= id_length:
                    groupings[i] = groupings[i].union(empathy.candidates)
                    grouping_idxs[i].append(idx)
                    needs_new_grouping = False
                    break
            
            if needs_new_grouping:
                groupings.append(empathy.candidates)
                grouping_idxs.append([idx])
    
        if id_length == 3:
            print(groupings, grouping_idxs)
        #all_accounted_for = cards_seen.get()

    return result

empathies = [Empathy("No Variant") for _ in range(5)]
empathies[0].set_empathy({(1,2), (3,2)})#, (1,5)}
empathies[1].set_empathy({(1,2), (3,2)})#, (1,5)}
empathies[2].set_empathy({(1,3), (2,3), (3,3)})
empathies[3].set_empathy({(1,2), (3,2)})#, (1,5)}
empathies[4].set_empathy({(0,3), (1,3), (2,3), (3,3), (4,3)})

if True:
    empathies = [Empathy("No Variant") for _ in range(5)]
    empathies[0].set_empathy({(1,5), (2,5)})#, (1,5)}
    empathies[1].set_empathy({(3,5), (4,5)})#, (1,5)}
    empathies[2].set_empathy({(1,3), (2,3), (3,3)})
    empathies[3].set_empathy({(1,5), (2,5)})#, (1,5)}
    empathies[4].set_empathy({(3,5), (4,5)})#, (1,5)}

print(get_locked_identities(empathies, {(1,2): 1}))
1/0

if __name__ == "__main__":
    a = RichCard(Card(0, 4, 3), "No Variant")
    a.handle_clue(RANK_CLUE, 3, True)
    a.handle_clue(COLOR_CLUE, 2, False)
    a.handle_clue(COLOR_CLUE, 4, True)
    print(a)