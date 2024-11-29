from card import Card, RichCard
from deck import get_random_deck, get_starting_pace
from hand import Hand, horizontal_concat
from constants import MAX_CLUE_NUM, COLOR_CLUE, RANK_CLUE, CardTuple, ClueTuple
from variants import SUITS, DARK_SUIT_NAMES, get_available_color_clues, get_available_rank_clues, get_all_touched_cards

import variants

from collections import Counter
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import itertools


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


def get_candidates_list_str(
    candidates_list: List[Tuple[int, int]],
    variant_name: str,
    actual_hand=None,
    poss_list=None,
):
    output = ""

    for rank in range(1, 6):
        output += "\n"
        for hand_order, candidates in enumerate(candidates_list):
            output += "  "
            for i, suit in enumerate(SUITS[variant_name]):
                if (i, rank) in candidates:
                    _char = "*"
                    if actual_hand is not None:
                        actual_card = actual_hand[hand_order]
                        if (i == actual_card.suit_index) and (rank == actual_card.rank):
                            _char = "O"
                    output += _char
                elif poss_list is not None and (i, rank) in poss_list[hand_order]:
                    output += "-"
                else:
                    output += "."

    return output


class GameState:
    def __init__(self, variant_name, player_names, our_player_index):
        self.set_variant_name(variant_name, len(player_names))
        self.player_names: List[str] = player_names
        self.our_player_index: int = our_player_index
        self.current_player_index: int = 0

        # Initialize the hands for each player (an array of cards)
        self.hands: List[Hand] = []
        for _ in range(len(player_names)):
            self.hands.append(Hand(variant_name))

        self.clue_tokens: int = MAX_CLUE_NUM
        self.bombs: int = 0
        self.rich_cards: Dict[int, RichCard] = {}
        self.marked_cards: Dict[str, Set[int]] = {
            "rank": set(),
            "color": set()
        }
        self.discards: Dict[CardTuple, int] = {}  # tracks # of discards per cardtuple
        self.turn: int = 0
        self.max_score: int = 99999
        self.notes: Dict[int, str] = {}

    @property
    def rank_clued_card_orders(self) -> Set[int]:
        return self.marked_cards["rank"]
    
    @property
    def color_clued_card_orders(self) -> Set[int]:
        return self.marked_cards["color"]
    
    @property
    def clued_card_orders(self) -> Set[int]:
        return self.rank_clued_card_orders.union(self.color_clued_card_orders)

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
    def max_num_cards(self) -> Dict[CardTuple, int]:
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
    def our_hand(self) -> List[Card]:
        return self.hands[self.our_player_index]

    @property
    def num_1s_played(self) -> int:
        return sum([x > 0 for x in self.stacks])

    def get_next_playable_card_tuple(self, suit_index: int) -> Tuple[int, int]:
        incr = (-1 if "Reversed" in SUITS[self.variant_name][suit_index] else 1)
        return (suit_index, self.stacks[suit_index] + incr)

    def get_candidates(self, order) -> Optional[Set[Tuple[int, int]]]:
        player_index, i = self.order_to_index.get(order, (None, None))
        if player_index is None:
            return None
        return self.all_candidates_list[player_index][i]

    def get_possibilities(self, order) -> Optional[Set[Tuple[int, int]]]:
        player_index, i = self.order_to_index.get(order, (None, None))
        if player_index is None:
            return None
        return self.all_possibilities_list[player_index][i]

    def get_base_filtrations(self, order) -> Optional[Set[Tuple[int, int]]]:
        player_index, i = self.order_to_index.get(order, (None, None))
        if player_index is None:
            return None
        return self.all_base_filtrations[player_index][i]

    def get_card(self, order) -> Card:
        player_index, i = self.order_to_index[order]
        return self.hands[player_index][i]
    
    # TODO: split this out into a non class function
    def is_playable(self, candidates: Set[Tuple[int, int]]) -> bool:
        return not len(candidates.difference(self.playables)) and len(candidates)

    def is_playable_card(self, card: Card) -> bool:
        return (card.suit_index, card.rank) in self.playables

    # TODO: split this out into a non class function
    def is_trash(self, candidates: Set[Tuple[int, int]]) -> bool:
        return not len(candidates.difference(self.trash)) and len(candidates)

    def is_trash_card(self, card: Card) -> bool:
        return (card.suit_index, card.rank) in self.trash

    def is_critical(self, candidates: Set[Tuple[int, int]]) -> bool:
        return not len(candidates.difference(self.criticals)) and len(candidates)

    def is_critical_card(self, card: Card) -> bool:
        return (card.suit_index, card.rank) in self.criticals

    def is_clued(self, order) -> bool:
        return (
            order in self.color_clued_card_orders
            or order in self.rank_clued_card_orders
        )

    def get_clued_orders(self, player_index: int) -> List[int]:
        """Returns orders from right to left."""
        return [
            x.order
            for x in self.hands[player_index]
            if x.order in self.color_clued_card_orders
            or x.order in self.rank_clued_card_orders
        ]

    def get_unclued_orders(self, player_index: int) -> List[int]:
        """Returns orders from right to left."""
        return [
            x.order
            for x in self.hands[player_index]
            if x.order not in self.color_clued_card_orders
            and x.order not in self.rank_clued_card_orders
        ]
    
    def get_touched_card_tuples(self, clue_type: int, clue_value: int) -> Set[Tuple[int, int]]:
        return get_all_touched_cards(clue_type, clue_value, self.variant_name)

    def get_touched_orders(self, clue_type: int, clue_value: int, target_index: int) -> List[int]:
        """Ordering is oldest to newest."""
        target_hand = self.hands[target_index]
        all_touched_cards = get_all_touched_cards(clue_type, clue_value, self.variant_name)
        return [card.order for card in target_hand if card.to_tuple() in all_touched_cards]

    def get_touched_cards(self, clue_type: int, clue_value: int, target_index: int) -> List[Card]:
        """Ordering is oldest to newest."""
        target_hand = self.hands[target_index]
        all_touched_cards = get_all_touched_cards(clue_type, clue_value, self.variant_name)
        return [card for card in target_hand if card.to_tuple() in all_touched_cards]
    
    def get_touched_slots(self, clue_type: int, clue_value: int, target_index: int) -> List[int]:
        """Index of 0 = oldest as per convention."""
        target_hand = self.hands[target_index]
        all_touched_cards = get_all_touched_cards(clue_type, clue_value, self.variant_name)
        return [i for i, card in enumerate(target_hand) if card.to_tuple() in all_touched_cards]

    def get_all_other_players_cards(
        self, player_index=None
    ) -> Dict[Tuple[int, int], int]:
        result = {}
        for pindex, hand in self.hands.items():
            if pindex in {self.our_player_index, player_index}:
                continue

            for c in hand:
                if c.to_tuple() not in result:
                    result[c.to_tuple()] = 0
                result[c.to_tuple()] += 1
        return result

    def get_all_other_players_clued_cards(
        self, player_index=None
    ) -> Set[Tuple[int, int]]:
        return {
            (c.suit_index, c.rank)
            for pindex, hand in self.hands.items()
            for c in hand
            if pindex not in {self.our_player_index, player_index}
            and (
                c.order in self.color_clued_card_orders
                or c.order in self.rank_clued_card_orders
            )
        }

    def set_variant_name(self, variant_name: str, num_players: int):
        self.variant_name = variant_name
        self.stacks = []
        for suit in SUITS[self.variant_name]:
            if "Reversed" in suit:
                self.stacks.append(6)
            else:
                self.stacks.append(0)

    def get_copies_visible(self, player_index, suit, rank) -> int:
        num = self.discards.get((suit, rank), 0)
        if self.stacks[suit] >= rank:
            num += 1

        for pindex in range(self.num_players):
            if pindex == player_index:
                continue
            for i, card in enumerate(self.hands[pindex]):
                if pindex == self.our_player_index:
                    candidates = self.our_candidates[i]
                    if len(candidates) == 1 and list(candidates)[0] == (suit, rank):
                        num += 1
                else:
                    if card.to_tuple() == (suit, rank):
                        num += 1
        return num

    def get_fully_known_card_orders(
        self, player_index: int, query_candidates=True, keyed_on_order=False
    ) -> Dict[Tuple[int, int], List[int]]:
        poss_list = (
            self.all_candidates_list[player_index]
            if query_candidates
            else self.all_possibilities_list[player_index]
        )
        orders = {}
        for i, poss in enumerate(poss_list):
            if len(poss) == 1:
                singleton = list(poss)[0]
                if keyed_on_order:
                    orders[self.hands[player_index][i].order] = singleton
                else:
                    if singleton not in orders:
                        orders[singleton] = []
                    orders[singleton].append(self.hands[player_index][i].order)
        return orders

    def get_all_fully_known_card_orders(
        self, query_candidates=True, keyed_on_order=False
    ) -> Dict[Tuple[int, int], List[int]]:
        orders = {}
        for player_index in range(self.num_players):
            poss_list = (
                self.all_candidates_list[player_index]
                if query_candidates
                else self.all_possibilities_list[player_index]
            )
            for i, poss in enumerate(poss_list):
                if len(poss) == 1:
                    singleton = list(poss)[0]
                    if keyed_on_order:
                        orders[self.hands[player_index][i].order] = singleton
                    else:
                        if singleton not in orders:
                            orders[singleton] = []
                        orders[singleton].append(self.hands[player_index][i].order)
        return orders

    def get_doubleton_orders(self, player_index: int, query_candidates=True):
        poss_list = (
            self.all_candidates_list[player_index]
            if query_candidates
            else self.all_possibilities_list[player_index]
        )
        orders = {}
        for i, poss in enumerate(poss_list):
            if len(poss) == 2:
                doubleton_tup = tuple(sorted([list(poss)[0], list(poss)[1]]))
                if doubleton_tup not in orders:
                    orders[doubleton_tup] = []
                orders[doubleton_tup].append(self.hands[player_index][i].order)
        return orders

    def get_tripleton_orders(self, player_index: int, query_candidates=True):
        poss_list = (
            self.all_candidates_list[player_index]
            if query_candidates
            else self.all_possibilities_list[player_index]
        )
        orders = {}
        possible_tripleton_candidates = set()
        for i, poss in enumerate(poss_list):
            if len(poss) in {2, 3}:
                for candidate in poss:
                    possible_tripleton_candidates.add(candidate)

        for tripleton in itertools.combinations(possible_tripleton_candidates, 3):
            orders[tripleton] = []
            for i, poss in enumerate(poss_list):
                if not len(poss.difference(set(tripleton))):
                    orders[tripleton].append(self.hands[player_index][i].order)
        return orders

    def _process_visible_cards(self, query_candidates=True):
        max_num_cards = self.max_num_cards
        for player_index in range(self.num_players):
            poss_list = (
                self.all_candidates_list[player_index]
                if query_candidates
                else self.all_possibilities_list[player_index]
            )
            fk_orders = self.get_fully_known_card_orders(player_index, query_candidates)
            for i, poss in enumerate(poss_list):
                this_order = self.hands[player_index][i].order
                removed_cards = set()
                for suit, rank in poss:
                    copies_visible = self.get_copies_visible(player_index, suit, rank)
                    # copies visible is only for other players' hands and discard pile
                    # also incorporate information from my own hand
                    for (fk_si, fk_rank), orders in fk_orders.items():
                        for order in orders:
                            if order != this_order and (fk_si, fk_rank) == (suit, rank):
                                copies_visible += 1

                    if max_num_cards[(suit, rank)] == copies_visible:
                        removed_cards.add((suit, rank))

                poss_list[i] = poss_list[i].difference(removed_cards)

    def _process_doubletons(self, query_candidates=True):
        maxcds = self.max_num_cards
        for player_index in range(self.num_players):
            poss_list = (
                self.all_candidates_list[player_index]
                if query_candidates
                else self.all_possibilities_list[player_index]
            )
            doubleton_orders = self.get_doubleton_orders(player_index, query_candidates)
            for doubleton, orders in doubleton_orders.items():
                if len(orders) < 2:
                    continue

                first, second = doubleton
                s1_vis = self.get_copies_visible(player_index, first[0], first[1])
                s2_vis = self.get_copies_visible(player_index, second[0], second[1])
                if len(orders) < maxcds[first] + maxcds[second] - s1_vis - s2_vis:
                    continue

                for i, _ in enumerate(poss_list):
                    if self.hands[player_index][i].order not in orders:
                        poss_list[i] = poss_list[i].difference({first, second})

    def _process_tripletons(self, query_candidates=True):
        maxcds = self.max_num_cards
        for player_index in range(self.num_players):
            poss_list = (
                self.all_candidates_list[player_index]
                if query_candidates
                else self.all_possibilities_list[player_index]
            )
            tripleton_orders = self.get_tripleton_orders(player_index, query_candidates)
            for tripleton, orders in tripleton_orders.items():
                if len(orders) < 3:
                    continue

                first, second, third = tripleton
                s1_vis = self.get_copies_visible(player_index, first[0], first[1])
                s2_vis = self.get_copies_visible(player_index, second[0], second[1])
                s3_vis = self.get_copies_visible(player_index, third[0], third[1])
                _1sts, _2nds, _3rds = maxcds[first], maxcds[second], maxcds[third]
                if len(orders) < _1sts + _2nds + _3rds - s1_vis - s2_vis - s3_vis:
                    continue

                for i, _ in enumerate(poss_list):
                    if self.hands[player_index][i].order not in orders:
                        poss_list[i] = poss_list[i].difference({first, second, third})

    def process_visible_cards(self):
        for _ in range(3):
            self._process_visible_cards(True)
            self._process_doubletons(True)
            self._process_tripletons(True)
            self._process_visible_cards(False)
            self._process_doubletons(False)
            self._process_tripletons(False)

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
                    "'" + self.notes.get(card.order, "") + "'"
                    for card in reversed(self.hands[i])
                ]
            )

        output += "\n\n"
        output += str(self.discards) # TODO
        output += "\n"
        output += horizontal_concat([str(hand) for hand in self.hands])
        return output

    def remove_card_from_hand(self, player_index: int, order: int) -> Card:
        hand = self.hands[player_index]
        rich_card = hand.remove(order)
        return rich_card.card

    def handle_draw(self, player_index: int, order: int, suit_index: int, rank: int) -> Card:
        new_card = Card(order=order, suit_index=suit_index, rank=rank)
        self.hands[player_index].draw(new_card)
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
        self, target_index: int, clue_type: int, clue_value: int, card_orders
    ):
        all_cards_touched_by_clue = get_all_touched_cards(
            clue_type, clue_value, self.variant_name
        )
        touched_cards = []
        candidates_list = self.all_candidates_list[target_index]
        poss_list = self.all_possibilities_list[target_index]
        base_filt_list = self.all_base_filtrations[target_index]

        for i, card in enumerate(self.hands[target_index]):
            if card.order in card_orders:
                touched_cards.append(card)
                new_candidates = candidates_list[i].intersection(
                    all_cards_touched_by_clue
                )
                new_possibilities = poss_list[i].intersection(all_cards_touched_by_clue)
                new_base_filt = base_filt_list[i].intersection(
                    all_cards_touched_by_clue
                )
                poss_list[i] = new_possibilities
                base_filt_list[i] = new_base_filt
                assert len(new_possibilities) and len(new_base_filt)
                if not len(new_candidates):
                    self.write_note(card.order, note="Positive clue conflict!")
                    candidates_list[i] = new_possibilities
                else:
                    candidates_list[i] = new_candidates
            else:
                new_candidates = candidates_list[i].difference(
                    all_cards_touched_by_clue
                )
                new_possibilities = poss_list[i].difference(all_cards_touched_by_clue)
                new_base_filt = base_filt_list[i].difference(all_cards_touched_by_clue)
                poss_list[i] = new_possibilities
                base_filt_list[i] = new_base_filt
                assert len(new_possibilities) and len(new_base_filt)
                if not len(new_candidates):
                    self.write_note(card.order, note="Negative clue conflict!")
                    candidates_list[i] = new_possibilities
                else:
                    candidates_list[i] = new_candidates
        self.process_visible_cards()
        return touched_cards

    def track_clued_cards(self, clue_type: int, clue_value: int, card_orders):
        for order in card_orders:
            if clue_type == RANK_CLUE:
                if order not in self.rank_clued_card_orders:
                    self.rank_clued_card_orders[order] = []
                self.rank_clued_card_orders[order].append(clue_value)
            elif clue_type == COLOR_CLUE:
                if order not in self.color_clued_card_orders:
                    self.color_clued_card_orders[order] = []
                self.color_clued_card_orders[order].append(clue_value)

    def handle_clue(
        self,
        clue_giver: int,
        target_index: int,
        clue_type: int,
        clue_value: int,
        card_orders,
    ):
        touched_cards = self.process_pos_neg_clues(
            target_index, clue_type, clue_value, card_orders
        )
        self.track_clued_cards(clue_type, clue_value, card_orders)
        return touched_cards

    def get_cards_touched_dict(
        self, target_index: int, clue_type_values: Tuple[int, int]
    ) -> Dict[Tuple[int, int, int], Set[Tuple[int, int]]]:
        target_hand = self.hands[target_index]
        return get_cards_touched_dict(
            self.variant_name, target_hand, target_index, clue_type_values
        )

    def get_good_actions(self, player_index: int) -> Dict[str, List[int]]:
        raise NotImplementedError

    def get_legal_clues(self) -> Dict[Tuple[int, int, int], Set[Tuple[int, int]]]:
        # (clue_value, clue_type, target_index) -> cards_touched
        raise NotImplementedError

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
