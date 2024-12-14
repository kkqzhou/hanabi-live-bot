from card import Card, LockedIdentity, RichCard, get_locked_identities
from deck import get_random_deck, get_starting_pace
from hand import Hand, horizontal_concat
from constants import MAX_CLUE_NUM, COLOR_CLUE, RANK_CLUE, CardTuple, ClueTuple, TextInt, ACTION
from variants import SUITS, DARK_SUIT_NAMES, get_available_color_clues, get_available_rank_clues, get_all_touched_cards

import variants

from collections import Counter
from typing import Dict, List, Optional, Set, Tuple
import numpy as np


class ActionableCard:
    def __init__(self, rich_card: RichCard, action: ACTION):
        self.rich_card = rich_card
        self.action = action
    
    def to_tuple(self) -> Tuple[int, int, ACTION]:
        tup = self.rich_card.to_tuple()
        return (tup[0], tup[1], self.action)

    def __str__(self) -> str:
        return str(self.to_tuple())

    def __repr__(self) -> str:
        return self.__str__()


def get_all_legal_clues(
    variant_name: str,
    target_hand: List[Card],
    clue_tuples: Optional[List[ClueTuple]] = None,
) -> Dict[ClueTuple, List[int]]:
    """clue_tuple -> hand indices touched by the clue"""
    clue_to_idxs_touched = {}
    available_color_clues = get_available_color_clues(variant_name)
    available_rank_clues = get_available_rank_clues(variant_name)
    if clue_tuples is None:
        clue_tuples = [
            (COLOR_CLUE, i) for i in range(len(available_color_clues))
        ] + [(RANK_CLUE, x) for x in available_rank_clues]
    
    for clue_type, clue_value in clue_tuples:
        # prevent illegal clues from being given
        if clue_type == COLOR_CLUE and clue_value >= len(available_color_clues):
            continue
        if clue_type == RANK_CLUE and clue_value not in available_rank_clues:
            continue

        cards_touched = get_all_touched_cards(clue_type, clue_value, variant_name)
        idxs_touched = [
            i for i, card in enumerate(target_hand) if card.to_tuple() in cards_touched
        ]
        if len(idxs_touched):
            clue_to_idxs_touched[(clue_type, clue_value)] = idxs_touched

    return clue_to_idxs_touched


