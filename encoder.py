from game_state import (
    Card,
    GameState,
    SUITS,
    DARK_SUIT_NAMES,
    get_all_cards,
    RANK_CLUE,
    COLOR_CLUE,
    is_brownish_pinkish,
    is_whiteish_rainbowy,
    get_all_touched_cards,
    get_available_color_clues,
    get_available_rank_clues,
)

from typing import Callable, Dict, List, Set, Optional, Tuple
from copy import deepcopy


def get_v1_mod_table(variant_name: str, preferred_modulus=None):
    # trash is marked as (0, 0)
    # playable is marked as (-1, 0)
    # stack x + n is marked as (x, -n)
    num_suits = len(SUITS[variant_name])
    if num_suits == 6:
        if preferred_modulus == 12:
            mod_table = {
                0: [(0, 0)],
                1: [(-1, 0)],
                2: [(0, -2), (3, -2)],
                3: [(1, -2)],
                4: [(2, -2)],
                5: [(4, -2)],
                6: [(5, -2)],
                7: [(0, -3), (3, -3)],
                8: [(1, -3), (4, -3)],
                9: [(2, -3), (5, -3)],
                10: [(0, -4), (1, -5), (2, -4), (3, -5), (4, -4), (5, -5)],
                11: [(0, -5), (1, -4), (2, -5), (3, -4), (4, -5), (5, -4)],
            }
        elif preferred_modulus == 16:
            mod_table = {
                0: [(0, 0)],
                1: [(-1, 0)],
                2: [(0, -2)],
                3: [(1, -2)],
                4: [(2, -2)],
                5: [(3, -2)],
                6: [(4, -2)],
                7: [(5, -2)],
                8: [(0, -3), (3, -3)],
                9: [(1, -3), (4, -3)],
                10: [(2, -3), (5, -3)],
                11: [(0, -4), (3, -5), (5, -4)],
                12: [(1, -4), (4, -5)],
                13: [(2, -4), (5, -5)],
                14: [(3, -4), (0, -5)],
                15: [(4, -4), (1, -5), (2, -5)],
            }
    elif num_suits == 5:
        if preferred_modulus == 12:
            mod_table = {
                0: [(0, 0)],
                1: [(-1, 0)],
                2: [(0, -2)],
                3: [(1, -2)],
                4: [(2, -2)],
                5: [(3, -2)],
                6: [(4, -2)],
                7: [(0, -3), (2, -3)],
                8: [(1, -3), (3, -3)],
                9: [(4, -3)],
                10: [(0, -4), (1, -5), (2, -4), (3, -5), (4, -4)],
                11: [(0, -5), (1, -4), (2, -5), (3, -4), (4, -5)],
            }
        elif preferred_modulus == 16:
            mod_table = {
                0: [(0, 0)],
                1: [(-1, 0)],
                2: [(0, -2)],
                3: [(1, -2)],
                4: [(2, -2)],
                5: [(3, -2)],
                6: [(4, -2)],
                7: [(0, -3)],
                8: [(1, -3)],
                9: [(2, -3)],
                10: [(3, -3)],
                11: [(4, -3)],
                12: [(0, -4), (2, -5), (4, -4)],
                13: [(1, -4), (3, -5)],
                14: [(2, -4), (4, -5)],
                15: [(3, -4), (0, -5), (1, -5)],
            }
        elif preferred_modulus == 20:
            mod_table = {
                0: [(0, 0)],
                1: [(-1, 0)],
                2: [(0, -2)],
                3: [(1, -2)],
                4: [(2, -2)],
                5: [(3, -2)],
                6: [(4, -2)],
                7: [(0, -3)],
                8: [(1, -3)],
                9: [(2, -3)],
                10: [(3, -3)],
                11: [(4, -3)],
                12: [(0, -4)],
                13: [(1, -4)],
                14: [(2, -4)],
                15: [(3, -4)],
                16: [(4, -4)],
                17: [(0, -5), (2, -5)],
                18: [(1, -5), (3, -5)],
                19: [(4, -5)],
            }
    elif num_suits == 4:
        if preferred_modulus == 12:
            mod_table = {
                0: [(0, 0)],
                1: [(-1, 0)],
                2: [(0, -2)],
                3: [(1, -2)],
                4: [(2, -2)],
                5: [(3, -2)],
                6: [(0, -3), (2, -3)],
                7: [(1, -3), (3, -3)],
                8: [(0, -4), (2, -5)],
                9: [(1, -4), (3, -5)],
                10: [(2, -4), (0, -5)],
                11: [(3, -4), (1, -5)],
            }
        elif preferred_modulus == 16:
            mod_table = {
                0: [(0, 0)],
                1: [(-1, 0)],
                2: [(0, -2)],
                3: [(1, -2)],
                4: [(2, -2)],
                5: [(3, -2)],
                6: [(0, -3)],
                7: [(1, -3)],
                8: [(2, -3)],
                9: [(3, -3)],
                10: [(0, -4)],
                11: [(1, -4)],
                12: [(2, -4)],
                13: [(3, -4)],
                14: [(0, -5), (2, -5)],
                15: [(1, -5), (3, -5)],
            }
    return mod_table


