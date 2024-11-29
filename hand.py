from card import Card, Empathy, RichCard, CardTuple
from typing import Dict, List, Optional, Set

from collections import Counter

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
            if i < nrows - 1:
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

    def __getitem__(self, index: int) -> RichCard:
        return self.rich_cards[index]

    def get_slot(self, slot: int) -> RichCard:
        return self.rich_cards[-slot-1]

    def __call__(self, slot: int) -> RichCard:
        return self.get_slot(slot)
    
    def get_order(self, order: int) -> RichCard:
        for c in self.rich_cards:
            if c.card.order == order:
                return c
        raise IndexError(order)
    
    def draw(self, card: Card):
        self.rich_cards.append(RichCard(card, self.variant_name))
        self.filtration.append(RichCard(Card(card.order, -1, -1), self.variant_name))

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
        return self.remove_index(self.size - slot)

    def __str__(self):
        return horizontal_concat([str(x) for x in self.rich_cards])
    
    def get_card_tuples(self) -> Dict[CardTuple, int]:
        return Counter([x.card.to_tuple() for x in self.rich_cards])