class GameState:
    def __init__(self, variant_name, player_names, our_player_index):
        self.set_variant_name(variant_name, len(player_names))
        self.player_names: List[str] = player_names
        self.our_player_index: int = our_player_index
        self.current_player_index: int = 0

        # Initialize the hands for each player (an array of cards)
        self.order_to_rich_card: Dict[int, RichCard] = {}
        self.hands: List[Hand] = []
        for _ in range(len(player_names)):
            self.hands.append(Hand(variant_name))

        self.clue_tokens: int = MAX_CLUE_NUM
        self.bombs: int = 0
        self.marked_cards: Dict[str, Set[int]] = {}
        self.discards: Counter[CardTuple] = Counter()  # tracks # of discards per cardtuple
        self.turn: int = 0
        self.max_score: int = 99999
        self.notes: Dict[int, str] = {}

    @property
    def num_players(self) -> int:
        return len(self.player_names)

    @property
    def our_player_name(self) -> str:
        return self.player_names[self.our_player_index]

    @property
    def playables(self) -> Set[CardTuple]:
        return variants.get_playables(self.variant_name, self.stacks)
    
    @property
    def one_away_from_playables(self) -> Set[CardTuple]:
        return variants.get_playables(self.variant_name, self.stacks, distance=2)

    @property
    def score_pct(self) -> float:
        return sum(self.stacks) / (5 * len(self.stacks))

    @property
    def max_num_cards(self) -> Counter[CardTuple]:
        return Counter(variants.get_all_cards_with_multiplicity(self.variant_name))

    @property
    def criticals(self) -> Set[Tuple[int, int]]:
        trash = self.trash
        crits = set()
        for (suit, rank), max_num in self.max_num_cards.items():
            if (suit, rank) in trash:
                continue
            if self.discards.get((suit, rank), 0) == max_num - 1:
                crits.add((suit, rank))
        return crits

    @property
    def non_5_criticals(self) -> Set[Tuple[int, int]]:
        return {(suit, rank) for (suit, rank) in self.criticals if rank != 5}

    @property
    def trash(self) -> Set[Tuple[int, int]]:
        return variants.get_trash(self.variant_name, self.stacks, discards=self.discards)

    @property
    def pace(self) -> int:
        return get_starting_pace(self.num_players, self.variant_name) - sum(
            self.discards.values()
        )

    @property
    def num_cards_in_deck(self) -> int:
        total_cards = len(variants.get_all_cards_with_multiplicity(self.variant_name))
        cards_dealt = {2: 10, 3: 15, 4: 16, 5: 20, 6: 18}[self.num_players]
        return max(
            0,
            total_cards - cards_dealt - sum(self.discards.values()) - sum(self.stacks),
        )

    @property
    def num_dark_suits(self) -> int:
        return len([x for x in SUITS[self.variant_name] if x in DARK_SUIT_NAMES])

    @property
    def our_hand(self) -> Hand:
        return self.hands[self.our_player_index]

    @property
    def num_1s_played(self) -> int:
        return sum([x > 0 for x in self.stacks])
    
    def is_playable(self, candidates: Set[CardTuple]) -> bool:
        return not len(candidates.difference(self.playables)) and len(candidates)

    def is_playable_card(self, card: Card) -> bool:
        return (card.suit_index, card.rank) in self.playables

    def is_trash(self, candidates: Set[CardTuple]) -> bool:
        return not len(candidates.difference(self.trash)) and len(candidates)

    def is_trash_card(self, card: Card) -> bool:
        return (card.suit_index, card.rank) in self.trash

    def is_critical(self, candidates: Set[CardTuple]) -> bool:
        return not len(candidates.difference(self.criticals)) and len(candidates)

    def is_critical_card(self, card: Card) -> bool:
        return (card.suit_index, card.rank) in self.criticals

    def is_clued(self, order) -> bool:
        return self.order_to_rich_card[order].is_clued

    def set_variant_name(self, variant_name: str, num_players: int):
        self.variant_name = variant_name
        self.stacks = []
        for suit in SUITS[self.variant_name]:
            if "Reversed" in suit:
                self.stacks.append(6)
            else:
                self.stacks.append(0)

    def get_clued_cards(self, type_: Optional[TextInt] = None, player_index: Optional[int] = None) -> List[RichCard]:
        if player_index is None:
            player_indices = [i for i in range(self.num_players)]
        else:
            player_indices = [player_index]

        if type_ == RANK_CLUE:
            return [c for pi in player_indices for c in self.hands[pi].rich_cards if c.is_rank_clued]
        elif type_ == COLOR_CLUE:
            return [c for pi in player_indices for c in self.hands[pi].rich_cards if c.is_color_clued]
        else:
            return [c for pi in player_indices for c in self.hands[pi].rich_cards if c.is_clued]

    def get_cards_seen_from(self, player_index: int) -> Counter[CardTuple]:
        cards_seen_from_pov = self.get_all_played_or_discarded()
        for i in range(self.num_players):
            if i == self.our_player_index or i == player_index:
                continue
            for rich_card in self.hands[i]:
                cards_seen_from_pov[rich_card.to_tuple()] += 1
        return cards_seen_from_pov

    def get_all_played_or_discarded(self) -> Counter[CardTuple]:
        return self.discards + Counter([
            (suit_index, rank) for suit_index in range(len(SUITS[self.variant_name]))
            for rank in range(1, 6)
            if variants.has_already_been_played(self.variant_name, self.stacks, suit_index, rank)
        ])

    def self_elim(self) -> List[LockedIdentity]:
        cards_seen = self.get_cards_seen_from(self.our_player_index)
        return get_locked_identities(self.our_hand.get_empathies(), cards_seen)

    def self_elim_filtration(self) -> List[LockedIdentity]:
        # TODO
        return get_locked_identities(self.our_hand.get_filtrations(), {})

    def cross_elim(self, addl_seen_from_self: Counter[CardTuple]):
        for player_index in range(self.num_players):
            if player_index == self.our_player_index:
                continue
            cards_seen = self.get_cards_seen_from(player_index) + addl_seen_from_self
            get_locked_identities(self.hands[player_index].get_empathies(), cards_seen)

    def cross_filtration_elim(self, addl_seen_from_self: Counter[CardTuple]):
        # TODO
        return

    def process_visible_cards(self):
        addl_seen_from_self: Counter[CardTuple] = Counter()
        locked_identities = self.self_elim()
        for li in locked_identities:
            addl_seen_from_self |= li.counts

        self.cross_elim(addl_seen_from_self)

    def __str__(self):
        our_player_name = self.player_names[self.our_player_index]
        current_player = self.player_names[self.current_player_index]
        output = f"\nVariant: {self.variant_name}, POV: {our_player_name}\n"
        output += f"Turn: {self.turn + 1}, currently on {current_player}\n"
        output += (
            f"Clues: {self.clue_tokens}, Bombs: {self.bombs}, "
            f"Pace: {self.pace}, Cards: {self.num_cards_in_deck}\n"
        )
        output += (
            "Stacks: "
            + ", ".join(
                [
                    suit_name + " " + str(self.stacks[i])
                    for i, suit_name in enumerate(SUITS[self.variant_name])
                ]
            )
        )
        for i, name in enumerate(self.player_names):
            output += f"\nNotes {name}: " + ", ".join(
                [
                    "'" + self.notes.get(rich_card.card.order, "") + "'"
                    for rich_card in reversed(self.hands[i].rich_cards)
                ]
            )

        output += "\n\n"

        discard_str_rows = [
            "".join(["." if (suit_index, rank) not in self.discards else str(self.discards[(suit_index, rank)])
                     for suit_index in range(len(SUITS[self.variant_name]))]) for rank in range(1, 6)]
        discard_str_rows.append(" " *len(SUITS[self.variant_name]))
        discard_str = "\n".join([x + "  " for x in discard_str_rows])
        output += horizontal_concat([discard_str] + [str(hand) for hand in self.hands])
        return output

    def remove_card_from_hand(self, player_index: int, order: int) -> Card:
        hand = self.hands[player_index]
        rich_card = hand.remove(order)
        return rich_card.card

    def handle_draw(self, player_index: int, order: int, suit_index: int, rank: int) -> Card:
        new_card = Card(order=order, suit_index=suit_index, rank=rank)
        rich_card = self.hands[player_index].draw(new_card)
        self.order_to_rich_card[rich_card.card.order] = rich_card
        self.process_visible_cards()
        return new_card

    def handle_play(self, player_index: int, order: int, suit_index: int, rank: int):
        self.remove_card_from_hand(player_index, order)
        self.stacks[suit_index] = rank
        self.process_visible_cards()
        return Card(order, suit_index, rank)

    def handle_discard(self, player_index: int, order: int, suit_index: int, rank: int):
        self.remove_card_from_hand(player_index, order)
        if (suit_index, rank) not in self.discards:
            self.discards[(suit_index, rank)] = 0
        self.discards[(suit_index, rank)] += 1
        self.process_visible_cards()
        return Card(order, suit_index, rank)
    
    def handle_strike(self, order: int):
        pass

    def super_handle_clue(
        self,
        clue_giver: int,
        target_index: int,
        clue_type: int,
        clue_value: int,
        card_orders,
    ):
        return self.handle_clue(
            clue_giver, target_index, clue_type, clue_value, card_orders
        )

    def process_pos_neg_clues(
        self, target_index: int, clue_type: TextInt, clue_value: int, card_orders
    ) -> List[RichCard]:
        all_cards_touched_by_clue = get_all_touched_cards(
            clue_type, clue_value, self.variant_name
        )
        all_cards_not_touched_by_clue = variants.get_all_cards(self.variant_name).difference(all_cards_touched_by_clue)
        touched_cards = []

        for _, rich_card in enumerate(self.hands[target_index].rich_cards):
            if rich_card.card.order in card_orders:
                rich_card.handle_clue(clue_type, clue_value, touched=True)
                if not len(rich_card.empathy.candidates):
                    self.write_note(card.order, note="Positive clue conflict!")
                    rich_card.empathy.set_empathy(all_cards_touched_by_clue, reset_inferences=True)
            else:
                rich_card.handle_clue(clue_type, clue_value, touched=False)

                if not len(rich_card.empathy.candidates):
                    self.write_note(card.order, note="Negative clue conflict!")
                    rich_card.empathy.set_empathy(all_cards_not_touched_by_clue, reset_inferences=True)

        self.process_visible_cards()
        return touched_cards

    def handle_clue(
        self,
        clue_giver: int,
        target_index: int,
        clue_type: TextInt,
        clue_value: int,
        card_orders,
    ):
        touched_cards = self.process_pos_neg_clues(
            target_index, clue_type, clue_value, card_orders
        )
        return touched_cards

    def write_note(self, order: int, note: str, candidates=None, append=True):
        _note = "t" + str(self.turn + 1) + ": "
        if candidates is not None:
            suit_names = SUITS[self.variant_name]
            if not self.is_trash(candidates):
                _note += (
                    "["
                    + ",".join(
                        [
                            suit_names[suit_index] + " " + str(rank)
                            for (suit_index, rank) in candidates
                        ]
                    )
                    + "]"
                )
            else:
                _note += "[trash]"
        _note += note

        if order not in self.notes:
            self.notes[order] = _note
            return

        if append:
            self.notes[order] += " | " + _note
        else:
            self.notes[order] = _note


