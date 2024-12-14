from card import Card, Empathy, RichCard, CardTuple
from constants import TextInt, RANK_CLUE, COLOR_CLUE
from typing import List, Optional, Tuple

from collections import Counter
from variants import get_all_touched_cards, get_available_rank_clues, get_available_color_clues


def horizontal_concat(strs, spacing: int = 2):
    """Assumes that all of the strings in strs take up the same number of rows."""
    if not len(strs):
        return ""
    nrows = len(strs[0].split("\n"))
    result = [""] * nrows
    for str_ in strs:
        str_split = str_.split("\n")
        for i in range(nrows):
            result[i] += str_split[i]
            result[i] += " " * spacing
    return "\n".join(result)


class Hand:
    def __init__(
        self,
        variant_name: str,
        cards: Optional[List[Card]] = None,
    ):
        self.variant_name = variant_name
        self.rich_cards = [RichCard(card, variant_name) for card in cards or []]
        self.filtration = [RichCard(Card(card.order, -1, -1), variant_name) for card in cards or []]

    @property
    def size(self) -> int:
        return len(self.rich_cards)
    
    def invert(self, slot_or_index: int) -> int:
        return self.size - slot_or_index
    
    def get_all_slots(self) -> List[int]:
        return [self.invert(x) for x in range(self.size-1, -1, -1)]

    def __getitem__(self, idx: int) -> RichCard:
        return self.rich_cards[idx]
    
    def __len__(self) -> int:
        return len(self.rich_cards)

    def get_slot(self, slot: int) -> RichCard:
        return self.rich_cards[self.invert(slot)]

    def __call__(self, slot: int) -> RichCard:
        return self.get_slot(slot)
    
    def get_order(self, order: int, filtration: bool = False) -> RichCard:
        for i, c in enumerate(self.rich_cards):
            if c.card.order == order:
                return self.filtration[i] if filtration else c
        raise IndexError(order)
    
    def get_filtration_order(self, order: int) -> RichCard:
        return self.get_order(order, filtration=True)
    
    def get_filtration_index(self, idx: int) -> RichCard:
        return self.filtration[idx]
    
    def get_filtration_slot(self, slot: int) -> RichCard:
        return self.get_filtration_index(self.invert(slot))
    
    def draw(self, card: Card) -> RichCard:
        rich_card = RichCard(card, self.variant_name)
        self.rich_cards.append(rich_card)
        self.filtration.append(RichCard(Card(card.order, -1, -1), self.variant_name))
        return rich_card

    def remove(self, order: int) -> RichCard:
        for i in range(len(self.size)):
            c = self.rich_cards[i]
            if c.card.order == order:
                del self.rich_cards[i]
                del self.filtration[i]
                return c
        raise IndexError(order)

    def remove_index(self, idx: int) -> RichCard:
        c = self.rich_cards[idx]
        del self.rich_cards[idx]
        return c
    
    def remove_slot(self, slot: int) -> RichCard:
        return self.remove_index(self.invert(slot))

    def __str__(self):
        return horizontal_concat([str(x) for x in reversed(self.rich_cards)])
    
    def get_card_tuples(self) -> Counter[CardTuple]:
        return Counter([x.card.to_tuple() for x in self.rich_cards])
    
    def get_clued_indices(self) -> List[int]:
        return [idx for idx, c in enumerate(self.rich_cards) if c.is_clued]
    
    def get_clued_slots(self) -> List[int]:
        return sorted([self.invert(idx) for idx, c in enumerate(self.rich_cards) if c.is_clued])

    def get_clued_orders(self) -> List[int]:
        return [c.card.order for c in self.rich_cards if c.is_clued]
    
    def get_unclued_indices(self) -> List[int]:
        return [idx for idx, c in enumerate(self.rich_cards) if not c.is_clued]
    
    def get_unclued_slots(self) -> List[int]:
        return sorted([self.invert(idx) for idx, c in enumerate(self.rich_cards) if not c.is_clued])

    def get_unclued_orders(self) -> List[int]:
        return [c.card.order for c in self.rich_cards if not c.is_clued]

    def get_touched_indices(self, clue_type: TextInt, clue_value: int) -> List[int]:
        card_tuples = get_all_touched_cards(clue_type, clue_value, self.variant_name)
        return [idx for idx, c in enumerate(self.rich_cards) if c.to_tuple() in card_tuples]
    
    def get_touched_slots(self, clue_type: TextInt, clue_value: int) -> List[int]:
        card_tuples = get_all_touched_cards(clue_type, clue_value, self.variant_name)
        return sorted([self.invert(idx) for idx, c in enumerate(self.rich_cards) if c.to_tuple() in card_tuples])

    def get_newly_touched_indices(self, clue_type: TextInt, clue_value: int) -> List[int]:
        touched_idxs = self.get_touched_indices(clue_type, clue_value)
        return sorted(set(touched_idxs).intersection(self.get_unclued_indices()))
    
    def get_newly_touched_slots(self, clue_type: TextInt, clue_value: int) -> List[int]:
        touched_slots = self.get_touched_slots(clue_type, clue_value)
        return sorted(set(touched_slots).intersection(self.get_unclued_slots()))

    def get_empathies(self) -> List[Empathy]:
        return [x.empathy for x in self.rich_cards]

    def get_filtrations(self) -> List[Empathy]:
        return [x.empathy for x in self.filtration]

    def get_legal_clues(self, type_: Optional[TextInt] = None) -> List[Tuple[TextInt, int]]:
        rank_clues = get_available_rank_clues(self.variant_name)
        color_clues = range(len(get_available_color_clues(self.variant_name)))
        result = []
        if type_ is None or type_ == RANK_CLUE:
            for rank in rank_clues:
                touched = get_all_touched_cards(RANK_CLUE, rank, self.variant_name)
                legal = False
                for x in self.rich_cards:
                    if x.to_tuple() in touched:
                        legal = True
                if legal:
                    result.append((RANK_CLUE, rank))
        
        if type_ is None or type_ == COLOR_CLUE:
            for color in color_clues:
                touched = get_all_touched_cards(COLOR_CLUE, color, self.variant_name)
                legal = False
                for x in self.rich_cards:
                    if x.to_tuple() in touched:
                        legal = True
                if legal:
                    result.append((COLOR_CLUE, color))

        return result

    def get_legal_rank_clues(self) -> List[int]:
        return [x[-1] for x in self.get_legal_clues(RANK_CLUE)]
    
    def get_legal_color_clues(self) -> List[int]:
        return [x[-1] for x in self.get_legal_clues(COLOR_CLUE)]
