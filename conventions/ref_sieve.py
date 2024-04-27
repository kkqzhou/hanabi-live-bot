from game_state import (
    GameState, get_all_touched_cards, RANK_CLUE, COLOR_CLUE, Card,
    get_available_color_clues, get_available_rank_clues
)
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from copy import deepcopy
from enum import Enum

# WIPWIPWIP

class BadRefSieveClue(Exception):
    pass


class RefSieveGameState(GameState):
    def __init__(self, variant_name, player_names, our_player_index):
        super().__init__(variant_name, player_names, our_player_index)
        self.discard_orders: Dict[int, List[int]] = {
            i: []
            for i in range(self.num_players)
        }
        self.play_orders: Dict[int, List[int]] = {
            i: []
            for i in range(self.num_players)
        }
        self.ctd_order: Dict[int, Optional[int]] = {
            i: None
            for i in range(self.num_players)
        }

    @property
    def next_player_index(self) -> int:
        return (self.our_player_index + 1) % self.num_players
    
    @property
    def all_play_orders(self) -> List[int]:
        return [x for play_orders in self.play_orders.values() for x in play_orders]
    
    @property
    def all_play_tuples(self) -> Set[Tuple[int, int]]:
        play_tuples = {self.get_card(order).to_tuple() for order in self.all_play_orders}
        return {x for x in play_tuples if x[-1] > 0}

    @property
    def our_play_orders(self) -> List[int]:
        return self.play_orders[self.our_player_index]
    
    @property
    def our_discard_orders(self) -> List[int]:
        return self.discard_orders[self.our_player_index]

    @property
    def clued_card_orders(self) -> Set[int]:
        clued = set(self.rank_clued_card_orders).union(set(self.color_clued_card_orders))
        clued = clued.union(set(self.all_play_orders))
        in_someones_hand = {card.order for hand in self.hands.values() for card in hand}
        return clued.intersection(in_someones_hand)
    
    @property
    def weak_trash(self) -> Set[Tuple[int, int]]:
        result = self.trash
        for order in self.clued_card_orders:
            card = self.get_card(order)
            tup = card.to_tuple()
            if tup[-1] > 0:
                result.add(tup)
        return result
    
    def is_weak_trash(self, candidates: Set[Tuple[int, int]]) -> bool:
        return not len(candidates.difference(self.weak_trash)) and len(candidates)
    
    def is_weak_trash_card(self, card: Card) -> bool:
        return card.to_tuple() in self.weak_trash

    def every_good_card_of_rank_is_playable(self, rank: int) -> bool:
        all_touched_cards = get_all_touched_cards(RANK_CLUE, rank, self.variant_name)
        at_least_one_card_playable = False
        for (si, r) in all_touched_cards:
            if r != rank:
                continue
            if (si, r) not in self.playables and (si, r) not in self.trash:
                return False
            if (si, r) in self.playables:
                at_least_one_card_playable = True
        return at_least_one_card_playable
    
    def every_card_of_rank_is_trash(self, rank: int) -> bool:
        return all([x >= rank for x in self.stacks])
    
    def is_known_trash_after_clue(self, order: int, clue_type: int, clue_value: int) -> bool:
        player_index, i = self.order_to_index[order]
        if player_index == self.our_player_index:
            return False
        all_touched_cards = get_all_touched_cards(clue_type, clue_value, self.variant_name)
        cands = self.all_candidates_list[player_index][i]
        card = self.hands[player_index][i]
        if card.to_tuple() in all_touched_cards:
            cands_after_clue = cands.intersection(all_touched_cards)
        else:
            cands_after_clue = cands.difference(all_touched_cards)
        return self.is_trash(cands_after_clue)

    def update_play_discard_orders(self):
        for player_index in range(self.num_players):
            candidates_list = self.all_candidates_list[player_index]
            for i, candidates in enumerate(candidates_list):
                card = self.hands[player_index][i]
                if self.is_playable(candidates) and card.order not in self.play_orders[player_index]:
                    self.play_orders[player_index].append(card.order)

                if self.is_trash(candidates):
                    if card.order not in self.discard_orders[player_index]:
                        self.discard_orders[player_index].append(card.order)
                    self.play_orders[player_index] = [
                        x for x in self.play_orders[player_index] if x != card.order
                    ]

                # assume good touch to some extent
                if not len(candidates.difference(self.playables.union(self.trash))) and not self.is_trash(candidates) and card.order in self.clued_card_orders:
                    if card.order not in self.play_orders[player_index]:
                        self.play_orders[player_index].append(card.order)

    def handle_clue(
        self,
        clue_giver: int,
        target_index: int,
        clue_type: int,
        clue_value: int,
        card_orders,
    ):
        newly_touched_card_orders = [order for order in card_orders if order not in self.clued_card_orders]
        ref_action_index = None
        ref_action_type = None

        if len(newly_touched_card_orders):
            if clue_type == RANK_CLUE:
                if self.every_good_card_of_rank_is_playable(clue_value):
                    for order in newly_touched_card_orders:
                        if order not in self.play_orders[target_index]:
                            self.play_orders[target_index].append(order)
                elif self.every_card_of_rank_is_trash(clue_value):
                    ref_action_index = self.get_index_of_ref_play_target(
                        target_index, clue_type, clue_value, touched_orders=card_orders
                    )
                    ref_action_type = "play"
                else:
                    ref_action_index = self.get_index_of_ref_discard_target(
                        target_index, clue_type, clue_value, touched_orders=card_orders
                    )
                    ref_action_type = "discard"
            else:
                ref_action_index = self.get_index_of_ref_play_target(
                    target_index, clue_type, clue_value, touched_orders=card_orders
                )
                ref_action_type = "play"

        old_clued_card_orders = deepcopy(self.clued_card_orders)
        result = super().handle_clue(
            clue_giver, target_index, clue_type, clue_value, card_orders
        )

        candidates_list = self.all_candidates_list[target_index]
        safe_action_revealed = False
        for i, candidates in enumerate(candidates_list):
            card = self.hands[target_index][i]
            if card.order in self.all_play_orders:
                continue

            if card.order not in old_clued_card_orders:
                continue

            if card.order not in card_orders:
                continue

            if self.is_playable(candidates) or self.is_trash(candidates):
                safe_action_revealed = True

        self.update_play_discard_orders()
        
        if not len(newly_touched_card_orders):
            print('@@@@@@ no newly touched cards', newly_touched_card_orders, self.clued_card_orders)
            return result
        
        if safe_action_revealed:
            print('@@@@@@ safe action revealed')
            return result
        
        if ref_action_index is not None:
            if ref_action_type == "discard":
                ctd = self.hands[target_index][ref_action_index]
                self.ctd_order[target_index] = ctd.order
            elif ref_action_type == "play":
                playable = self.hands[target_index][ref_action_index]
                self.play_orders[target_index].append(playable.order)
            else:
                raise ValueError(ref_action_type)
            
        return result
    
    def handle_play(self, player_index, order, suit_index, rank):
        result = super().handle_play(player_index, order, suit_index, rank)
        self.play_orders[player_index] = [
            x for x in self.play_orders[player_index] if x != order
        ]
        self.discard_orders[player_index] = [
            x for x in self.discard_orders[player_index] if x != order
        ]
        self.ctd_order[player_index] = None
        self.update_play_discard_orders()
        return result
    
    def handle_discard(self, player_index, order, suit_index, rank):
        result = super().handle_discard(player_index, order, suit_index, rank)
        self.discard_orders[player_index] = [
            x for x in self.discard_orders[player_index] if x != order
        ]
        self.play_orders[player_index] = [
            x for x in self.play_orders[player_index] if x != order
        ]
        self.ctd_order[player_index] = None
        self.update_play_discard_orders()
        return result
    
    def get_chop_order(self, player_index: int) -> Optional[int]:
        if self.ctd_order[player_index] is not None:
            return self.ctd_order[player_index]

        for j in range(len(self.hands[player_index])):
            card = self.hands[player_index][-j-1]
            if card.order not in self.clued_card_orders:
                return card.order
        
        return None
    
    def evaluate_clue_score(self, clue_type, clue_value, target_index) -> int:
        all_cards_touched_by_clue = get_all_touched_cards(
            clue_type, clue_value, self.variant_name
        )
        good_card_indices = [
            i
            for i in range(len(self.hands[target_index]))
            if not self.is_trash_card(self.hands[target_index][i])
        ]
        bad_cards_touched = [
            card for card in self.hands[target_index]
            if self.is_trash_card(card) and card.to_tuple() in all_cards_touched_by_clue
        ]
        if len(bad_cards_touched):
            score = 1000
        else:
            score = 1
        
        candidates_list = self.all_candidates_list[target_index]

        for i in good_card_indices:
            if self.hands[target_index][i].to_tuple() in all_cards_touched_by_clue:
                new_candidates = candidates_list[i].intersection(
                    all_cards_touched_by_clue
                )
            else:
                new_candidates = candidates_list[i].difference(
                    all_cards_touched_by_clue
                )
            score *= len(new_candidates)

        return score

    def get_index_of_ref_discard_target(
        self,
        target_index: int,
        clue_type: int,
        clue_value: int,
        touched_orders: Optional[List[int]] = None
    ) -> Optional[int]:
        all_touched_cards = get_all_touched_cards(clue_type, clue_value, self.variant_name)
        if touched_orders is not None:
            _touched_orders = touched_orders
        else:
            _touched_orders = [
                card.order for card in self.hands[target_index]
                if card.to_tuple() in all_touched_cards
            ]

        num_cards_in_hand = len(self.hands[target_index])
        leftmost_newly_touched = None

        for i, card in enumerate(self.hands[target_index]):
            if card.order in _touched_orders and card.order not in self.clued_card_orders:
                leftmost_newly_touched = i
            
        if leftmost_newly_touched is None:
            raise BadRefSieveClue(
                f"Invalid Ref Discard clue: {target_index} {clue_type} {clue_value}"
            )

        for j in range(num_cards_in_hand):
            i = num_cards_in_hand - j - 1
            if i > leftmost_newly_touched:
                continue

            card = self.hands[target_index][i]
            if card.order in self.clued_card_orders:
                continue

            if card.order in _touched_orders:
                continue

            return i

        return None
    
    def get_index_of_ref_play_target(
        self,
        target_index: int,
        clue_type: int,
        clue_value: int,
        touched_orders: Optional[List[int]] = None
    ) -> int:
        all_touched_cards = get_all_touched_cards(clue_type, clue_value, self.variant_name)
        if touched_orders is not None:
            _touched_orders = touched_orders
        else:
            _touched_orders = [
                card.order for card in self.hands[target_index]
                if card.to_tuple() in all_touched_cards
            ]

        num_cards_in_hand = len(self.hands[target_index])
        leftmost_newly_touched = None
        for i, card in enumerate(self.hands[target_index]):
            if card.order in _touched_orders and card.order not in self.clued_card_orders:
                leftmost_newly_touched = i
            
        if leftmost_newly_touched is None:
            raise BadRefSieveClue(
                f"Invalid Ref Play clue: {target_index} {clue_type} {clue_value}"
            )

        unclued_indices = [
            i for i in range(num_cards_in_hand)
            if self.hands[target_index][i].order not in self.clued_card_orders
        ]
        x_to_unclued_indices = dict(enumerate(unclued_indices))
        unclued_indices_to_x = {idx: x for x, idx in x_to_unclued_indices.items()}
        newly_clued_indices = [
            i for i in unclued_indices
            if self.hands[target_index][i].order in _touched_orders
        ]
        shifted_indices = [
            x_to_unclued_indices[(unclued_indices_to_x[i] + 1) % len(unclued_indices)]
            for i in newly_clued_indices
        ]
        return max(shifted_indices)

    def get_touched_cards(self, clue_type: int, clue_value: int, target_index: int) -> List[Card]:
        target_hand = self.hands[target_index]
        all_touched_cards = get_all_touched_cards(clue_type, clue_value, self.variant_name)
        touched_cards = [card for card in target_hand if card.to_tuple() in all_touched_cards]
        return touched_cards

    def get_ref_sieve_clues(self) -> Dict[Tuple[int, int, int], str]:
        # (clue_value, clue_type, target_index) -> clue_type
        result = {}
        for target_index in range(self.num_players):
            if target_index == self.our_player_index:
                continue
            
            target_hand = self.hands[target_index]
            for clue_type in [RANK_CLUE, COLOR_CLUE]:
                if clue_type == RANK_CLUE:
                    all_clue_values = get_available_rank_clues(self.variant_name)
                else:
                    color_clues = get_available_color_clues(self.variant_name)
                    all_clue_values = list(range(len(color_clues)))

                for clue_value in all_clue_values:
                    all_touched_cards = get_all_touched_cards(clue_type, clue_value, self.variant_name)
                    touched_cards = self.get_touched_cards(clue_type, clue_value, target_index)
                    if not len(touched_cards):
                        continue

                    touched_card_orders = [card.order for card in touched_cards]
                    newly_touched_cards = [card for card in touched_cards if card.order not in self.clued_card_orders]

                    reveals_safe_action = False
                    for c in target_hand:
                        if c.order in self.all_play_orders:
                            continue

                        if c.order not in self.clued_card_orders:
                            continue

                        if c.order not in touched_card_orders:
                            continue

                        candidates = self.get_candidates(c.order)
                        new_cands = candidates.intersection(all_touched_cards)
                        
                        if self.is_playable(new_cands) or self.is_trash(new_cands):
                            reveals_safe_action = True

                    if reveals_safe_action:
                        result[(clue_type, clue_value, target_index)] = "SAFE_ACTION"
                    elif len(newly_touched_cards):
                        if clue_type == RANK_CLUE:
                            nothing_is_trash = True
                            for card in newly_touched_cards:
                                if self.is_weak_trash_card(card):
                                    nothing_is_trash = False

                            if self.every_good_card_of_rank_is_playable(clue_value) and nothing_is_trash:
                                result[(clue_type, clue_value, target_index)] = "DIRECT_PLAY"
                            elif self.every_card_of_rank_is_trash(clue_value):
                                ref_play_index = self.get_index_of_ref_play_target(target_index, clue_type, clue_value)
                                playable_card = target_hand[ref_play_index]
                                if self.is_playable_card(playable_card) and playable_card.to_tuple() not in self.all_play_tuples:
                                    result[(clue_type, clue_value, target_index)] = "REF_PLAY"
                            else:
                                ref_discard_index = self.get_index_of_ref_discard_target(target_index, clue_type, clue_value)
                                if ref_discard_index is None:
                                    result[(clue_type, clue_value, target_index)] = "LOCK"
                                else:
                                    result[(clue_type, clue_value, target_index)] = "REF_DISCARD"
                        else:
                            ref_play_index = self.get_index_of_ref_play_target(target_index, clue_type, clue_value)
                            playable_card = target_hand[ref_play_index]
                            if self.is_playable_card(playable_card) and playable_card.to_tuple() not in self.all_play_tuples:
                                result[(clue_type, clue_value, target_index)] = "REF_PLAY"

        return result


if __name__ == "__main__":
    import numpy as np
    from game_state import get_random_deck

    np.random.seed(20000)
    variant_name = "Prism (5 Suits)"
    player_names = ["test0", "test1", "test2", "test3"]
    states = {
        player_index: GameState(variant_name, player_names, player_index)
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

    states[0].print()