if __name__ == "__main__":
    import numpy as np
    from conventions.reactor import ReactorGameState

    np.random.seed(19991)
    variant_name = "No Variant"
    player_names = ["test0", "test1", "test2"]
    states = {
        player_index: ReactorGameState(variant_name, player_names, player_index)
        for player_index, player_name in enumerate(player_names)
    }
    deck = get_random_deck(variant_name)
    num_cards_per_player = {2: 5, 3: 5, 4: 4, 5: 4, 6: 3}[len(states)]
    order = 0

    for player_index, player_name in enumerate(states):
        for i in range(num_cards_per_player):
            card = deck.pop(0)
            for player_iterate in states:
                if player_iterate == player_name:
                    states[player_iterate].handle_draw(player_index, order, -1, -1)
                else:
                    states[player_iterate].handle_draw(
                        player_index, order, card.suit_index, card.rank
                    )
            order += 1

    self = states[0]
    self.print()
    print(self.get_reactive_clues())
    states[1].handle_clue(0, 2, RANK_CLUE, 2, [11, 13])
    states[2].handle_clue(0, 2, RANK_CLUE, 2, [11, 13])
    print(1, states[1].unresolved_reactions, states[1].play_orders)
    print(2, states[2].unresolved_reactions, states[2].play_orders)

    states[1].handle_play(1, 9, 0, 1)
    states[2].handle_play(1, 9, 0, 1)
    states[2].print()
    print(1, states[1].unresolved_reactions, states[1].play_orders)
    print(2, states[2].unresolved_reactions, states[2].play_orders)
