from game_state import (
    GameState, RANK_CLUE, COLOR_CLUE, Card,
    get_available_color_clues, get_available_rank_clues
)
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from copy import deepcopy
from enum import Enum


def get_reactive_playable_human_slot(
    target_hand: List[Card],
    candidates_list: List[Set[Tuple[int, int]]],
    playables: Set[Tuple[int, int]],
    play_orders: List[int],
) -> Optional[int]:
    """Human slot means newest = 1, instead of oldest = 0"""
    leftmost_play = None
    for i, card in enumerate(target_hand):
        if card.order in play_orders:
            continue
        
        candidates = candidates_list[i]
        # TODO: this is a bug that will need to be fixed eventually, but need to use filtration instead of candidates
        if not len(candidates.difference(playables)) and len(candidates):
            continue

        # TODO: if an unclued playable card is also clued in the same hand, the clued copy takes priority
        if card.to_tuple() in playables:
            leftmost_play = len(target_hand) - i
    return leftmost_play


def get_reactive_trash_human_slot(
    target_hand: List[Card],
    candidates_list: List[Set[Tuple[int, int]]],
    trash: Set[Tuple[int, int]],
    clued_orders: List[int],
    discard_orders: List[int],
) -> Optional[int]:
    """Human slot means newest = 1, instead of oldest = 0"""
    leftmost_trash = None
    for i, card in enumerate(target_hand):
        # first iterate over clued cards
        if card.order not in clued_orders:
            continue
        
        candidates = candidates_list[i]
        # TODO: this is a bug that will need to be fixed eventually, but need to use filtration instead of candidates
        if not len(candidates.difference(trash)) and len(candidates):
            continue
        
        if card.to_tuple() in trash:
            leftmost_trash = len(target_hand) - i

    if leftmost_trash is not None:
        return leftmost_trash

    for i, card in enumerate(target_hand):
        # then iterate over unclued cards
        if card.order in clued_orders or card.order in discard_orders:
            continue
        
        candidates = candidates_list[i]
        # TODO: this is a bug that will need to be fixed eventually, but need to use filtration instead of candidates
        if not len(candidates.difference(trash)) and len(candidates):
            continue

        if card.to_tuple() in trash:
            leftmost_trash = len(target_hand) - i

    return leftmost_trash


