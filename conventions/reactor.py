from game_state import (
    GameState, RANK_CLUE, COLOR_CLUE, Card,
    get_available_color_clues, get_available_rank_clues
)
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from copy import deepcopy
from enum import Enum


class ReactorGameState(GameState):
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
    def all_discard_orders(self) -> List[int]:
        return [x for discard_orders in self.discard_orders.values() for x in discard_orders]

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
    
    def has_safe_play(self, player_index: int) -> bool:
        return len(self.play_orders[player_index]) > 0
    
    def has_safe_discard(self, player_index: int) -> bool:
        return len(self.discard_orders[player_index]) > 0
    
    def get_reactive_player_index_ordering(self) -> List[int]:
        """This can be empty if everyone has safe plays."""
        ben = None
        for i in range(len(self.num_players) - 1):
            player_index = (self.our_player_index + 1 + i) % self.num_players
            if not self.has_safe_play(player_index):
                ben = player_index

        if ben is None:
            return []
        
        ordering = [ben]
        _player_index = ben
        for i in range(len(self.num_players) - 1):
            _player_index = (_player_index + 1) % self.num_players
            if _player_index != self.our_player_index:
                ordering.append(_player_index)
        return ordering
    
    def get_leftmost_non_obvious_playable_human_slot(self, player_index: int) -> Optional[int]:
        """Human slot means newest = 1, instead of oldest = 0"""
        target_hand = self.hands[player_index]
        leftmost_play = None
        for i, card in enumerate(target_hand):
            if card.order in self.all_play_orders:
                continue
            
            # TODO: this is a bug that will need to be fixed eventually, but need to use filtration instead of candidates
            if self.is_playable(self.all_candidates_list[player_index][i]):
                continue

            # TODO: if an unclued playable card is also clued in the same hand, the clued copy takes priority
            
            leftmost_play = len(target_hand) - i
        return leftmost_play

    def get_trash_target_human_slot(self, player_index: int) -> Optional[int]:
        """Human slot means newest = 1, instead of oldest = 0"""
        target_hand = self.hands[player_index]
        leftmost_trash = None
        for i, card in enumerate(target_hand):
            if card.order in self.all_discard_orders:
                continue

    def every_good_card_of_rank_is_playable(self, rank: int) -> bool:
        touched_card_tuples = self.get_touched_card_tuples(RANK_CLUE, rank)
        at_least_one_card_playable = False
        for (si, r) in touched_card_tuples:
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
        touched_card_tuples = self.get_touched_card_tuples(clue_type, clue_value)
        cands = self.all_candidates_list[player_index][i]
        card = self.hands[player_index][i]
        if card.to_tuple() in touched_card_tuples:
            cands_after_clue = cands.intersection(touched_card_tuples)
        else:
            cands_after_clue = cands.difference(touched_card_tuples)
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
        touched_card_tuples = self.get_touched_card_tuples(clue_type, clue_value)
        good_card_indices = [
            i
            for i in range(len(self.hands[target_index]))
            if not self.is_trash_card(self.hands[target_index][i])
        ]
        bad_cards_touched = [
            card for card in self.hands[target_index]
            if self.is_trash_card(card) and card.to_tuple() in touched_card_tuples
        ]
        if len(bad_cards_touched):
            score = 1000
        else:
            score = 1
        
        candidates_list = self.all_candidates_list[target_index]

        for i in good_card_indices:
            if self.hands[target_index][i].to_tuple() in touched_card_tuples:
                new_candidates = candidates_list[i].intersection(touched_card_tuples)
            else:
                new_candidates = candidates_list[i].difference(touched_card_tuples)
            score *= len(new_candidates)

        return score

    def get_index_of_ref_discard_target(
        self,
        target_index: int,
        clue_type: int,
        clue_value: int,
        touched_orders: Optional[List[int]] = None
    ) -> Optional[int]:
        """A return value of None signifies a lock"""
        touched_card_tuples = self.get_touched_card_tuples(clue_type, clue_value)
        if touched_orders is not None:
            _touched_orders = touched_orders
        else:
            _touched_orders = [
                card.order for card in self.hands[target_index]
                if card.to_tuple() in touched_card_tuples
            ]

        num_cards_in_hand = len(self.hands[target_index])
        unclued_orders = [card.order for card in self.hands[target_index] if card.order in self.clued_card_orders]
        if not len(unclued_orders):
            raise IndentationError("Cannot call get_index_of_ref_discard_target when hand is fully clued!")
        
        rightmost_unclued_order = min(unclued_orders)
        if rightmost_unclued_order in _touched_orders:
            return None

        # find the leftmost card to the right of a newly touched card
        newly_touched_indices = [
            i for i, card in enumerate(self.hands[target_index])
            if card.order in _touched_orders and card.order not in self.clued_card_orders
        ]

        if not len(newly_touched_indices):
            raise IndentationError(
                f"Invalid Ref Discard clue, no new cards are clued: {target_index} {clue_type} {clue_value}"
            )
        leftmost_newly_touched_index = max(newly_touched_indices)

        for j in range(num_cards_in_hand):
            i = num_cards_in_hand - j - 1
            if i > leftmost_newly_touched_index:
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
        touched_card_tuples = self.get_touched_card_tuples(clue_type, clue_value)
        if touched_orders is not None:
            _touched_orders = touched_orders
        else:
            _touched_orders = [
                card.order for card in self.hands[target_index]
                if card.to_tuple() in touched_card_tuples
            ]

        num_cards_in_hand = len(self.hands[target_index])
        leftmost_newly_touched = None
        for i, card in enumerate(self.hands[target_index]):
            if card.order in _touched_orders and card.order not in self.clued_card_orders:
                leftmost_newly_touched = i
            
        if leftmost_newly_touched is None:
            raise IndentationError(
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

    def get_stable_clues(self) -> Dict[Tuple[int, int, int], str]:
        # (clue_value, clue_type, target_index) -> clue_type
        result = {}
        ordering = self.get_reactive_player_index_ordering()

        for target_index in range(self.num_players):
            if len(ordering) > 0 and target_index != ordering[0]:
                continue
            
            target_hand = self.hands[target_index]
            for clue_type in [RANK_CLUE, COLOR_CLUE]:
                if clue_type == RANK_CLUE:
                    all_clue_values = get_available_rank_clues(self.variant_name)
                else:
                    color_clues = get_available_color_clues(self.variant_name)
                    all_clue_values = list(range(len(color_clues)))

                for clue_value in all_clue_values:
                    touched_card_tuples = self.get_touched_card_tuples(clue_type, clue_value)
                    touched_cards = self.get_touched_cards(clue_type, clue_value, target_index)
                    if not len(touched_cards):
                        continue
                    
                    # oldest to newest
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
                        new_cands = candidates.intersection(touched_card_tuples)
                        
                        if self.is_playable(new_cands) or self.is_trash(new_cands):
                            reveals_safe_action = True

                    if reveals_safe_action:
                        result[(clue_type, clue_value, target_index)] = "SAFE_ACTION"
                    elif len(newly_touched_cards):
                        if clue_type == RANK_CLUE:
                            if self.every_good_card_of_rank_is_playable(clue_value) and not self.is_weak_trash_card(newly_touched_cards[-1]):
                                result[(clue_type, clue_value, target_index)] = "DIRECT_PLAY"
                            elif self.every_card_of_rank_is_trash(clue_value):
                                ref_play_index = self.get_index_of_ref_play_target(target_index, clue_type, clue_value)
                                targeted_card = target_hand[ref_play_index]
                                if self.is_playable_card(targeted_card) and targeted_card.to_tuple() not in self.all_play_tuples:
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

    def get_reactive_clues(self) -> Dict[Tuple[int, int, int], str]:
        # (clue_value, clue_type, target_index) -> clue_type
        if self.num_players > 3:
            raise NotImplementedError
        result = {}
        ordering = self.get_reactive_player_index_ordering()

        # TODO: response inversion
        if not len(ordering):
            return {}
        
        for target_index in [ordering[1]]:
            if len(ordering) > 0 and target_index != ordering[0]:
                continue
            
            target_hand = self.hands[target_index]
            for clue_type in [RANK_CLUE, COLOR_CLUE]:
                if clue_type == RANK_CLUE:
                    all_clue_values = get_available_rank_clues(self.variant_name)
                else:
                    color_clues = get_available_color_clues(self.variant_name)
                    all_clue_values = list(range(len(color_clues)))

                for clue_value in all_clue_values:
                    slots_touched = self.get_touched_slots(clue_type, clue_value, target_index)
                    if not len(slots_touched):
                        continue
                    
                    # bot -> human slot ordering: [0, 1, 2, 3, 4] -> [5, 4, 3, 2, 1]
                    slots_touched = [len(target_hand) - x for x in slots_touched]
                    focused_slot = (
                        slots_touched[1] if (slots_touched[0] == 1 and len(slots_touched) > 1)
                        else slots_touched[0]
                    )