def get_v2_mod_table(variant_name: str, preferred_modulus=None):
    # trash is marked as (0, 0)
    # playable is marked as (-1, 0)
    # stack x + n is marked as (x, -n)
    num_suits = len(SUITS[variant_name])
    dark_suits = [x for x in SUITS[variant_name] if x in DARK_SUIT_NAMES]
    if num_suits == 6:
        if preferred_modulus == 15:
            mod_table = {
                0: [(0, 0)],
                1: [(0, -1)],
                2: [(1, -1)],
                3: [(2, -1)],
                4: [(3, -1)],
                5: [(4, -1)],
                6: [(5, -1)],
                7: [(0, -2), (1, -2)],
                8: [(2, -2), (3, -2)],
                9: [(4, -2)],
                10: [(5, -2)],
                11: [(0, -3), (1, -3)],
                12: [(2, -3), (3, -3)],
                13: [(4, -3), (5, -3)],
                14: [(i, -j) for i in range(6) for j in {4, 5}],
            }
        elif preferred_modulus == 16:
            if len(dark_suits) == 2:
                mod_table = {
                    0: [(0, 0)],
                    1: [(0, -1)],
                    2: [(1, -1)],
                    3: [(2, -1)],
                    4: [(3, -1)],
                    5: [(4, -1), (5, -1)],
                    6: [(0, -2), (1, -2)],
                    7: [(2, -2)],
                    8: [(3, -2)],
                    9: [(4, -2)],
                    10: [(5, -2)],
                    11: [(0, -3), (1, -3)],
                    12: [(2, -3), (3, -3)],
                    13: [(4, -3)],
                    14: [(5, -3)],
                    15: [(i, -j) for i in range(6) for j in {4, 5}],
                }
            else:
                mod_table = {
                    0: [(0, 0)],
                    1: [(0, -1)],
                    2: [(1, -1)],
                    3: [(2, -1)],
                    4: [(3, -1)],
                    5: [(4, -1)],
                    6: [(5, -1)],
                    7: [(0, -2)],
                    8: [(1, -2)],
                    9: [(2, -2)],
                    10: [(3, -2)],
                    11: [(4, -2)],
                    12: [(5, -2)],
                    13: [(0, -3), (1, -3)],
                    14: [(4, -3), (5, -3)],
                    15: [(2, -3), (3, -3)]
                    + [(i, -j) for i in range(6) for j in {4, 5}],
                }
    elif num_suits == 5:
        if preferred_modulus == 12:
            mod_table = {
                0: [(0, 0)],
                1: [(0, -1)],
                2: [(1, -1)],
                3: [(2, -1)],
                4: [(3, -1)],
                5: [(4, -1)],
                6: [(0, -2), (1, -2)],
                7: [(2, -2), (3, -2)],
                8: [(4, -2)],
                9: [(0, -3), (1, -3)],
                10: [(2, -3)],
                11: [(3, -3), (4, -3)] + [(i, -j) for i in range(5) for j in {4, 5}],
            }
        elif preferred_modulus == 15:
            mod_table = {
                0: [(0, 0)],
                1: [(0, -1)],
                2: [(1, -1)],
                3: [(2, -1)],
                4: [(3, -1)],
                5: [(4, -1)],
                6: [(0, -2)],
                7: [(1, -2)],
                8: [(2, -2)],
                9: [(3, -2)],
                10: [(4, -2)],
                11: [(0, -3)],
                12: [(1, -3)],
                13: [(2, -3)],
                14: [(3, -3), (4, -3)] + [(i, -j) for i in range(5) for j in {4, 5}],
            }
        elif preferred_modulus == 16:
            mod_table = {
                0: [(0, 0)],
                1: [(0, -1)],
                2: [(1, -1)],
                3: [(2, -1)],
                4: [(3, -1)],
                5: [(4, -1)],
                6: [(0, -2)],
                7: [(1, -2)],
                8: [(2, -2)],
                9: [(3, -2)],
                10: [(4, -2)],
                11: [(0, -3)],
                12: [(1, -3)],
                13: [(2, -3)],
                14: [(4, -3)],
                15: [(3, -3)] + [(i, -j) for i in range(5) for j in {4, 5}],
            }
    elif num_suits == 4:
        if preferred_modulus == 12:
            mod_table = {
                0: [(0, 0)],
                1: [(0, -1)],
                2: [(1, -1)],
                3: [(2, -1)],
                4: [(3, -1)],
                5: [(0, -2)],
                6: [(1, -2)],
                7: [(2, -2)],
                8: [(3, -2)],
                9: [(0, -3), (1, -3)],
                10: [(2, -3), (3, -3)],
                11: [(i, -j) for i in range(4) for j in {4, 5}],
            }
        elif preferred_modulus == 15:
            mod_table = {
                0: [(0, 0)],
                1: [(0, -1)],
                2: [(1, -1)],
                3: [(2, -1)],
                4: [(3, -1)],
                5: [(0, -2)],
                6: [(1, -2)],
                7: [(2, -2)],
                8: [(3, -2)],
                9: [(0, -3)],
                10: [(1, -3)],
                11: [(2, -3)],
                12: [(3, -3)],
                13: [(0, -4)],
                14: [(1, -4), (2, -4), (3, -4), (0, -5), (1, -5), (2, -5), (3, -5)],
            }
        elif preferred_modulus == 16:
            mod_table = {
                0: [(0, 0)],
                1: [(0, -1)],
                2: [(1, -1)],
                3: [(2, -1)],
                4: [(3, -1)],
                5: [(0, -2)],
                6: [(1, -2)],
                7: [(2, -2)],
                8: [(3, -2)],
                9: [(0, -3)],
                10: [(1, -3)],
                11: [(2, -3)],
                12: [(3, -3)],
                13: [(0, -4)],
                14: [(1, -4)],
                15: [(2, -4), (3, -4), (0, -5), (1, -5), (2, -5), (3, -5)],
            }
    return mod_table