class UnresolvedReaction:
    def __init__(
        self,
        target_index: int,
        play_parity: int,
        focused_slot: int,
        ordering: List[int],
        player_slot_orders: Dict[int, List[int]],
        current_play_orders: List[int],
        current_clued_orders: Set[int],
        current_discard_orders: Set[int],
        all_candidates_list: Dict[int, List[Set[Tuple[int, int]]]],
        target_hand: List[Card],
        playables: List[Tuple[int, int]],
        trash: List[Tuple[int, int]]
    ):
        assert len(ordering) >= 2
        self.target_index = target_index
        self.play_parity = play_parity
        self.focused_slot = focused_slot
        self.ordering = ordering
        self.player_slot_orders = player_slot_orders
        self.current_play_orders = current_play_orders
        self.current_clued_orders = current_clued_orders
        self.current_discard_orders = current_discard_orders
        self.all_candidates_list = all_candidates_list
        self.target_hand = target_hand
        self.playables = playables
        self.trash = trash

    def __str__(self) -> str:
        return f"[{self.play_parity} {self.focused_slot} {self.ordering} {self.player_slot_orders}]"

    def __repr__(self) -> str:
        return self.__str__()
    
    def is_playable(self, candidates: Set[Tuple[int, int]]) -> bool:
        return not len(candidates.difference(self.playables)) and len(candidates)

    def is_playable_card(self, card: Card) -> bool:
        return (card.suit_index, card.rank) in self.playables
    
    def get_reactive_playable_human_slot(self):
        return get_reactive_playable_human_slot(self.target_hand, self.all_candidates_list[self.target_index], self.playables, self.current_play_orders)

    def get_reactive_trash_human_slot(self):
        return get_reactive_trash_human_slot(self.target_hand, self.all_candidates_list[self.target_index], self.trash, self.current_clued_orders, self.current_discard_orders)


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
        self.unresolved_reactions: Dict[int, Optional[UnresolvedReaction]] = {
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
    
    def get_reactive_player_index_ordering(self, player_index: Optional[int] = None) -> List[int]:
        """This can be empty if everyone has safe plays."""
        ben = None
        pindex = player_index if player_index is not None else self.our_player_index
        for i in range(self.num_players - 1):
            player_index = (pindex + 1 + i) % self.num_players
            if not self.has_safe_play(player_index):
                ben = player_index
                break

        if ben is None:
            return []
        
        ordering = [ben]
        _player_index = ben
        for i in range(self.num_players - 1):
            _player_index = (_player_index + 1) % self.num_players
            if _player_index != pindex:
                ordering.append(_player_index)
        return ordering

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
                    print(f'[update_play_discard_orders 1] Adding play order {card.order}')
                    self.play_orders[player_index].append(card.order)

                if self.is_trash(candidates):
                    if card.order not in self.discard_orders[player_index]:
                        print(f'[update_play_discard_orders 2] Adding discard order {card.order}')
                        self.discard_orders[player_index].append(card.order)
                    self.play_orders[player_index] = [
                        x for x in self.play_orders[player_index] if x != card.order
                    ]

    def handle_clue(
        self,
        clue_giver: int,
        target_index: int,
        clue_type: int,
        clue_value: int,
        card_orders,
    ):
        # TODO: handle locked
        ordering = self.get_reactive_player_index_ordering(clue_giver)
        if not len(ordering) or ordering[0] == target_index:
            return self.handle_stable_clue(clue_giver, target_index, clue_type, clue_value, card_orders)
        else:
            return self.handle_reactive_clue(clue_giver, target_index, clue_type, clue_value, card_orders)

    def handle_stable_clue(
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
                    for order in sorted(newly_touched_card_orders, reverse=True):
                        # newest cards get pushed into the queue first
                        if order not in self.play_orders[target_index]:
                            print(f'[handle_stable_clue 1] Adding play order {order}')
                            self.play_orders[target_index].append(order)
                elif self.every_card_of_rank_is_trash(clue_value):
                    # TODO: implement brown/null variant specific
                    ref_action_index = self.get_index_of_ref_play_target(
                        target_index, clue_type, clue_value, touched_orders=card_orders
                    )
                    ref_action_type = "play"
                else:
                    ref_action_index = self.get_index_of_ref_discard_target(
                        target_index, clue_type, clue_value, touched_orders=card_orders
                    )
                    ref_action_type = "lock" if ref_action_index is None else "discard"
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
                self.write_note(ctd.order, note="ctd")
            elif ref_action_type == "play":
                playable = self.hands[target_index][ref_action_index]
                print(f'[handle_stable_clue 2] Adding play order {playable.order}')
                self.play_orders[target_index].append(playable.order)
                self.write_note(playable.order, note=f"[f] order {len(self.play_orders[target_index])}")
        
        if ref_action_type == "lock":
            # TODO: implement something
            pass
            
        return result
    
    def handle_reactive_clue(
        self,
        clue_giver: int,
        target_index: int,
        clue_type: int,
        clue_value: int,
        card_orders,
    ):
        ordering = self.get_reactive_player_index_ordering(clue_giver)
        target_hand = self.hands[target_index]
        slots_touched = sorted(
            len(target_hand) - i
            for i, card in enumerate(target_hand) if card.order in card_orders
        )
        focused_slot = (
            slots_touched[1] if (slots_touched[0] == 1 and len(slots_touched) > 1)
            else slots_touched[0]
        )
        self.unresolved_reactions[ordering[0]] = UnresolvedReaction(
            target_index=target_index,
            play_parity=0 if clue_type == RANK_CLUE else 1,
            focused_slot=focused_slot,
            ordering=ordering,
            player_slot_orders={
                player_index: sorted([x.order for x in self.hands[player_index]], reverse=True)
                for player_index in ordering
            },
            current_play_orders=deepcopy(self.all_play_orders),
            current_clued_orders=deepcopy(self.clued_card_orders),
            current_discard_orders=deepcopy(self.all_discard_orders),
            all_candidates_list=deepcopy(self.all_candidates_list),
            target_hand=deepcopy(target_hand),
            playables=deepcopy(self.playables),
            trash=deepcopy(self.trash)
        )

        return super().handle_clue(
            clue_giver, target_index, clue_type, clue_value, card_orders
        )
    
    def handle_play(self, player_index: int, order: int, suit_index: int, rank: int):
        result = super().handle_play(player_index, order, suit_index, rank)
        self.play_orders[player_index] = [
            x for x in self.play_orders[player_index] if x != order
        ]
        self.discard_orders[player_index] = [
            x for x in self.discard_orders[player_index] if x != order
        ]
        self.ctd_order[player_index] = None
        if self.unresolved_reactions[player_index] is not None:
            ur = self.unresolved_reactions[player_index]
            reacter_index = ur.ordering[0]
            reacter_hand = ur.player_slot_orders[reacter_index]
            slot_reacted = reacter_hand.index(order) + 1

            tgt_slot = (ur.focused_slot - slot_reacted - 1) % len(reacter_hand) + 1

            if ur.play_parity == 0:
                playable_order = ur.player_slot_orders[ur.ordering[1]][tgt_slot - 1]
                print(f'[handle_play 1] Unresolved reaction: adding play order {playable_order}')
                if playable_order not in {x.order for x in self.hands[ur.ordering[1]]}:
                    print(f'Bad playable order {playable_order} not found in hand, ignoring...')
                else:
                    self.play_orders[ur.ordering[1]].append(playable_order)
                    self.write_note(playable_order, note=f"[f] order {len(self.play_orders[ur.ordering[1]])}")
            elif ur.play_parity == 1:
                discard_order = ur.player_slot_orders[ur.ordering[1]][tgt_slot - 1]
                print(f'[handle_play 2] Unresolved reaction: adding discard order {discard_order}')
                if discard_order not in {x.order for x in self.hands[ur.ordering[1]]}:
                    print(f'Bad discard order {discard_order} not found in hand, ignoring...')
                else:
                    self.discard_orders[ur.ordering[1]].append(discard_order)
                    self.write_note(discard_order, note=f"[kt] order {len(self.discard_orders[ur.ordering[1]])}")

            self.unresolved_reactions[player_index] = None

        self.update_play_discard_orders()
        print(f'Handling play of {order} by {player_index}. New play orders: {self.play_orders}, new discard orders: {self.discard_orders}')
        return result
    
    def handle_discard(self, player_index: int, order: int, suit_index: int, rank: int):
        # TODO: handle locked players
        # TODO: elim
        result = super().handle_discard(player_index, order, suit_index, rank)
        self.discard_orders[player_index] = [
            x for x in self.discard_orders[player_index] if x != order
        ]
        self.play_orders[player_index] = [
            x for x in self.play_orders[player_index] if x != order
        ]
        self.ctd_order[player_index] = None
        if self.unresolved_reactions[player_index] is not None:
            ur = self.unresolved_reactions[player_index]
            reacter_index = ur.ordering[0]
            reacter_hand = ur.player_slot_orders[reacter_index]
            slot_reacted = reacter_hand.index(order) + 1

            tgt_slot = (ur.focused_slot - slot_reacted - 1) % len(reacter_hand) + 1

            if ur.play_parity == 0:
                discard_order = ur.player_slot_orders[ur.ordering[1]][tgt_slot - 1]
                print(f'[handle_discard 1] Unresolved reaction: adding discard order {discard_order}')
                if discard_order not in {x.order for x in self.hands[ur.ordering[1]]}:
                    print(f'Bad discard order {discard_order} not found in hand, skipping...')
                else:
                    self.discard_orders[ur.ordering[1]].append(discard_order)
                    self.write_note(discard_order, note=f"[kt] order {len(self.discard_orders[ur.ordering[1]])}")
            elif ur.play_parity == 1:
                playable_order = ur.player_slot_orders[ur.ordering[1]][tgt_slot - 1]
                print(f'[handle_discard 2] Unresolved reaction: adding play order {playable_order}')
                if playable_order not in {x.order for x in self.hands[ur.ordering[1]]}:
                    print(f'Bad playable order {playable_order} not found in hand, skipping...')
                else:
                    self.play_orders[ur.ordering[1]].append(playable_order)
                    self.write_note(playable_order, note=f"[f] order {len(self.play_orders[ur.ordering[1]])}")

            self.unresolved_reactions[player_index] = None

        self.update_play_discard_orders()
        print(f'Handling discard of {order} by {player_index}. New play orders: {self.play_orders}, new discard orders: {self.discard_orders}')
        return result
    
    def handle_strike(self, order: int):
        for player_index in range(len(self.unresolved_reactions)):
            self.unresolved_reactions[player_index] = None
    
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
        unclued_orders = [
            card.order for card in self.hands[target_index] if card.order not in self.clued_card_orders
        ]
        if not len(unclued_orders):
            return None
        
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
        """(clue_value, clue_type, target_index) -> clue_type"""
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
                        
                        if c.order in self.all_discard_orders:
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
                        result[(clue_value, clue_type, target_index)] = "SAFE_ACTION"
                    elif len(newly_touched_cards):
                        if clue_type == RANK_CLUE:
                            all_good_playable = self.every_good_card_of_rank_is_playable(clue_value)
                            all_rank_trash = self.every_card_of_rank_is_trash(clue_value)

                            if all_good_playable:
                                if not self.is_weak_trash_card(newly_touched_cards[-1]):
                                    result[(clue_value, clue_type, target_index)] = "DIRECT_PLAY"
                            elif all_rank_trash:
                                ref_play_index = self.get_index_of_ref_play_target(target_index, clue_type, clue_value)
                                targeted_card = target_hand[ref_play_index]
                                if self.is_playable_card(targeted_card) and targeted_card.to_tuple() not in self.all_play_tuples:
                                    result[(clue_value, clue_type, target_index)] = "REF_PLAY"
                            elif not all_good_playable:
                                ref_discard_index = self.get_index_of_ref_discard_target(target_index, clue_type, clue_value)
                                if ref_discard_index is None:
                                    result[(clue_value, clue_type, target_index)] = "LOCK"
                                else:
                                    result[(clue_value, clue_type, target_index)] = "REF_DISCARD"
                        else:
                            ref_play_index = self.get_index_of_ref_play_target(target_index, clue_type, clue_value)
                            playable_card = target_hand[ref_play_index]
                            if self.is_playable_card(playable_card) and playable_card.to_tuple() not in self.all_play_tuples:
                                result[(clue_value, clue_type, target_index)] = "REF_PLAY"

        return result

    def get_reactive_clues(self) -> Dict[Tuple[int, int, int], str]:
        """(clue_value, clue_type, target_index) -> clue_type"""
        if self.num_players > 3:
            raise NotImplementedError
        result = {}
        ordering = self.get_reactive_player_index_ordering()

        # TODO: response inversion
        if not len(ordering):
            return {}
        
        reacter_index = ordering[0]
        reacter_hand = self.hands[reacter_index]
        for target_index in [ordering[1]]:
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
                    slots_touched = sorted([len(target_hand) - x for x in slots_touched])
                    focused_slot = (
                        slots_touched[1] if (slots_touched[0] == 1 and len(slots_touched) > 1)
                        else slots_touched[0]
                    )
                    pslot = get_reactive_playable_human_slot(
                        target_hand,
                        self.all_candidates_list[target_index],
                        self.playables,
                        self.all_play_orders
                    )

                    if clue_type == RANK_CLUE:
                        if pslot is None:
                            for fslot in [1, 5, 4, 3, 2]:
                                target_fslot = (focused_slot - fslot - 1) % len(target_hand) + 1
                                target_card = target_hand[-target_fslot]
                                if target_card.to_tuple() in self.one_away_from_playables:
                                    reacter_card = reacter_hand[-fslot]

                                    reacter_tuple_required = self.get_next_playable_card_tuple(target_card.suit_index)
                                    if reacter_tuple_required not in self.all_candidates_list[reacter_index][-fslot]:
                                        print(
                                            f'[{clue_value}, {clue_type}, {target_index}] Attempted finessed card '
                                            f'{reacter_tuple_required} cannot be on reacters slot {fslot}'
                                        )
                                        continue
                                    
                                    if reacter_card.to_tuple() == reacter_tuple_required:
                                        result[(clue_value, clue_type, target_index)] = '2P0D_FINESSE'

                                    break
                        else:
                            reactive_pslot = (focused_slot - pslot - 1) % len(target_hand) + 1
                            if self.is_playable_card(reacter_hand[-reactive_pslot]) and reacter_hand[-reactive_pslot].to_tuple() != target_hand[-pslot].to_tuple():
                                result[(clue_value, clue_type, target_index)] = '2P0D_PLAY'
                    else:                      
                        tslot = get_reactive_trash_human_slot(
                            target_hand,
                            self.all_candidates_list[target_index],
                            self.trash,
                            self.clued_card_orders,
                            self.all_discard_orders
                        )
                        if pslot is not None:
                            reactive_tslot = (focused_slot - pslot - 1) % len(target_hand) + 1
                            if not self.is_critical_card(reacter_hand[-reactive_tslot]):
                                result[(clue_value, clue_type, target_index)] = '1P1D_DISCARD'
                        elif tslot is not None:
                            reactive_pslot = (focused_slot - tslot - 1) % len(target_hand) + 1
                            if self.is_playable_card(reacter_hand[-reactive_pslot]):
                                result[(clue_value, clue_type, target_index)] = '1P1D_PLAY'

        return result
