from card import RichCard, Empathy
from constants import COLOR_CLUE, RANK_CLUE
from deck import get_deck_from_tuples
from hand import Hand

# p0 | p3 g1 y2 k1 p1
# p1 | k4 y4 b3 r5 k2
# p2 | p2 b1 g3 r2 b5

variant_name = "Black (6 Suits)"
deck = get_deck_from_tuples([
    (4,1), (5,1), (1,2), (2,1), (4,2),
    (5,2), (0,5), (3,3), (1,4), (5,4),
    (3,5), (0,2), (2,3), (3,1), (4,2)
])

h1 = Hand(variant_name)
h2 = Hand(variant_name)
h3 = Hand(variant_name)
for hand in [h1, h2, h3]:
    for i in range(5):
        card = deck.pop()
        hand.draw(card)

print(h1.get_card_tuples() + h3.get_card_tuples())


empathy = Empathy("Omni (5 Suits)", (1, 1))
empathy.remove((4,5))
empathy.update_inferences({(2,1),(1,1),(1,2),(3,2)})
print(empathy)
empathy.handle_clue(RANK_CLUE, 1, True)
print(empathy)