def get_special_hat_clues_dict(variant_name: str):
    all_3color_wr_vars = [
        var
        for var in SUITS
        if len(get_available_color_clues(var)) == 3 and is_whiteish_rainbowy(var)
    ]
    all_1color_vars = [var for var in SUITS if len(get_available_color_clues(var)) == 1]
    all_lp_1_vars = [var for var in SUITS if "Light-Pink-Ones" in var]
    all_mr_1_vars = [var for var in SUITS if "Muddy-Rainbow-Ones" in var]
    all_oe_vars = [var for var in SUITS if "Odds and Evens" in var]
    base_dct = {
        var: {
            0: [(COLOR_CLUE, 0), (RANK_CLUE, 2)],
            1: [(COLOR_CLUE, 1), (RANK_CLUE, 3)],
            2: [(COLOR_CLUE, 2), (RANK_CLUE, 4)],
            3: [(RANK_CLUE, 5), (RANK_CLUE, 1)],
        }
        for var in all_3color_wr_vars
    }

    for var in all_1color_vars:
        base_dct[var] = {
            0: [(COLOR_CLUE, 0)],
            1: [(RANK_CLUE, 1), (RANK_CLUE, 5)],
            2: [(RANK_CLUE, 2), (RANK_CLUE, 3)],
            3: [(RANK_CLUE, 4)],
        }

    for var in all_lp_1_vars:
        avail_color_clues = get_available_color_clues(var)
        if len(avail_color_clues) == 6:
            base_dct[var] = {
                0: [(RANK_CLUE, 5), (COLOR_CLUE, 0)],
                1: [(RANK_CLUE, 2), (COLOR_CLUE, 1), (COLOR_CLUE, 2)],
                2: [(RANK_CLUE, 3), (COLOR_CLUE, 3), (COLOR_CLUE, 4)],
                3: [(RANK_CLUE, 4), (COLOR_CLUE, 5)],
            }
        elif len(avail_color_clues) == 5:
            base_dct[var] = {
                0: [(RANK_CLUE, 5), (COLOR_CLUE, 0)],
                1: [(RANK_CLUE, 2), (COLOR_CLUE, 1), (COLOR_CLUE, 2)],
                2: [(RANK_CLUE, 3), (COLOR_CLUE, 3)],
                3: [(RANK_CLUE, 4), (COLOR_CLUE, 4)],
            }
        elif len(avail_color_clues) == 4:
            base_dct[var] = {
                0: [(RANK_CLUE, 5), (COLOR_CLUE, 0)],
                1: [(RANK_CLUE, 2), (COLOR_CLUE, 1)],
                2: [(RANK_CLUE, 3), (COLOR_CLUE, 2)],
                3: [(RANK_CLUE, 4), (COLOR_CLUE, 3)],
            }

    for var in all_mr_1_vars:
        avail_color_clues = get_available_color_clues(var)
        if len(avail_color_clues) == 6:
            base_dct[var] = {
                0: [(COLOR_CLUE, 0), (RANK_CLUE, 5)],
                1: [(COLOR_CLUE, 1), (COLOR_CLUE, 2), (RANK_CLUE, 2)],
                2: [(COLOR_CLUE, 3), (COLOR_CLUE, 4), (RANK_CLUE, 3)],
                3: [(COLOR_CLUE, 5), (RANK_CLUE, 4)],
            }
        elif len(avail_color_clues) == 5:
            base_dct[var] = {
                0: [(COLOR_CLUE, 0), (RANK_CLUE, 5)],
                1: [(COLOR_CLUE, 1), (COLOR_CLUE, 2), (RANK_CLUE, 2)],
                2: [(COLOR_CLUE, 3), (RANK_CLUE, 3)],
                3: [(COLOR_CLUE, 4), (RANK_CLUE, 4)],
            }
        elif len(avail_color_clues) == 4:
            base_dct[var] = {
                0: [(COLOR_CLUE, 0), (RANK_CLUE, 5)],
                1: [(COLOR_CLUE, 1), (RANK_CLUE, 2)],
                2: [(COLOR_CLUE, 2), (RANK_CLUE, 3)],
                3: [(COLOR_CLUE, 3), (RANK_CLUE, 4)],
            }

    for var in all_oe_vars:
        avail_color_clues = get_available_color_clues(var)
        if len(avail_color_clues) == 6:
            base_dct[var] = {
                0: [(RANK_CLUE, 0), (COLOR_CLUE, 0)],
                1: [(RANK_CLUE, 1)],
                2: [(COLOR_CLUE, 1), (COLOR_CLUE, 2)],
                3: [(COLOR_CLUE, 3), (COLOR_CLUE, 4), (COLOR_CLUE, 5)],
            }
        elif len(avail_color_clues) == 5:
            base_dct[var] = {
                0: [(RANK_CLUE, 0), (COLOR_CLUE, 0)],
                1: [(RANK_CLUE, 1)],
                2: [(COLOR_CLUE, 1), (COLOR_CLUE, 2)],
                3: [(COLOR_CLUE, 3), (COLOR_CLUE, 4)],
            }
        elif len(avail_color_clues) == 4:
            base_dct[var] = {
                0: [(RANK_CLUE, 0)],
                1: [(RANK_CLUE, 1)],
                2: [(COLOR_CLUE, 0), (COLOR_CLUE, 1)],
                3: [(COLOR_CLUE, 2), (COLOR_CLUE, 3)],
            }

    base_dct["Valentine Mix (6 Suits)"] = {
        0: [(RANK_CLUE, 5), (RANK_CLUE, 1)],
        1: [(COLOR_CLUE, 0), (RANK_CLUE, 2)],
        2: [(COLOR_CLUE, 1), (RANK_CLUE, 3)],
        3: [(RANK_CLUE, 4)],
    }
    base_dct["Valentine Mix (5 Suits)"] = {
        0: [(RANK_CLUE, 5), (RANK_CLUE, 1)],
        1: [(COLOR_CLUE, 0), (RANK_CLUE, 2)],
        2: [(COLOR_CLUE, 1), (RANK_CLUE, 3)],
        3: [(RANK_CLUE, 4)],
    }

    return base_dct.get(variant_name, {})


class SuperPosition:
    def __init__(
        self,
        default_residue: int,
        increment_candidates: Dict[int, Set[Tuple[int, int]]],
        triggering_orders: Set[int],
    ):
        self.default_residue = default_residue
        self.increment = increment_candidates
        self.triggering_orders = triggering_orders
        self.unexpected_trash = 0

    @property
    def residue_increment(self) -> int:
        return self.unexpected_trash

    def get_updated_residue(self, mod_base: int) -> int:
        return (self.default_residue + self.residue_increment) % mod_base

    def get_sp_identities(self) -> Set[Tuple[int, int]]:
        return self.increment[self.residue_increment]

    def __str__(self):
        return (
            f"Residue: {self.default_residue}, Triggering: {self.triggering_orders}, "
            f"Unexpected # trash: {self.unexpected_trash}\n"
            f"Superposition identities: {self.get_sp_identities()}"
        )

    def __repr__(self):
        return self.__str__()


class BaseEncoderGameState(GameState):
    def __init__(self, variant_name, player_names, our_player_index, mod_table_func):
        self.mod_table_func: Callable[[str, int], Dict] = mod_table_func
        super().__init__(variant_name, player_names, our_player_index)
        self.other_info_clued_card_orders["hat_clued_card_orders"] = set()
        self.other_info_clued_card_orders["trashy_orders"] = []

    @property
    def hat_clued_card_orders(self) -> Set[int]:
        return self.other_info_clued_card_orders["hat_clued_card_orders"]

    @property
    def trashy_orders(self) -> List[int]:
        return self.other_info_clued_card_orders["trashy_orders"]

    # various game conditions
    @property
    def cannot_play(self) -> bool:
        max_crits = 0
        for player_index in range(self.num_players):
            if player_index == self.our_player_index:
                continue
            num_crits = sum(
                [self.is_critical_card(card) for card in self.hands[player_index]]
            )
            max_crits = max(max_crits, num_crits)

        return (
            max_crits > self.num_cards_in_deck
            and self.num_cards_in_deck > 0
            and self.pace >= 0
        )

    @property
    def endgame_stall_condition(self) -> bool:
        cond1 = self.clue_tokens > 0 and (
            self.pace <= self.num_players / 2 or self.num_cards_in_deck == 1
        )
        cond2 = self.clue_tokens >= self.num_players and (
            self.num_cards_in_deck <= self.num_players - 2
        )
        return cond1 or cond2

    @property
    def no_urgency(self) -> bool:
        return (
            self.pace > self.num_players / 2
            and self.num_cards_in_deck > self.num_players - 2
        )

    def set_variant_name(self, variant_name: str, num_players: int):
        super().set_variant_name(variant_name, num_players)
        if num_players == 4:
            self.mod_table = self.mod_table_func(variant_name, preferred_modulus=12)
        elif num_players == 5:
            self.mod_table = self.mod_table_func(variant_name, preferred_modulus=16)
        elif num_players == 6:
            self.mod_table = self.mod_table_func(variant_name, preferred_modulus=20)
        else:
            raise NotImplementedError

    def get_rightmost_unnumbered_card(self, player_index) -> Optional[Card]:
        for card in self.hands[player_index]:  # iterating oldest to newest
            if card.order not in self.rank_clued_card_orders:
                return card
        return None

    def get_rightmost_uncolored_card(self, player_index) -> Optional[Card]:
        for card in self.hands[player_index]:  # iterating oldest to newest
            if card.order not in self.color_clued_card_orders:
                return card
        return None

    def get_leftmost_non_hat_clued_card(self, player_index) -> Optional[Card]:
        for j in range(len(self.hands[player_index])):
            card = self.hands[player_index][-j - 1]
            if card.order not in self.hat_clued_card_orders:
                return card
        return None

    def get_all_other_players_hat_clued_cards(
        self, player_index=None, no_singletons=False
    ) -> Set[Tuple[int, int]]:
        if no_singletons:
            return {
                (c.suit_index, c.rank)
                for pindex, hand in self.hands.items()
                for i, c in enumerate(hand)
                if pindex not in {self.our_player_index, player_index}
                and c.order in self.hat_clued_card_orders
                and len(self.all_candidates_list[pindex][i]) > 1
            }
        else:
            return {
                (c.suit_index, c.rank)
                for pindex, hand in self.hands.items()
                for c in hand
                if pindex not in {self.our_player_index, player_index}
                and c.order in self.hat_clued_card_orders
            }

    def get_leftmost_non_hat_clued_cards(self) -> List[Optional[Card]]:
        result = []
        for player_index, hand in self.hands.items():
            if player_index == self.our_player_index:
                continue
            lnhc = self.get_leftmost_non_hat_clued_card(player_index)
            result.append(lnhc)
        return result

    @property
    def mod_base(self) -> int:
        return max(self.mod_table) + 1

    @property
    def num_residues_per_player(self) -> int:
        return int(self.mod_base / (self.num_players - 1))

    @property
    def identity_to_residue(self) -> Dict[Tuple[int, int], int]:
        result = {}
        trash_residue = 0
        for residue, identities in self.mod_table.items():
            # trash is marked as (0, 0)
            # playable is marked as (-1, 0)
            # stack x + n is marked as (x, -n)
            for identity in identities:
                if identity == (-1, 0):
                    for playable in self.playables:
                        result[playable] = residue
                elif identity[1] < 0:
                    # blue stack is 2, identity of (3, -2) is blue 4
                    rank = self.stacks[identity[0]] - identity[1]
                    result[(identity[0], rank)] = residue
                elif identity == (0, 0):
                    assert residue == trash_residue

        # override explicit identities
        for residue, identities in self.mod_table.items():
            for identity in identities:
                if identity[1] > 0:
                    result[identity] = residue

        # override trash
        for suit_index, rank in self.trash:
            result[(suit_index, rank)] = trash_residue

        return result

    @property
    def residue_to_identities(self) -> Dict[int, Set[Tuple[int, int]]]:
        result = {}
        for identity, residue in self.identity_to_residue.items():
            if residue not in result:
                result[residue] = set()
            result[residue].add(identity)
        return result

    def get_special_hat_clues(self, target_index: int, clue_mapping_only=False) -> Dict:
        dct = get_special_hat_clues_dict(self.variant_name)
        if clue_mapping_only:
            return dct if len(dct) else None

        return (
            {
                raw_residue: self.get_cards_touched_dict(target_index, clue_type_values)
                for raw_residue, clue_type_values in dct.items()
            }
            if len(dct)
            else None
        )

    def get_all_possible_clues_dict(
        self,
    ) -> Dict[Tuple[int, int, int], Set[Tuple[int, int]]]:
        all_possible_clues_dict = {}
        for target_index in range(self.num_players):
            if target_index == self.our_player_index:
                continue

            clue_type_values = [
                (RANK_CLUE, cv) for cv in get_available_rank_clues(self.variant_name)
            ] + [
                (COLOR_CLUE, cv)
                for cv in range(len(get_available_color_clues(self.variant_name)))
            ]
            all_possible_clues_dict.update(
                self.get_cards_touched_dict(target_index, clue_type_values)
            )
        return all_possible_clues_dict

    def get_legal_clues_helper(
        self, sum_of_residues: int
    ) -> Dict[Tuple[int, int, int], Set[Tuple[int, int]]]:
        num_residues = self.num_residues_per_player
        target_index = (
            self.our_player_index + 1 + (sum_of_residues // num_residues)
        ) % self.num_players
        raw_residue = sum_of_residues % num_residues
        target_hand = self.hands[target_index]

        assert target_index != self.our_player_index
        print(
            "Evaluating legal hat clues - sum of residues =",
            sum_of_residues,
            "target_index",
            target_index,
        )
        maybe_special_hat_clues = self.get_special_hat_clues(target_index)
        if maybe_special_hat_clues is not None:
            return maybe_special_hat_clues[raw_residue]

        if num_residues == 4:
            if raw_residue in {0, 1}:
                if is_brownish_pinkish(self.variant_name):
                    if raw_residue == 0:
                        return self.get_cards_touched_dict(
                            target_index,
                            [(RANK_CLUE, 1), (RANK_CLUE, 3), (RANK_CLUE, 5)],
                        )
                    else:
                        return self.get_cards_touched_dict(
                            target_index,
                            [(RANK_CLUE, 2), (RANK_CLUE, 4)],
                        )
                else:
                    rightmost_unnumbered = self.get_rightmost_unnumbered_card(
                        target_index
                    )
                    # iterate over rank clues
                    # TODO: special 1s/5s
                    rank_to_cards_touched = {}
                    for clue_value in get_available_rank_clues(self.variant_name):
                        cards_touched = get_all_touched_cards(
                            RANK_CLUE, clue_value, self.variant_name
                        )
                        cards_touched_in_target_hand = [
                            card
                            for card in target_hand
                            if (card.suit_index, card.rank) in cards_touched
                        ]
                        if len(cards_touched_in_target_hand):
                            rank_to_cards_touched[
                                clue_value
                            ] = cards_touched_in_target_hand

                    if rightmost_unnumbered is None:
                        clue_rank = (
                            min(rank_to_cards_touched)
                            if raw_residue == 0
                            else max(rank_to_cards_touched)
                        )
                        return {
                            (clue_value, RANK_CLUE, target_index): cards_touched
                            for clue_value, cards_touched in rank_to_cards_touched.items()
                            if clue_value == clue_rank
                        }
                    else:
                        if raw_residue == 0:
                            return {
                                (clue_value, RANK_CLUE, target_index): cards_touched
                                for clue_value, cards_touched in rank_to_cards_touched.items()
                                if rightmost_unnumbered in cards_touched
                            }
                        else:
                            return {
                                (clue_value, RANK_CLUE, target_index): cards_touched
                                for clue_value, cards_touched in rank_to_cards_touched.items()
                                if rightmost_unnumbered not in cards_touched
                            }

            elif raw_residue in {2, 3}:
                if is_whiteish_rainbowy(self.variant_name):
                    num_colors = len(get_available_color_clues(self.variant_name))
                    if num_colors in {2, 4, 5, 6}:
                        color_to_cards_touched = {}
                        clue_values = [
                            x for x in range(num_colors) if (x - raw_residue) % 2 == 0
                        ]
                        for clue_value in clue_values:
                            cards_touched = get_all_touched_cards(
                                COLOR_CLUE, clue_value, self.variant_name
                            )
                            cards_touched_in_target_hand = [
                                card
                                for card in target_hand
                                if (card.suit_index, card.rank) in cards_touched
                            ]
                            if len(cards_touched_in_target_hand):
                                color_to_cards_touched[
                                    clue_value
                                ] = cards_touched_in_target_hand

                        return {
                            (clue_value, COLOR_CLUE, target_index): cards_touched
                            for clue_value, cards_touched in color_to_cards_touched.items()
                        }
                    else:
                        raise NotImplementedError
                else:
                    rightmost_uncolored = self.get_rightmost_uncolored_card(
                        target_index
                    )
                    # iterate over color clues
                    color_to_cards_touched = {}
                    for clue_value, _ in enumerate(
                        get_available_color_clues(self.variant_name)
                    ):
                        cards_touched = get_all_touched_cards(
                            COLOR_CLUE, clue_value, self.variant_name
                        )
                        cards_touched_in_target_hand = [
                            card
                            for card in target_hand
                            if (card.suit_index, card.rank) in cards_touched
                        ]
                        if len(cards_touched_in_target_hand):
                            color_to_cards_touched[
                                clue_value
                            ] = cards_touched_in_target_hand

                    if rightmost_uncolored is None:
                        clue_color = (
                            min(color_to_cards_touched)
                            if raw_residue == 2
                            else max(color_to_cards_touched)
                        )
                        return {
                            (clue_value, COLOR_CLUE, target_index): cards_touched
                            for clue_value, cards_touched in color_to_cards_touched.items()
                            if clue_value == clue_color
                        }
                    else:
                        if raw_residue == 2:
                            return {
                                (clue_value, COLOR_CLUE, target_index): cards_touched
                                for clue_value, cards_touched in color_to_cards_touched.items()
                                if rightmost_uncolored in cards_touched
                            }
                        else:
                            return {
                                (clue_value, COLOR_CLUE, target_index): cards_touched
                                for clue_value, cards_touched in color_to_cards_touched.items()
                                if rightmost_uncolored not in cards_touched
                            }

        elif num_residues == 3:
            raise NotImplementedError
        else:
            raise NotImplementedError

    def get_legal_clues(self) -> Dict[Tuple[int, int, int], Set[Tuple[int, int]]]:
        # (clue_value, clue_type, target_index) -> cards_touched
        raise NotImplementedError

    def evaluate_clue_score(self, clue_value, clue_type, target_index) -> int:
        all_cards_touched_by_clue = get_all_touched_cards(
            clue_type, clue_value, self.variant_name
        )
        good_card_indices = [
            i
            for i in range(len(self.hands[target_index]))
            if not self.is_trash_card(self.hands[target_index][i])
        ]
        candidates_list = self.all_candidates_list[target_index]
        score = 1

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

    def get_hat_residue(
        self,
        clue_giver: int,
        target_index: int,
        clue_type: int,
        clue_value: int,
        card_orders,
    ):
        num_residues = self.num_residues_per_player
        rightmost_unnumbered = self.get_rightmost_unnumbered_card(target_index)
        rightmost_uncolored = self.get_rightmost_uncolored_card(target_index)

        clue_mappings = self.get_special_hat_clues(target_index, clue_mapping_only=True)
        if clue_mappings is not None:
            for raw_residue, clue_type_values in clue_mappings.items():
                for _type, _value in clue_type_values:
                    if clue_type == _type and clue_value == _value:
                        return (
                            raw_residue
                            + ((target_index - clue_giver - 1) % self.num_players)
                            * num_residues
                        )

        if num_residues == 4:
            if clue_type == RANK_CLUE:
                if is_brownish_pinkish(self.variant_name):
                    raw_residue = 0 if clue_value in {1, 3, 5} else 1
                else:
                    if rightmost_unnumbered is None:
                        all_ranks_clued = []
                        for card in self.hands[target_index]:
                            all_ranks_clued += self.rank_clued_card_orders[card.order]

                        if clue_value == min(all_ranks_clued):
                            raw_residue = 0
                        elif clue_value == max(all_ranks_clued):
                            raw_residue = 1
                        else:
                            raise IndentationError
                    else:
                        if rightmost_unnumbered.order in card_orders:
                            raw_residue = 0
                        else:
                            raw_residue = 1
            elif clue_type == COLOR_CLUE:
                if is_whiteish_rainbowy(self.variant_name):
                    num_colors = len(get_available_color_clues(self.variant_name))
                    if num_colors in {2, 4, 5, 6}:
                        raw_residue = 2 if clue_value % 2 == 0 else 3
                    else:
                        raise NotImplementedError
                else:
                    if rightmost_uncolored is None:
                        all_colors_clued = []
                        for card in self.hands[target_index]:
                            all_colors_clued += self.color_clued_card_orders[card.order]

                        if clue_value == min(all_colors_clued):
                            raw_residue = 2
                        elif clue_value == max(all_colors_clued):
                            raw_residue = 3
                        else:
                            raise IndentationError
                    else:
                        if rightmost_uncolored.order in card_orders:
                            raw_residue = 2
                        else:
                            raw_residue = 3
            else:
                raise ImportError
        elif num_residues == 3:
            raise NotImplementedError
        else:
            raise NotImplementedError

        return (
            raw_residue
            + ((target_index - clue_giver - 1) % self.num_players) * num_residues
        )

    def get_good_actions(self, player_index: int) -> Dict[str, List[int]]:
        raise NotImplementedError

    def write_note(self, order: int, note: str, candidates=None, append=True):
        if order in self.trashy_orders:
            super().write_note(order=order, note="[kt]", candidates=None, append=append)
            return

        super().write_note(order=order, note=note, candidates=candidates, append=append)


class EncoderV2GameState(BaseEncoderGameState):
    def __init__(self, variant_name, player_names, our_player_index):
        super().__init__(variant_name, player_names, our_player_index, get_v2_mod_table)
        self.ambiguous_residue_orders: Set[int] = set()

    @property
    def should_interpret_hat_clue(self) -> bool:
        return self.clue_tokens < 8

    def get_hat_clue_target(self, player_index) -> Tuple[Optional[Card], bool]:
        # return_type: (card, is_in_ambiguous_orders)
        left_non_hat_clued = self.get_leftmost_non_hat_clued_card(player_index)

        if 0.3 <= self.score_pct < 0.6:
            for i in range(len(self.hands[player_index])):
                card = self.hands[player_index][-i - 1]
                if card.order in self.ambiguous_residue_orders:
                    return card, True

            if left_non_hat_clued is not None:
                return left_non_hat_clued, False
        else:
            if left_non_hat_clued is not None:
                return left_non_hat_clued, False

            for i in range(len(self.hands[player_index])):
                card = self.hands[player_index][-i - 1]
                if card.order in self.ambiguous_residue_orders:
                    return card, True

        return None, False

    def get_nonglobal_candidates(self, player_index, identities, new_candidates):
        nonglobal_candidates = set()
        player_singletons = [
            list(self.all_candidates_list[player_index][i])[0]
            for i in range(len(self.hands[player_index]))
            if len(self.all_candidates_list[player_index][i]) == 1
        ]
        other_singletons = [
            list(self.all_candidates_list[pindex][i])[0]
            for pindex in range(self.num_players)
            for i in range(len(self.hands[pindex]))
            if len(self.all_candidates_list[pindex][i]) == 1 and pindex != player_index
        ]
        if len(player_singletons) or len(other_singletons):
            print("Player SINGLETONS", player_singletons)
            print("Other SINGLETONS", other_singletons)

        for suit_index, rank in identities:
            if (suit_index, rank) not in self.max_num_cards:
                continue
            num_singletons_held = player_singletons.count(
                (suit_index, rank)
            ) + other_singletons.count((suit_index, rank))
            num_discarded = self.discards.get((suit_index, rank), 0)
            max_num_cards = self.max_num_cards[(suit_index, rank)]
            if (
                (suit_index, rank) not in new_candidates
                and num_discarded + num_singletons_held < max_num_cards
            ):
                nonglobal_candidates.add((suit_index, rank))

        if len(nonglobal_candidates):
            print(
                f"{self.our_player_name} {player_index} NONGLOBAL CANDIDATES",
                nonglobal_candidates,
            )
        return nonglobal_candidates

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
        if not self.should_interpret_hat_clue:
            self.track_clued_cards(clue_type, clue_value, card_orders)
            return touched_cards

        order_to_index = self.order_to_index
        identity_to_residue = self.identity_to_residue
        residue_to_identities = self.residue_to_identities
        hat_residue = self.get_hat_residue(
            clue_giver, target_index, clue_type, clue_value, card_orders
        )

        sum_of_others_residues = 0
        for player_index, hand in self.hands.items():
            if player_index in {self.our_player_index, clue_giver}:
                continue

            hat_clue_target, is_ambig = self.get_hat_clue_target(player_index)
            if hat_clue_target is None:
                continue

            _, i = order_to_index[hat_clue_target.order]
            candidates = self.all_candidates_list[player_index][i]
            if is_ambig:
                other_res = 0
                if hat_clue_target.order in self.ambiguous_residue_orders:
                    card_res = (
                        1
                        + hat_clue_target.suit_index
                        + (hat_clue_target.rank - 1) * len(SUITS[self.variant_name])
                    )
                    other_res = card_res % self.mod_base
                    new_candidates = candidates.intersection(
                        {
                            (suit_index, rank)
                            for (suit_index, rank) in get_all_cards(self.variant_name)
                            if (
                                1
                                + suit_index
                                + (rank - 1) * len(SUITS[self.variant_name])
                                - other_res
                            )
                            % self.mod_base
                            == 0
                        }
                    )
                    self.ambiguous_residue_orders.remove(hat_clue_target.order)
            else:
                other_res = identity_to_residue[hat_clue_target.to_tuple()]
                new_candidates = candidates.intersection(
                    residue_to_identities[other_res]
                )
                if len(residue_to_identities[other_res].difference(self.trash)) >= 3:
                    self.ambiguous_residue_orders.add(hat_clue_target.order)

            nonglobal_candidates = self.get_nonglobal_candidates(
                player_index, residue_to_identities[other_res], new_candidates
            )
            if len(new_candidates):
                self.all_candidates_list[player_index][i] = new_candidates
                note = f" ({other_res})"
                if hat_clue_target.order in self.ambiguous_residue_orders:
                    note += " [?]"
                self.write_note(
                    hat_clue_target.order, note=note, candidates=new_candidates
                )
                self.hat_clued_card_orders.add(hat_clue_target.order)
            else:
                self.write_note(
                    hat_clue_target.order, note="someone gave a bad hat clue"
                )

            player_name = self.player_names[player_index]
            print(f"{player_name} {hat_clue_target} has residue {other_res}")
            sum_of_others_residues += other_res

        if self.our_player_index != clue_giver:
            my_residue = (hat_residue - sum_of_others_residues) % self.mod_base
            print(f"My ({self.our_player_name})) residue = {my_residue}.")
            my_hat_target, my_is_ambig = self.get_hat_clue_target(self.our_player_index)
            if my_hat_target is None:
                return super().handle_clue(
                    clue_giver, target_index, clue_type, clue_value, card_orders
                )

            _, my_i = order_to_index[my_hat_target.order]
            my_candidates = self.our_candidates[my_i]
            if my_is_ambig:
                fillin_candidates = {
                    (suit_index, rank)
                    for (suit_index, rank) in get_all_cards(self.variant_name)
                    if (
                        1
                        + suit_index
                        + (rank - 1) * len(SUITS[self.variant_name])
                        - my_residue
                    )
                    % self.mod_base
                    == 0
                }
                print(f"Fill-in candidates: {fillin_candidates}")
                new_candidates = my_candidates.intersection(fillin_candidates)
                self.ambiguous_residue_orders.remove(my_hat_target.order)
            else:
                print(f"Hat candidates: {residue_to_identities[my_residue]}")
                new_candidates = my_candidates.intersection(
                    residue_to_identities[my_residue]
                )
                if len(residue_to_identities[my_residue].difference(self.trash)) >= 3:
                    self.ambiguous_residue_orders.add(my_hat_target.order)

            my_nonglobal_candidates = self.get_nonglobal_candidates(
                self.our_player_index, residue_to_identities[my_residue], new_candidates
            )
            if len(new_candidates):
                self.all_candidates_list[self.our_player_index][my_i] = new_candidates
                note = f" ({my_residue})"
                if my_hat_target.order in self.ambiguous_residue_orders:
                    note += " [?]"
                self.write_note(
                    my_hat_target.order, note=note, candidates=new_candidates
                )
                self.hat_clued_card_orders.add(my_hat_target.order)
            else:
                self.write_note(my_hat_target.order, note="someone gave a bad hat clue")

        self.track_clued_cards(clue_type, clue_value, card_orders)
        return touched_cards

    def get_legal_clues(self) -> Dict[Tuple[int, int, int], Set[Tuple[int, int]]]:
        # (clue_value, clue_type, target_index) -> cards_touched
        if not self.should_interpret_hat_clue:
            return self.get_all_possible_clues_dict()

        sum_of_residues = 0
        identity_to_residue = self.identity_to_residue
        for player_index, hand in self.hands.items():
            if player_index == self.our_player_index:
                continue

            hat_target, is_ambig = self.get_hat_clue_target(player_index)
            if hat_target is None:
                continue

            if is_ambig:
                card_res = (
                    1
                    + hat_target.suit_index
                    + (hat_target.rank - 1) * len(SUITS[self.variant_name])
                )
                sum_of_residues += card_res % self.mod_base
            else:
                sum_of_residues += identity_to_residue[hat_target.to_tuple()]

        sum_of_residues = sum_of_residues % self.mod_base
        return self.get_legal_clues_helper(sum_of_residues)

    def get_good_actions(self, player_index: int) -> Dict[str, List[int]]:
        all_other_players_cards = self.get_all_other_players_cards(player_index)
        all_op_hat_clued_cards = self.get_all_other_players_hat_clued_cards(
            player_index, no_singletons=False
        )
        hand = self.hands[player_index]
        candidates_list = self.all_candidates_list[player_index]

        playable = [
            hand[i].order
            for i, candidates in enumerate(candidates_list)
            if self.is_playable(candidates)
        ]
        trash = [
            hand[i].order
            for i, candidates in enumerate(candidates_list)
            if self.is_trash(candidates)
        ]
        yoloable = []
        for i, candidates in enumerate(candidates_list):
            if hand[i].order not in self.hat_clued_card_orders:
                # don't yolo cards we haven't explicitly touched lol
                continue

            if self.is_trash(candidates):
                continue

            if self.is_playable(candidates.difference(self.trash)):
                yoloable.append(hand[i].order)

        dupe_in_own_hand = []
        dupe_in_other_hand = []
        dupe_in_other_hand_or_trash = []
        seen_in_other_hand = []

        fully_knowns = self.get_fully_known_card_orders(player_index)
        for _, orders in fully_knowns.items():
            if len(orders) > 1:
                dupe_in_own_hand += orders[1:]

        for i, candidates in enumerate(candidates_list):
            if not len(candidates.difference(all_op_hat_clued_cards)):
                dupe_in_other_hand.append(hand[i].order)
            elif not len(
                candidates.difference(all_op_hat_clued_cards.union(self.trash))
            ):
                dupe_in_other_hand_or_trash.append(hand[i].order)
            elif not len(candidates.difference(all_other_players_cards)):
                seen_in_other_hand.append(hand[i].order)

        return {
            "playable": playable,
            "trash": trash,
            "yoloable": yoloable,
            "dupe_in_own_hand": dupe_in_own_hand,
            "dupe_in_other_hand": dupe_in_other_hand,
            "dupe_in_other_hand_or_trash": dupe_in_other_hand_or_trash,
            "seen_in_other_hand": seen_in_other_hand,
        }


class EncoderV1GameState(BaseEncoderGameState):
    def __init__(self, variant_name, player_names, our_player_index):
        super().__init__(variant_name, player_names, our_player_index, get_v1_mod_table)
        self.superpositions: Dict[int, SuperPosition] = {}  # order -> SuperPosition
        self.identities_called_to_play: Set[Tuple[int, int]] = set()
        self.play_order_queue: List[int] = []

    @property
    def can_clue_dupes_as_plays(self) -> bool:
        return self.score_pct >= 0.66 and self.pace <= self.num_players - 1

    def handle_play(self, player_index: int, order: int, suit_index: int, rank: int):
        if (suit_index, rank) in self.identities_called_to_play:
            self.identities_called_to_play.remove((suit_index, rank))

        order_to_index = self.order_to_index
        rewrite_note = False
        for sp_order, superposition in self.superpositions.items():
            _, i = order_to_index[sp_order]
            if order in superposition.triggering_orders:
                superposition.triggering_orders.remove(order)

            removed_trash_orders = set()
            for maybe_trash_order in superposition.triggering_orders:
                maybe_trash_card = self.get_card(maybe_trash_order)
                mt_id = (maybe_trash_card.suit_index, maybe_trash_card.rank)
                if self.is_trash_card(maybe_trash_card) or mt_id == (suit_index, rank):
                    removed_trash_orders.add(maybe_trash_order)

            for trash_order in removed_trash_orders:
                # trash is only "unexpected" if we played it
                if (player_index == self.our_player_index) and (
                    order in self.hat_clued_card_orders
                    and order in self.superpositions
                    and not self.can_clue_dupes_as_plays
                ):
                    superposition.unexpected_trash += 1
                    rewrite_note = True
                else:
                    print("A player with known duped card played it")
                superposition.triggering_orders.remove(trash_order)

            if len(removed_trash_orders):
                new_candidates = superposition.get_sp_identities()
                print(
                    self.our_player_name, i, sp_order, "New candidates", new_candidates
                )
                self.our_candidates[i] = self.our_possibilities[i].intersection(
                    new_candidates
                )
                if superposition.get_updated_residue(self.mod_base) == 0:
                    self.trashy_orders.append(sp_order)
                else:
                    if sp_order in self.trashy_orders:
                        self.trashy_orders.remove(sp_order)

                if superposition.get_updated_residue(self.mod_base) == 1:
                    self.play_order_queue.append(sp_order)
                    print(f"Updated play order queue (play): {self.play_order_queue}")

                if rewrite_note:
                    self.write_note(
                        sp_order, note="", candidates=self.our_candidates[i]
                    )

        if order in self.play_order_queue:
            self.play_order_queue = [x for x in self.play_order_queue if x != order]
            print(f"Deleted {order} from play order queue: {self.play_order_queue}")

        if order in self.superpositions:
            del self.superpositions[order]

        return super().handle_play(player_index, order, suit_index, rank)

    def handle_discard(self, player_index: int, order: int, suit_index: int, rank: int):
        order_to_index = self.order_to_index
        rewrite_note = False
        for sp_order, superposition in self.superpositions.items():
            _, i = order_to_index[sp_order]
            other_hc_orders_w_discarded_identity = {
                card.order
                for i in range(self.num_players)
                for card in self.hands[i]
                if (i != self.our_player_index)
                and card.to_tuple() == (suit_index, rank)
                and card.order in self.hat_clued_card_orders
            }
            if order in superposition.triggering_orders:
                if len(other_hc_orders_w_discarded_identity) == 1:
                    superposition.unexpected_trash += 1
                    rewrite_note = True
                superposition.triggering_orders.remove(order)
                new_candidates = superposition.get_sp_identities()
                self.our_candidates[i] = self.our_possibilities[i].intersection(
                    new_candidates
                )
                if superposition.get_updated_residue(self.mod_base) == 0:
                    self.trashy_orders.append(sp_order)
                else:
                    if sp_order in self.trashy_orders:
                        self.trashy_orders.remove(sp_order)

                if superposition.get_updated_residue(self.mod_base) == 1:
                    self.play_order_queue.append(sp_order)
                    print(f"Updated play order queue (disc): {self.play_order_queue}")

                if rewrite_note:
                    self.write_note(
                        sp_order, note="", candidates=self.our_candidates[i]
                    )

        if order in self.play_order_queue:
            self.play_order_queue = [x for x in self.play_order_queue if x != order]
            print(f"Deleted {order} from play order queue: {self.play_order_queue}")

        if order in self.superpositions:
            del self.superpositions[order]

        return super().handle_discard(player_index, order, suit_index, rank)

    def handle_clue(
        self,
        clue_giver: int,
        target_index: int,
        clue_type: int,
        clue_value: int,
        card_orders,
    ):
        order_to_index = self.order_to_index
        identity_to_residue = self.identity_to_residue
        residue_to_identities = self.residue_to_identities
        hat_residue = self.get_hat_residue(
            clue_giver, target_index, clue_type, clue_value, card_orders
        )
        triggering_orders = set()

        sum_of_others_residues = 0
        print(f"Identities called to play: {self.identities_called_to_play}")
        for player_index, hand in self.hands.items():
            if player_index in {self.our_player_index, clue_giver}:
                continue

            left_non_hat_clued = self.get_leftmost_non_hat_clued_card(player_index)
            if left_non_hat_clued is None:
                continue

            identity = left_non_hat_clued.to_tuple()
            if self.is_playable_card(left_non_hat_clued):
                triggering_orders.add(left_non_hat_clued.order)
                if (
                    identity in self.identities_called_to_play
                    and not self.can_clue_dupes_as_plays
                ):
                    other_residue = 0
                else:
                    other_residue = identity_to_residue[identity]
                    self.identities_called_to_play.add(identity)
            else:
                other_residue = identity_to_residue[identity]

            print(
                f"{self.player_names[player_index]} {left_non_hat_clued} "
                f"has residue {other_residue}."
            )
            sum_of_others_residues += other_residue

            _, i = order_to_index[left_non_hat_clued.order]
            implied_ids = residue_to_identities.get(other_residue, set())
            if other_residue == 0:
                implied_ids = implied_ids.union(self.identities_called_to_play)

            new_candidates = self.all_candidates_list[player_index][i].intersection(
                implied_ids
            )

            if len(new_candidates):
                self.all_candidates_list[player_index][i] = new_candidates

                self.write_note(
                    left_non_hat_clued.order, note="", candidates=new_candidates
                )
                self.hat_clued_card_orders.add(left_non_hat_clued.order)
            else:
                self.write_note(
                    left_non_hat_clued.order,
                    note="someone messed up and gave a bad hat clue",
                )

        if self.our_player_index != clue_giver:
            left_non_hat_clued = self.get_leftmost_non_hat_clued_card(
                self.our_player_index
            )

            if left_non_hat_clued is not None:
                my_residue = (hat_residue - sum_of_others_residues) % self.mod_base
                my_implied_ids = residue_to_identities.get(my_residue, set())
                if my_residue == 0:
                    my_implied_ids = my_implied_ids.union(
                        self.identities_called_to_play
                    )
                    self.trashy_orders.append(left_non_hat_clued.order)
                else:
                    if left_non_hat_clued.order in self.trashy_orders:
                        self.trashy_orders.remove(left_non_hat_clued.order)

                if my_residue == 1:
                    self.play_order_queue.append(left_non_hat_clued.order)
                    print(f"Updated play order queue (clue): {self.play_order_queue}")

                print(f"My ({self.our_player_name}) residue = {my_residue}.")
                print(f"Hat candidates: {my_implied_ids}")

                increment_candidates = {
                    i: residue_to_identities.get(
                        (my_residue + i) % self.mod_base, set()
                    ).union(
                        self.identities_called_to_play
                        if ((my_residue + i) % self.mod_base == 0)
                        else set()
                    )
                    for i in range(4)
                }

                self.superpositions[left_non_hat_clued.order] = SuperPosition(
                    my_residue, increment_candidates, triggering_orders
                )
                _, i = order_to_index[left_non_hat_clued.order]
                new_candidates = self.all_candidates_list[self.our_player_index][
                    i
                ].intersection(my_implied_ids)
                self.all_candidates_list[self.our_player_index][i] = new_candidates
                self.write_note(
                    left_non_hat_clued.order, note="", candidates=new_candidates
                )
                self.hat_clued_card_orders.add(left_non_hat_clued.order)

        return super().handle_clue(
            clue_giver, target_index, clue_type, clue_value, card_orders
        )

    def get_legal_clues(self) -> Dict[Tuple[int, int, int], Set[Tuple[int, int]]]:
        # (clue_value, clue_type, target_index) -> cards_touched
        sum_of_residues = 0
        identity_to_residue = self.identity_to_residue
        local_identities_called_to_play = deepcopy(self.identities_called_to_play)
        for player_index, hand in self.hands.items():
            if player_index == self.our_player_index:
                continue
            lnhc = self.get_leftmost_non_hat_clued_card(player_index)
            if lnhc is None:
                continue

            identity = lnhc.to_tuple()
            if self.is_playable_card(lnhc):
                if identity in local_identities_called_to_play and (
                    not self.can_clue_dupes_as_plays
                ):
                    sum_of_residues += 0
                else:
                    sum_of_residues += identity_to_residue[identity]
                    local_identities_called_to_play.add(identity)
            else:
                sum_of_residues += identity_to_residue[identity]

        sum_of_residues = sum_of_residues % self.mod_base
        return self.get_legal_clues_helper(sum_of_residues)

    def get_good_actions(self, player_index: int) -> Dict[str, List[int]]:
        all_other_players_cards = self.get_all_other_players_cards(player_index)
        all_op_unknown_hat_clued_cards = self.get_all_other_players_hat_clued_cards(
            player_index, no_singletons=True
        )
        hand = self.hands[player_index]
        candidates_list = self.all_candidates_list[player_index]

        trash = sorted(
            [
                hand[i].order
                for i, candidates in enumerate(candidates_list)
                if self.is_trash(candidates) or hand[i].order in self.trashy_orders
            ]
        )
        playable = []
        for i, candidates in enumerate(candidates_list):
            if self.is_trash(candidates):
                continue

            if hand[i].order in self.trashy_orders and len(candidates) > 1:
                continue

            if (
                self.is_playable(candidates.difference(self.trash))
                and hand[i].order in self.hat_clued_card_orders
            ):
                playable.append(hand[i].order)
                continue

            if self.is_playable(candidates):
                playable.append(hand[i].order)

        dupe_in_own_hand = []
        dupe_in_other_hand = []
        dupe_in_other_hand_or_trash = []
        seen_in_other_hand = []

        fully_knowns = self.get_fully_known_card_orders(player_index)
        for _, orders in fully_knowns.items():
            if len(orders) > 1:
                dupe_in_own_hand += orders[1:]

        for i, candidates in enumerate(candidates_list):
            # only count unknown hat clued cards for the purposes of determining "dupedness"
            if not len(candidates.difference(all_op_unknown_hat_clued_cards)):
                dupe_in_other_hand.append(hand[i].order)
            elif not len(
                candidates.difference(all_op_unknown_hat_clued_cards.union(self.trash))
            ):
                dupe_in_other_hand_or_trash.append(hand[i].order)
            elif not len(candidates.difference(all_other_players_cards)):
                seen_in_other_hand.append(hand[i].order)

        return {
            "playable": playable,
            "trash": trash,
            "dupe_in_own_hand": dupe_in_own_hand,
            "dupe_in_other_hand": dupe_in_other_hand,
            "dupe_in_other_hand_or_trash": dupe_in_other_hand_or_trash,
            "seen_in_other_hand": seen_in_other_hand,
        }
