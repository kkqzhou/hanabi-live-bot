import json
import websocket

from constants import ACTION, COLOR_CLUE, RANK_CLUE
from game_state import GameState
from conventions.encoder import EncoderV1GameState, EncoderV2GameState
from conventions.h_group import HGroupGameState
from conventions.ref_sieve import RefSieveGameState
from conventions.reactor import ReactorGameState
import traceback
from typing import Dict, Type


def is_int(x):
    try:
        int(x)
        return True
    except Exception:
        return False


class HanabiClient:
    def __init__(
        self,
        url,
        cookie,
        bot_to_join: str,
        convention: str,
        disconnect_on_game_end: bool,
        table_name: str,
        max_num_players: int
    ):
        self.bot_to_join = bot_to_join
        self.convention_name = (
            convention.replace("_", "").replace("-", "").replace(" ", "").lower()
        )
        self.game_state_cls: Type[GameState] = {
            "encoderv1": EncoderV1GameState,
            "encoderv2": EncoderV2GameState,
            "hgroup": HGroupGameState,
            "refsieve": RefSieveGameState,
            "reactor": ReactorGameState,
        }[self.convention_name]
        self.disconnect_on_game_end = disconnect_on_game_end
        self.table_name = table_name
        self.max_num_players = max_num_players

        # Initialize all class variables
        self.commandHandlers = {}
        self.tables = {}
        self.username = ""
        self.ws = None
        self.action_time = False
        self.everyone_connected = False
        self.games: Dict[int, GameState] = {}

        # Initialize the website command handlers (for the lobby)
        self.commandHandlers["welcome"] = self.welcome
        self.commandHandlers["warning"] = self.warning
        self.commandHandlers["error"] = self.error
        self.commandHandlers["chat"] = self.chat
        self.commandHandlers["table"] = self.table
        self.commandHandlers["tableList"] = self.table_list
        self.commandHandlers["tableGone"] = self.table_gone
        self.commandHandlers["tableStart"] = self.table_start

        # Initialize the website command handlers (for the game)
        self.commandHandlers["init"] = self.init
        self.commandHandlers["gameAction"] = self.game_action
        self.commandHandlers["gameActionList"] = self.game_action_list
        self.commandHandlers["databaseID"] = self.database_id
        self.commandHandlers["connected"] = self.connected
        self.commandHandlers["clock"] = self.clock
        self.commandHandlers["user"] = self.user
        self.commandHandlers["noteListPlayer"] = self.note_list_player
        self.commandHandlers["chatTyping"] = self.chat_typing

        # Start the WebSocket client
        print(f'Connecting to "{url}".')

        self.ws = websocket.WebSocketApp(
            url,
            on_message=lambda ws, message: self.websocket_message(ws, message),
            on_error=lambda ws, error: self.websocket_error(ws, error),
            on_open=lambda ws: self.websocket_open(ws),
            on_close=lambda ws: self.websocket_close(ws),
            cookie=cookie,
        )
        self.ws.run_forever()

    def websocket_message(self, ws, message):
        # WebSocket messages from the server come in the format of:
        # commandName {"field_name":"value"}
        # For more information, see:
        # https://github.com/Hanabi-Live/hanabi-live/blob/main/server/src/actions.go
        result = message.split(" ", 1)  # Split it into two things
        if len(result) != 1 and len(result) != 2:
            print("error: received an invalid WebSocket message:")
            print(message)
            return

        command = result[0]
        try:
            data = json.loads(result[1])
        except:
            print(f'error: the JSON data for the command of "{command}" was invalid')
            return

        if command in self.commandHandlers:
            if command not in {"gameAction", "clock", "warning", "user"}:
                print('debug: got command "' + command + '"')

            try:
                self.commandHandlers[command](data)
            except Exception as e:
                en = e.__class__.__name__
                print("**************************\n" * 3)
                print(f'error: command handler for "{command}" raised {en}, details:\n')
                traceback.print_exc()
                print("**************************\n" * 3)
                return
        else:
            print(f'debug: ignoring command "{command}"')

    def websocket_error(self, ws, error):
        print(f"Encountered a WebSocket error ({error.__class__.__name__}), details:")
        print(error)

    def websocket_close(self, ws):
        print("WebSocket connection closed.")

    def websocket_open(self, ws):
        print("Successfully established WebSocket connection.")

    # --------------------------------
    # Website Command Handlers (Lobby)
    # --------------------------------

    def welcome(self, data):
        # The "welcome" message is the first message that the server sends us
        # once we have established a connection
        # It contains our username, settings, and so forth
        self.username = data["username"]
        if self.bot_to_join == "create":
            self.chat_create_table()

    def error(self, data):
        # Either we have done something wrong,
        # or something has gone wrong on the server
        print(data)

    def warning(self, data):
        # We have done something wrong
        print(data)

    def chat(self, data):
        # We only care about private messages
        if data["recipient"] != self.username:
            return

        # We only care about private messages that start with a forward slash
        if not data["msg"].startswith("/"):
            return

        args = data["msg"][1:].split(" ")
        command = args[0]

        if command == "join":
            player_name = args[1] if len(args) > 1 else None
            self.chat_join(data, player_name)
        elif command == "create":
            self.chat_create_table()
        elif command == "start":
            self.chat_start()
        elif command in {"setvariant", "set_variant"}:
            variant_name = (
                (
                    args[1]
                    .replace("_", " ")
                    .replace("+", " & ")
                    .replace("6s", "(6 Suits)")
                    .replace("5s", "(5 Suits)")
                    .replace("4s", "(4 Suits)")
                    .replace("3s", "(3 Suits)")
                )
                if len(args) > 1
                else None
            )
            self.chat_set_variant(variant_name)
        elif command == "terminate":
            table_id = args[1] if len(args) > 1 else None
            self.chat_terminate(table_id)
        elif command == "reattend":
            table_id = args[1] if len(args) > 1 else 0
            self.chat_reattend(table_id)
        elif command == "restart":
            self.chat_restart()
        else:
            msg = "That is not a valid command."
            self.chat_reply(msg, data["who"])

    def chat_join(self, data, player_name=None):
        # Someone sent a private message to the bot and requested that we join
        # their game
        # Find the table that the current user is currently in
        table_id = None

        if is_int(player_name):
            self.send("tableJoin", {"tableID": int(player_name)})
            return

        if player_name is None:
            player_name = data.get("who", "")

        print(player_name)
        print("-----------")
        for table in self.tables.values():
            # Ignore games that have already started (and shared replays)
            if table["running"]:
                continue

            if player_name in table["players"]:
                if len(table["players"]) == 6:
                    msg = "Your game is full. Please make room for me before requesting that I join your game."
                    self.chat_reply(msg, data["who"])
                    return

                table_id = table["id"]
                break

        if table_id is None:
            msg = "Please create a table first before requesting that I join your game."
            self.chat_reply(msg, data["who"])
            return

        self.send("tableJoin", {"tableID": table_id})

    def chat_reattend(self, table_id: int):
        self.send("reattend", {"tableID": table_id})

    def chat_create_table(self):
        self.send(
            "tableCreate",
            {"name": self.table_name, "maxPlayers": self.max_num_players},
        )

    def chat_set_variant(self, variant_name: str):
        if variant_name is not None:
            for table in self.tables.values():
                if self.username in table["players"]:
                    self.send(
                        "tableSetVariant",
                        {
                            "tableID": table["id"],
                            "options": {"variantName": variant_name},
                        },
                    )

    def chat_start(self):
        for table in self.tables.values():
            if self.username in table["players"]:
                self.send("tableStart", {"tableID": table["id"]})

    def chat_restart(self):
        for table in self.tables.values():
            if self.username in table["players"]:
                self.s
                self.send("tableRestart", {"tableID": table["id"], "hidePregame": True})

    def chat_terminate(self, table_id=None):
        if table_id is None:
            for table in self.tables.values():
                if self.username in table["players"]:
                    table_id = table["id"]

        self.send("terminateTable", {"tableID": table_id})

    def table(self, data):
        self.tables[data["id"]] = data
        if (
            self.bot_to_join is not None
            and self.bot_to_join != "create"
            and self.bot_to_join in data["players"]
        ):
            self.send("tableJoin", {"tableID": data["id"]})

    def table_list(self, data_list):
        for data in data_list:
            self.table(data)

    def table_gone(self, data):
        del self.tables[data["tableID"]]

    def table_start(self, data):
        # The server has told us that a game that we are in is starting
        # So, the next step is to request some high-level information about the
        # game (e.g. number of players)
        # The server will respond with an "init" command
        self.send("getGameInfo1", {"tableID": data["tableID"]})

    # -------------------------------
    # Website Command Handlers (Game)
    # -------------------------------

    def init(self, data):
        print("Init data:")
        print(data)
        print()

        """
        {
            'tableID': 29600,
            'playerNames': ['yagami_green', 'yagami_light', 'yagami_blue'],
            'ourPlayerIndex': 2, 'spectating': False, 'shadowing': False, 'replay': False,
            'databaseID': -1, 'hasCustomSeed': False, 'seed': 'p3v177s1',
            'datetimeStarted': '2023-07-03T20:36:19.812308097Z', 'datetimeFinished': '0001-01-01T00:00:00Z',
            'options': {
                'numPlayers': 3, 'startingPlayer': 0, 'variantID': 0, 'variantName': 'Omni (5 Suits)',
                'timed': False, 'timeBase': 0, 'timePerTurn': 0, 'speedrun': False, 'cardCycle': False,
                'deckPlays': False, 'emptyClues': False, 'oneExtraCard': False, 'oneLessCard': False,
                'allOrNothing': False, 'detrimentalCharacters': False
            }, 'characterAssignments': [], 'characterMetadata': [], 'sharedReplay': False,
            'sharedReplayLeader': 'yagami_light', 'sharedReplaySegment': 0, 'sharedReplayEffMod': 0,
            'paused': False, 'pausePlayerIndex': -1, 'pauseQueued': False
        }
        """

        self.action_time = False
        self.everyone_connected = False

        # Make a new game state and store it on the "games" dictionary

        state = self.game_state_cls(
            variant_name=data["options"]["variantName"],
            player_names=data["playerNames"],
            our_player_index=data["ourPlayerIndex"],
        )
        self.games[data["tableID"]] = state

        # At this point, the JavaScript client would have enough information to
        # load and display the game UI; for our purposes, we do not need to
        # load a UI, so we can just jump directly to the next step
        # Now, we request the specific actions that have taken place thus far
        # in the game (which will come in a "gameActionList")
        self.send("getGameInfo2", {"tableID": data["tableID"]})

    def _go(self, data):
        if data["tableID"] not in self.games:
            print("NO STATE FOUND FOR TABLE ID = " + str(data["tableID"]) + "!")
            return

        state = self.games[data["tableID"]]
        if (
            (state.current_player_index == state.our_player_index)
            & self.action_time
            & self.everyone_connected
        ):
            print("Player " + str(state.our_player_index) + " DECIDING ACTION!")
            self.decide_action(data["tableID"])
            self.action_time = False

    def game_action(self, data):
        # We just received a new action for an ongoing game
        self.handle_action(data["action"], data["tableID"])
        self._go(data)

    def game_action_list(self, data):
        for action in data["list"]:
            self.handle_action(action, data["tableID"])

        # Let the server know that we have finished "loading the UI"
        # (so that our name does not appear as red / disconnected)
        self.send("loaded", {"tableID": data["tableID"]})
        self._go(data)

    def handle_action(self, data, table_id):
        _type = data["type"]
        print(f'debug: got a game action of "{_type}" for table {table_id}: {data}')

        # Local variables
        state = self.games[table_id]

        if data["type"] == "draw":
            card = state.handle_draw(
                data["playerIndex"], data["order"], data["suitIndex"], data["rank"]
            )

        elif data["type"] == "play":
            # state.print()
            state.handle_play(
                data["playerIndex"], data["order"], data["suitIndex"], data["rank"]
            )

        elif data["type"] == "discard":
            # state.print()
            state.handle_discard(
                data["playerIndex"], data["order"], data["suitIndex"], data["rank"]
            )

        elif data["type"] == "clue":
            # state.print()
            state.handle_clue(
                data["giver"],
                data["target"],
                data["clue"]["type"],
                data["clue"]["value"],
                data["list"],
            )

        elif data["type"] == "turn":
            state.turn = data["num"]
            state.current_player_index = data["currentPlayerIndex"]
            state.print()

        elif data["type"] == "strike":
            state.bombs = data["num"]
            state.handle_strike(data["order"])

        elif data["type"] == "status":
            state.clue_tokens = data["clues"]
            state.max_score = data["maxScore"]

        elif data["type"] == "gameOver":
            if self.disconnect_on_game_end:
                raise SystemExit

    def database_id(self, data):
        # Games are transformed into shared replays after they are completed
        # The server sends a "databaseID" message when the game has ended
        # Use this as a signal to leave the shared replay
        self.send(
            "tableUnattend",
            {
                "tableID": data["tableID"],
            },
        )

        # Delete the game state for the game to free up memory
        del self.games[data["tableID"]]

    def connected(self, data):
        print("Connected: " + str(data))
        self.everyone_connected = sum(data["list"]) == len(data["list"])
        print("self.everyone_connected = " + str(self.everyone_connected))
        state = self.games[data["tableID"]]
        if state.turn == 0 and self.everyone_connected:
            state.print()

    def clock(self, data):
        """
        {
            'tableID': 2345, 'times': [-2268, -1015, -1039], 'activePlayerIndex': 1,
            'timeTaken': 0
        }
        """
        self.action_time = True
        self._go(data)

    def user(self, data):
        """
        {
            'userID': 81697, 'name': 'kingCLUE', 'status': 0, 'tableID': 0,
            'hyphenated': False, 'inactive': False
        }
        """
        pass

    def note_list_player(self, data):
        print("Note List Player: " + str(data))

    def chat_typing(self, data):
        print("Chat Typing: ", str(data))
        self.action_time = True
        self._go(data)

    def play(self, order, table_id):
        print(f"Playing order: {order}")
        self.send("action", {"tableID": table_id, "type": ACTION.PLAY, "target": order})

    def discard(self, order, table_id):
        print(f"Discarding order: {order}")
        self.send(
            "action", {"tableID": table_id, "type": ACTION.DISCARD, "target": order}
        )

    def clue(self, target_index, clue_type, clue_value, table_id):
        _type = {COLOR_CLUE: ACTION.COLOR_CLUE, RANK_CLUE: ACTION.RANK_CLUE}[clue_type]
        print(f"Giving {_type._name_} with value {clue_value} to {target_index}")
        self.send(
            "action",
            {
                "tableID": table_id,
                "type": _type,
                "target": target_index,
                "value": clue_value,
            },
        )

    def write_note(self, table_id, order, note):
        self.send("note", {"tableID": table_id, "order": order, "note": note})

    def decide_action(self, table_id):
        # The server expects to be told about actions in the following format:
        # https://github.com/Hanabi-Live/hanabi-live/blob/main/server/src/command.go
        state = self.games[table_id]
        if isinstance(state, EncoderV1GameState):
            self.encoder_v1(state, table_id)
        elif isinstance(state, EncoderV2GameState):
            self.encoder_v2(state, table_id)
        elif isinstance(state, HGroupGameState):
            self.hgroup(state, table_id)
        elif isinstance(state, RefSieveGameState):
            self.ref_sieve(state, table_id)
        elif isinstance(state, ReactorGameState):
            self.reactor(state, table_id)
        else:
            raise ValueError(type(state))

        for order, note in state.notes.items():
            self.write_note(table_id, order, note)

    def hgroup(self, state: HGroupGameState, table_id: int):
        good_actions = {
            player_index: state.get_good_actions(player_index)
            for player_index in range(state.num_players)
        }
        my_good_actions = good_actions[state.our_player_index]
        next_player_good_actions = good_actions[state.next_player_index]
        print(f"{state.our_player_name} POV - good actions:")
        for player_index, orders in good_actions.items():
            print(player_index, orders)

        next_player_has_safe_action = False
        my_chop_order = state.get_chop_order(state.our_player_index)
        np_chop_order = state.get_chop_order(state.next_player_index)

        for action_type, orders in next_player_good_actions.items():
            if action_type == "seen_in_other_hand":
                # TODO: handle this at later levels
                continue
            if len(orders):
                next_player_has_safe_action = True
                break

        if not next_player_has_safe_action and state.clue_tokens >= 1:
            if np_chop_order is not None:
                np_chop = state.get_card(np_chop_order)
                if (np_chop.suit_index, np_chop.rank) in state.playables:
                    self.clue(
                        state.next_player_index,
                        COLOR_CLUE,
                        np_chop.suit_index,
                        table_id,
                    )
                    return
                elif (np_chop.suit_index, np_chop.rank) in state.criticals:
                    self.clue(
                        state.next_player_index, RANK_CLUE, np_chop.rank, table_id
                    )
                    return

        # play if nothing urgent to do
        if len(my_good_actions["playable"]):
            # sort playables by lowest possible rank of candidates
            sorted_playables = sorted(
                my_good_actions["playable"],
                key=lambda order: min([x[1] for x in state.get_candidates(order)]),
            )
            playable_fives = [
                order
                for order in my_good_actions["playable"]
                if min([x[1] for x in state.get_candidates(order)]) == 5
            ]
            if len(playable_fives):
                self.play(playable_fives[0], table_id)
                return

            unique_playables = [
                order
                for order in sorted_playables
                if order not in my_good_actions["dupe_in_other_hand"]
            ]
            if len(unique_playables):
                self.play(unique_playables[0], table_id)
                return

            # all the playables we have are duped in someone else's hand
            # figure out where the duped card is and how to best resolve it
            for playable_order in sorted_playables:
                playable_candidates = state.get_candidates(playable_order)
                if state.pace <= state.num_players - 2:
                    print("PACE IS TOO LOW, NEED TO PLAY!!!")
                    self.play(playable_order, table_id)
                    return

                if len(playable_candidates) >= 2:
                    print("IDK WHAT THIS IS BUT ITS DUPED")
                    self.discard(playable_order, table_id)
                    return

                suit_index, rank = list(playable_candidates)[0]
                for player_index, hand in state.hands.items():
                    if player_index == state.our_player_index:
                        continue

                    for i, card in enumerate(hand):
                        if (suit_index, rank) != (card.suit_index, card.rank):
                            continue

                        candidates = state.all_candidates_list[player_index][i]
                        candidates_minus_my_play = candidates.difference(
                            {(suit_index, rank)}
                        )
                        if state.is_trash(candidates_minus_my_play):
                            print("OTHER GUY WILL KNOW ITS TRASH AFTER I PLAY THIS")
                            self.play(playable_order, table_id)
                            return

                        what_other_guy_sees = state.get_all_other_players_clued_cards(
                            player_index
                        )
                        unique_candidates_after_my_play = (
                            candidates_minus_my_play.difference(what_other_guy_sees)
                        )
                        if not len(unique_candidates_after_my_play) or state.is_trash(
                            unique_candidates_after_my_play
                        ):
                            print("OTHER GUY WILL KNOW ITS DUPED AFTER I PLAY THIS")
                            self.play(playable_order, table_id)
                            return

        if state.clue_tokens < 8:
            for trashable in [
                "trash",
                "dupe_in_own_hand",
                "dupe_in_other_hand",
                "dupe_in_other_hand_or_trash",
            ]:
                if len(my_good_actions[trashable]):
                    self.discard(my_good_actions[trashable][0], table_id)
                    return

            self.discard(my_chop_order, table_id)
            return

        if np_chop_order is not None:
            burn_clue_card = state.get_card(np_chop_order)
        else:
            burn_clue_card = state.hands[state.next_player_index][0]
        self.clue(state.next_player_index, RANK_CLUE, burn_clue_card.rank, table_id)

    def reactor(self, state: ReactorGameState, table_id: int):
        stable_clues = state.get_stable_clues()
        reactive_clues = state.get_reactive_clues()
        print('------------------')
        print('Players play/discard/chop:')
        for pindex in range(state.num_players):
            print(pindex, state.play_orders[pindex], state.discard_orders[pindex], state.get_chop_order(pindex))
        print('Play orders')
        print(state.play_orders)
        print('Discard orders')
        print(state.discard_orders)
        print('Unresolved reactions')
        print(state.unresolved_reactions)

        print('All stable clues:')
        for (clue_value, clue_type, target_index), y in stable_clues.items():
            assert y in {"SAFE_ACTION", "DIRECT_PLAY", "REF_PLAY", "REF_DISCARD", "LOCK"}
            print("COLOR" if clue_type == COLOR_CLUE else "RANK", clue_value, 'to', target_index, ':', y)

        print('All reactive clues:')
        for (clue_value, clue_type, target_index), y in reactive_clues.items():
            print("COLOR" if clue_type == COLOR_CLUE else "RANK", clue_value, 'to', target_index, ':', y)

        print('------------------')

        # TODO: fold into a function
        ur = state.unresolved_reactions[state.our_player_index]
        if ur is not None:
            target_index = ur.ordering[1]
            target_orders = ur.player_slot_orders[target_index]
            reacter_orders = ur.player_slot_orders[state.our_player_index]
            pslot = ur.get_reactive_playable_human_slot()
            tslot = ur.get_reactive_trash_human_slot()
            print(f'Responding to reactive where {target_index} is target')
            print(f'pslot = {pslot}, tslot = {tslot}')

            if ur.play_parity == 0:
                if pslot is not None:
                    reacter_slot = (ur.focused_slot - pslot - 1) % len(target_orders) + 1
                    order_to_play = reacter_orders[reacter_slot - 1]
                    print(f'!!1 Playing slot {reacter_slot}')
                    self.play(order_to_play, table_id)
                    state.unresolved_reactions[state.our_player_index] = None
                    return

                for reacter_slot in [1,5,4,3,2]:
                    order_to_play = reacter_orders[reacter_slot - 1]
                    order_to_play_candidates = state.get_candidates(order_to_play)
                    fslot = (ur.focused_slot - reacter_slot - 1) % len(target_orders) + 1
                    fcard = state.hands[target_index][-fslot]
                    if fcard.to_tuple() in state.one_away_from_playables:
                        if state.get_next_playable_card_tuple(fcard.suit_index) not in order_to_play_candidates:
                            continue
                        else:
                            print(f'!!2 Playing slot {reacter_slot}')
                            self.play(order_to_play, table_id)
                            state.unresolved_reactions[state.our_player_index] = None
                            return
                    
            elif ur.play_parity == 1:
                if pslot is not None:
                    reacter_slot = (ur.focused_slot - pslot - 1) % len(target_orders) + 1
                    order_to_discard = reacter_orders[reacter_slot - 1]
                    print(f'!!3 Discarding slot {reacter_slot}')
                    self.discard(order_to_discard, table_id)
                    state.unresolved_reactions[state.our_player_index] = None
                    return
                
                if tslot is not None:
                    reacter_slot = (ur.focused_slot - tslot - 1) % len(target_orders) + 1
                    order_to_play = reacter_orders[reacter_slot - 1]
                    print(f'!!4 Playing slot {reacter_slot}')
                    self.play(order_to_play, table_id)
                    state.unresolved_reactions[state.our_player_index] = None
                    return

        if len(state.our_play_orders):
            print(f'!!5 Playing order {state.our_play_orders[0]}')
            self.play(state.our_play_orders[0], table_id)
            return

        if len(state.our_discard_orders) and (state.clue_tokens < 8):
            print(f'!!6 Discarding order {state.our_discard_orders[0]}')
            self.discard(state.our_discard_orders[0], table_id)
            return

        if len(reactive_clues) and state.clue_tokens >= 2:
            for (clue_value, clue_type, target_index), clue_str in reactive_clues.items():
                if clue_str in {'2P0D_PLAY', '2P0D_FINESSE'}:
                    self.clue(target_index, clue_type, clue_value, table_id)
                    return
                
            for (clue_value, clue_type, target_index), clue_str in reactive_clues.items():
                if clue_str in {'1P1D_DISCARD', '1P1D_PLAY'}:
                    self.clue(target_index, clue_type, clue_value, table_id)
                    return
                
        if len(stable_clues) and state.clue_tokens >= 1:
            for (clue_value, clue_type, target_index), clue_str in stable_clues.items():
                if clue_str != 'LOCK':
                    self.clue(target_index, clue_type, clue_value, table_id)
                    return
        
        if (state.clue_tokens < 8):
            chop_order = state.get_chop_order(state.our_player_index)
            if chop_order is not None:
                self.discard(chop_order, table_id)
                return

        self.play(state.our_hand[-1].order, table_id)

    def ref_sieve(self, state: RefSieveGameState, table_id: int):
        ref_sieve_clues = state.get_ref_sieve_clues()
        print('Players play/discard/chop:')
        for pindex in range(state.num_players):
            print(pindex, state.play_orders[pindex], state.discard_orders[pindex], state.get_chop_order(pindex))

        print('All ref sieve clues:')
        for x, y in ref_sieve_clues.items():
            assert y in {"SAFE_ACTION", "DIRECT_PLAY", "REF_PLAY", "REF_DISCARD", "LOCK"}
            print(x, y)
        
        bob = state.next_player_index
        bob_chop_order = state.get_chop_order(bob)
        if bob_chop_order is not None:
            bob_chop_card = state.get_card(bob_chop_order)
            urgent_card_on_bobs_chop = (state.is_playable_card(bob_chop_card) and bob_chop_order not in state.clued_card_orders) or state.is_critical_card(bob_chop_card)
            bob_no_safe_actions = (
                len(state.play_orders[bob]) +
                len(state.discard_orders[bob]) == 0
            )
            clues_to_bob = {x: y for x, y in ref_sieve_clues.items() if x[-1] == bob}
            if (state.clue_tokens >= 1) and (state.num_cards_in_deck >= 2) and urgent_card_on_bobs_chop and bob_no_safe_actions:
                print('Bob has a crit/playable on chop and no safe actions!')
                play_clues_to_bob = [x for x, y in clues_to_bob.items() if y in {"DIRECT_PLAY", "REF_PLAY"}]
                safe_action_clues_to_bob = [x for x, y in clues_to_bob.items() if y in {"SAFE_ACTION"}]
                discard_clues_to_bob = [x for x, y in clues_to_bob.items() if y in {"REF_DISCARD"}]
                if len(play_clues_to_bob):
                    play_clues_ranked = sorted(
                        play_clues_to_bob, key=lambda x: state.evaluate_clue_score(x[0], x[1], x[2])
                    )
                    for clue_type, clue_value, target_index in play_clues_ranked:
                        self.clue(target_index, clue_type, clue_value, table_id)
                        return

                if len(safe_action_clues_to_bob):
                    clue_type, clue_value, _ = safe_action_clues_to_bob[0]
                    self.clue(bob, clue_type, clue_value, table_id)
                    return
                
                if len(discard_clues_to_bob):
                    # find a clue that gets rid of trash
                    for clue_type, clue_value, _ in discard_clues_to_bob:
                        discard_index = state.get_index_of_ref_discard_target(bob, clue_type, clue_value)
                        if discard_index is None:
                            continue

                        discard_target_card = state.hands[bob][discard_index]
                        touched_cards = state.get_touched_cards(clue_type, clue_value, bob)
                        newly_touched_cards = [card for card in touched_cards if card.order not in state.clued_card_orders]
                        does_not_bad_touch = True
                        for card in newly_touched_cards:
                            if state.is_weak_trash_card(card):
                                does_not_bad_touch = False
                        if does_not_bad_touch and state.is_weak_trash_card(discard_target_card):
                            print('Found kt to remove in Bobs hand!')
                            self.clue(bob, clue_type, clue_value, table_id)
                            return
                        
                    # otherwise find a clue that doesn't get rid of a crit
                    for clue_type, clue_value, _ in discard_clues_to_bob:
                        discard_index = state.get_index_of_ref_discard_target(bob, clue_type, clue_value)
                        if discard_index is None:
                            continue

                        discard_target_card = state.hands[bob][discard_index]
                        if not state.is_critical_card(discard_target_card):
                            print('No kt to remove in Bobs hand, saving crits instead')
                            self.clue(bob, clue_type, clue_value, table_id)
                            return

        if len(state.our_play_orders):
            self.play(state.our_play_orders[0], table_id)
            return
        
        play_clues = [x for x, y in ref_sieve_clues.items() if y in {"DIRECT_PLAY", "REF_PLAY"}]
        safe_action_clues = [x for x, y in ref_sieve_clues.items() if y in {"SAFE_ACTION"}]
        discard_clues = [x for x, y in ref_sieve_clues.items() if y in {"REF_DISCARD"}]
        lock_clues = [x for x, y in ref_sieve_clues.items() if y in {"LOCK"}]
        if (state.clue_tokens >= 2):
            print('Give some sort of useful clue')

            if len(play_clues):
                play_clues_ranked = sorted(
                    play_clues, key=lambda x: state.evaluate_clue_score(x[0], x[1], x[2])
                )
                for clue_type, clue_value, target_index in play_clues_ranked:
                    self.clue(target_index, clue_type, clue_value, table_id)
                    return
            
            if len(safe_action_clues):
                for clue_type, clue_value, target_index in safe_action_clues:
                    touched_cards = state.get_touched_cards(clue_type, clue_value, target_index)
                    newly_touched_cards = [card for card in touched_cards if card.order not in state.clued_card_orders]
                    for card in newly_touched_cards:
                        if state.is_weak_trash_card(card):
                            continue
                        
                        self.clue(target_index, clue_type, clue_value, table_id)
                        return
            
            if len(discard_clues):
                players_with_good_chops = [
                    pindex for pindex in range(state.num_players)
                    if pindex != state.our_player_index
                    and state.get_chop_order(pindex) is not None
                    and not state.is_weak_trash_card(state.get_card(state.get_chop_order(pindex)))
                ]
                good_discard_clues = [x for x in discard_clues if x[-1] in players_with_good_chops]
                for clue_type, clue_value, target_index in good_discard_clues:
                    discard_index = state.get_index_of_ref_discard_target(target_index, clue_type, clue_value)
                    if discard_index is None:
                        continue

                    discard_target_card = state.hands[target_index][discard_index]
                    touched_cards = state.get_touched_cards(clue_type, clue_value, target_index)
                    newly_touched_cards = [card for card in touched_cards if card.order not in state.clued_card_orders]
                    does_not_bad_touch = True
                    for card in newly_touched_cards:
                        if state.is_weak_trash_card(card):
                            does_not_bad_touch = False
                    if does_not_bad_touch and state.is_weak_trash_card(discard_target_card):
                        self.clue(target_index, clue_type, clue_value, table_id)
                        return

        if len(state.our_discard_orders):
            self.discard(state.our_discard_orders[0], table_id)
            return
        
        if (state.clue_tokens < 8):
            chop_order = state.get_chop_order(state.our_player_index)
            if chop_order is not None:
                self.discard(chop_order, table_id)
                return

        self.play(state.our_hand[-1].order, table_id)

    def encoder_v2(self, state: EncoderV2GameState, table_id: int):
        # ragequit
        if state.pace < 0 or state.max_score < 5 * len(state.stacks):
            self.play(state.our_hand[-1].order, table_id)
            return

        # TODO: implement elim
        good_actions = {
            player_index: state.get_good_actions(player_index)
            for player_index in range(state.num_players)
        }
        my_good_actions = good_actions[state.our_player_index]
        print(state.our_player_name + " good actions:")
        for action_type, orders in good_actions.items():
            print(action_type, orders)

        max_crits = 0
        for player_index in range(state.num_players):
            if player_index == state.our_player_index:
                continue
            num_crits = sum(
                [state.is_critical_card(card) for card in state.hands[player_index]]
            )
            max_crits = max(max_crits, num_crits)

        if state.cannot_play:
            print(f"CANNOT PLAY! {max_crits} crits > {state.num_cards_in_deck} cards")

        if len(my_good_actions["playable"]) and not state.cannot_play:
            # sort playables by lowest possible rank of candidates
            sorted_playables = sorted(
                my_good_actions["playable"],
                key=lambda order: min([x[1] for x in state.get_candidates(order)]),
            )
            num_crits_i_have = sum([state.is_critical(x) for x in state.our_candidates])

            # TODO: clean this up and put this into the encoder game state
            # priority 0
            fk_orders = state.get_fully_known_card_orders(
                state.our_player_index, keyed_on_order=True
            )
            for order in sorted_playables:
                if order in fk_orders:
                    identity = fk_orders[order]
                    next_playable = (identity[0], identity[1] + 1)
                    all_others_hc_cards = state.get_all_other_players_hat_clued_cards()
                    dire_circumstances = (
                        identity not in state.criticals
                        and num_crits_i_have > state.num_cards_in_deck
                    )
                    duped_in_another_hand = (
                        order in my_good_actions["dupe_in_other_hand"]
                        and state.num_cards_in_deck != 1
                    )
                    if dire_circumstances:
                        print(f"Would love to play {identity} but cannot")
                    elif duped_in_another_hand:
                        print(f"Not playing {identity} prio 0 when duped in other hand")

                    if (
                        next_playable in all_others_hc_cards
                        and not dire_circumstances
                        and not duped_in_another_hand
                    ):
                        print("PRIO 0")
                        self.play(order, table_id)
                        return

            # priority 1
            key_crits = [
                order
                for order in sorted_playables
                if state.is_critical(state.get_candidates(order))
                and max([x[1] for x in state.get_candidates(order)]) <= 3
            ]
            if len(key_crits):
                print("PRIO 1")
                self.play(key_crits[0], table_id)
                return

            # priority 2
            playable_fives = [
                order
                for order in my_good_actions["playable"]
                if min([x[1] for x in state.get_candidates(order)]) == 5
            ]
            if len(playable_fives):
                print("PRIO 2")
                self.play(playable_fives[0], table_id)
                return

            # priority 3
            unique_playables = [
                order
                for order in sorted_playables
                if order not in my_good_actions["dupe_in_other_hand"]
            ]
            if len(unique_playables):
                print("PRIO 3")
                self.play(unique_playables[0], table_id)
                return

            # all the playables we have are duped in someone else's hand
            # figure out where the duped card is and how to best resolve it
            for playable_order in sorted_playables:
                playable_candidates = state.get_candidates(playable_order)
                if len(playable_candidates) >= 2:
                    print("TOO MANY CANDIDATES TO WORRY ABOUT, PLAYING THIS")
                    self.play(playable_order, table_id)
                    return

                suit_index, rank = list(playable_candidates)[0]
                for player_index, hand in state.hands.items():
                    if player_index == state.our_player_index:
                        continue

                    for i, card in enumerate(hand):
                        if (suit_index, rank) != (card.suit_index, card.rank):
                            continue

                        candidates = state.all_candidates_list[player_index][i]
                        candidates_minus_my_play = candidates.difference(
                            {(suit_index, rank)}
                        )
                        if state.is_trash(candidates_minus_my_play):
                            print("OTHER GUY WILL KNOW ITS TRASH AFTER I PLAY THIS")
                            self.play(playable_order, table_id)
                            return

                        what_other_guy_sees = (
                            state.get_all_other_players_hat_clued_cards(player_index)
                        )
                        unique_candidates_after_my_play = (
                            candidates_minus_my_play.difference(what_other_guy_sees)
                        )
                        if not len(unique_candidates_after_my_play) or state.is_trash(
                            unique_candidates_after_my_play
                        ):
                            print("OTHER GUY WILL KNOW ITS DUPED AFTER I PLAY THIS")
                            self.play(playable_order, table_id)
                            return

                        if card.order in state.ambiguous_residue_orders:
                            print("THIS CARD IS IN AMB CARD ORDERS, WILL BE RESOLVED")
                            self.play(playable_order, table_id)
                            return

            if state.pace <= state.num_players - 2:
                print("PACE IS TOO LOW, NEED TO PLAY!!!")
                self.play(sorted_playables[0], table_id)
            elif state.clue_tokens >= 8:
                print("AT 8 TOKENS, CAN'T DISCARD!!!")
                self.play(sorted_playables[0], table_id)
            else:
                print("NO DUPES WILL DEFINITELY RESOLVE, GDing this instead")
                self.discard(sorted_playables[0], table_id)
            return

        cannot_yolo = (state.bombs > 1) and (state.pace >= 1)
        if (
            len(my_good_actions["yoloable"])
            and not cannot_yolo
            and not state.cannot_play
        ):
            self.play(my_good_actions["yoloable"][0], table_id)
            return

        if state.pace < 0 or state.num_cards_in_deck <= 0:
            for i in range(len(state.our_hand)):
                candidates = state.our_candidates[-i - 1]
                if len(candidates.intersection(state.playables)):
                    print("LAST RESORT PLAY")
                    self.play(state.our_hand[-i - 1].order, table_id)
                    return

        lnhcs = state.get_leftmost_non_hat_clued_cards()
        num_useful_cards = 0
        for card in lnhcs:
            if card is None:
                continue
            if (card.suit_index, card.rank) in state.trash:
                continue
            num_useful_cards += 1

        # clues that narrow down useful cards the most are good, lowest scores first
        legal_clues = state.get_legal_clues()
        legal_clue_to_score = {
            (clue_value, clue_type, target_index): state.evaluate_clue_score(
                clue_value, clue_type, target_index
            )
            for (clue_value, clue_type, target_index) in legal_clues
        }
        legal_hat_clues = sorted(legal_clue_to_score.items(), key=lambda x: x[-1])
        print("All legal clues available:")
        for x, score in legal_hat_clues:
            print(f"{x}: {score}")

        if state.clue_tokens >= 2:
            if 0 <= state.score_pct < 0.24:
                r = {2: 0.79, 3: 0.76, 4: 0.7, 5: 0.6, 6: 0.45, 7: 0.3, 8: 0.0}[
                    min(8, state.clue_tokens + max(0, 4 - state.pace))
                ]
                num_useful_cards_touched = int(r * min(4, state.num_players - 1))
            elif 0.24 <= state.score_pct < 0.48:
                r = {2: 0.7, 3: 0.67, 4: 0.6, 5: 0.48, 6: 0.36, 7: 0.2, 8: 0.0}[
                    min(8, state.clue_tokens + max(0, 4 - state.pace))
                ]
                num_useful_cards_touched = int(r * min(4, state.num_players - 1))
            elif 0.48 <= state.score_pct < 0.72:
                r = {2: 0.6, 3: 0.55, 4: 0.48, 5: 0.4, 6: 0.3, 7: 0.17, 8: 0.0}[
                    min(8, state.clue_tokens + max(0, 4 - state.pace))
                ]
                num_useful_cards_touched = int(r * min(4, state.num_players - 1))
            else:
                r = {2: 0.48, 3: 0.36, 4: 0.24, 5: 0.16, 6: 0.1, 7: 0.05, 8: 0.0}[
                    min(8, state.clue_tokens + max(0, 4 - state.pace))
                ]
                num_useful_cards_touched = int(r * min(4, state.num_players - 1))

            if num_useful_cards >= num_useful_cards_touched:
                for (clue_value, clue_type, target_index), _ in legal_hat_clues:
                    print(f"USEFUL CLUE! Score = {state.score_pct:.3f}, we see {lnhcs}")
                    self.clue(target_index, clue_type, clue_value, table_id)
                    return

        # basic stall in endgame
        if state.clue_tokens >= 1 and (state.pace < 3 or state.num_cards_in_deck == 1):
            for (clue_value, clue_type, target_index), _ in legal_hat_clues:
                print("STALL CLUE!")
                self.clue(target_index, clue_type, clue_value, table_id)
                return

        # basic stall in endgame
        if state.clue_tokens >= state.num_players and (
            state.num_cards_in_deck <= state.num_players / 2
        ):
            for (clue_value, clue_type, target_index), _ in legal_hat_clues:
                print("STALL CLUE 2!")
                self.clue(target_index, clue_type, clue_value, table_id)
                return

        # discard if nothing better to do
        if state.clue_tokens < 8:
            if len(my_good_actions["trash"]):
                print("X TRASH")
                self.discard(my_good_actions["trash"][0], table_id)
                return
            if len(my_good_actions["dupe_in_own_hand"]):
                print("X DUPE_IN_OWN_HAND")
                self.discard(my_good_actions["dupe_in_own_hand"][0], table_id)
                return
            if len(my_good_actions["dupe_in_other_hand"]):
                print("X DUPE_IN_OTHER_HAND")
                self.discard(my_good_actions["dupe_in_other_hand"][0], table_id)
                return
            if len(my_good_actions["dupe_in_other_hand_or_trash"]):
                print("X DUPE_IN_OTHER_HAND_OR_TRASH")
                self.discard(
                    my_good_actions["dupe_in_other_hand_or_trash"][0], table_id
                )
                return

        # unless we have no safe actions
        if state.clue_tokens >= 1 and len(legal_hat_clues):
            for (clue_value, clue_type, target_index), _ in legal_hat_clues:
                print("CLUE BECAUSE NO SAFE ACTION!")
                self.clue(target_index, clue_type, clue_value, table_id)
                return

        if state.clue_tokens < 8:
            if len(my_good_actions["seen_in_other_hand"]):
                print("DISCARDING CARD SEEN BUT NOT TOUCHED!")
                self.discard(my_good_actions["seen_in_other_hand"][0], table_id)
                return

            for i, candidates in enumerate(state.our_candidates):
                if state.our_hand[-i - 1].order not in state.hat_clued_card_orders:
                    print("SACRIFICING NON HAT CLUED SLOT " + str(i) + "!")
                    self.discard(state.our_hand[-i - 1].order, table_id)
                    return

            for i, candidates in enumerate(state.our_candidates):
                if (
                    not len(candidates.intersection(state.criticals))
                    or i == len(state.our_candidates) - 1
                ):
                    print("SACRIFICING SLOT " + str(len(state.our_hand) - i - 1) + "!")
                    self.discard(state.our_hand[i].order, table_id)
                    return
        else:
            for i, candidates in enumerate(state.our_candidates):
                if (
                    not len(candidates.intersection(state.criticals))
                    or i == len(state.our_candidates) - 1
                ):
                    print(
                        "STALL BOMBING SLOT " + str(len(state.our_hand) - i - 1) + "!"
                    )
                    self.play(state.our_hand[i].order, table_id)
                    return

    def encoder_v1(self, state: EncoderV1GameState, table_id: int):
        # TODO: implement elim
        good_actions = {
            player_index: state.get_good_actions(player_index)
            for player_index in range(state.num_players)
        }
        my_good_actions = good_actions[state.our_player_index]
        print(state.our_player_name + " good actions:")
        for action_type, orders in good_actions.items():
            print(action_type, orders)

        if state.cannot_play:
            print(f"CANNOT PLAY! someone's crits > {state.num_cards_in_deck} cards")

        if len(my_good_actions["playable"]) and not state.cannot_play:
            # sort playables by lowest possible rank of candidates
            sorted_playables = sorted(
                my_good_actions["playable"],
                key=lambda order: min([x[1] for x in state.get_candidates(order)]),
            )

            # priority 0
            fk_orders = state.get_fully_known_card_orders(
                state.our_player_index, keyed_on_order=True
            )
            for order in sorted_playables:
                if order in fk_orders:
                    identity = fk_orders[order]
                    next_playable = (identity[0], identity[1] + 1)
                    all_others_hc_cards = state.get_all_other_players_hat_clued_cards()
                    dire_circumstances = (
                        identity not in state.criticals
                        and state.our_num_crits > state.num_cards_in_deck
                    )
                    if dire_circumstances:
                        print(f"Would love to play {identity} but cannot")

                    prefer_not_to_play = (
                        state.no_urgency
                        and order in my_good_actions["dupe_in_other_hand"]
                    )
                    if prefer_not_to_play:
                        print(f"Prefer not to play {identity} as top priority")

                    if next_playable in all_others_hc_cards and not (
                        dire_circumstances or prefer_not_to_play
                    ):
                        print("PRIO 0")
                        self.play(order, table_id)
                        return

            # priority 1
            key_crits = [
                order
                for order in sorted_playables
                if state.is_critical(state.get_candidates(order))
                and max([x[1] for x in state.get_candidates(order)]) <= 3
            ]
            if len(key_crits):
                print("PRIO 1")
                self.play(key_crits[0], table_id)
                return

            # priority 2
            playable_fives = [
                order
                for order in my_good_actions["playable"]
                if min([x[1] for x in state.get_candidates(order)]) == 5
            ]
            if len(playable_fives):
                print("PRIO 2")
                self.play(playable_fives[0], table_id)
                return

            # priority 3
            if len(state.play_order_queue):
                for order in state.play_order_queue:
                    if order in sorted_playables:
                        print("PRIO 3")
                        self.play(order, table_id)
                        return

            # priority 4
            unique_playables = [
                order
                for order in sorted_playables
                if order not in my_good_actions["dupe_in_other_hand"]
            ]
            if len(unique_playables):
                print("PRIO 4")
                self.play(unique_playables[0], table_id)
                return

            # handle duped stuff
            for playable_order in sorted_playables:
                playable_candidates = state.get_candidates(playable_order)
                if len(playable_candidates) >= 2:
                    print("TOO MANY CANDIDATES TO WORRY ABOUT, PLAYING THIS")
                    self.play(playable_order, table_id)
                    return

                suit_index, rank = list(playable_candidates)[0]
                for player_index, hand in state.hands.items():
                    if player_index == state.our_player_index:
                        continue

                    for i, card in enumerate(hand):
                        if (suit_index, rank) != (card.suit_index, card.rank):
                            continue

                        candidates = state.all_candidates_list[player_index][i]
                        candidates_minus_my_play = candidates.difference(
                            {(suit_index, rank)}
                        )
                        if state.is_trash(candidates_minus_my_play):
                            print("OTHER GUY WILL KNOW ITS TRASH AFTER I PLAY THIS")
                            self.play(playable_order, table_id)
                            return

                        what_other_guy_sees = (
                            state.get_all_other_players_hat_clued_cards(player_index)
                        )
                        unique_candidates_after_my_play = (
                            candidates_minus_my_play.difference(what_other_guy_sees)
                        )
                        if not len(unique_candidates_after_my_play) or state.is_trash(
                            unique_candidates_after_my_play
                        ):
                            print("OTHER GUY WILL KNOW ITS DUPED AFTER I PLAY THIS")
                            self.play(playable_order, table_id)
                            return

                        if state.is_playable(candidates) and state.clue_tokens < 8:
                            print("OTHER GUY WILL PLAY THIS, DISCARDING")
                            self.discard(playable_order, table_id)
                            return

            if state.pace <= state.num_players - 2:
                print("PACE IS TOO LOW, NEED TO PLAY!!!")
                self.play(sorted_playables[0], table_id)
            elif state.clue_tokens >= 8:
                print("AT 8 TOKENS, CAN'T DISCARD!!!")
                self.play(sorted_playables[0], table_id)
            else:
                print("NO DUPES WILL DEFINITELY RESOLVE, GDing this instead")
                self.discard(sorted_playables[0], table_id)
            return

        lnhcs = state.get_leftmost_non_hat_clued_cards()
        num_useful_cards = 0
        for card in lnhcs:
            if card is None:
                continue
            if (card.suit_index, card.rank) in state.trash:
                continue
            num_useful_cards += 1

        # clues that narrow down useful cards the most are good, lowest scores first
        legal_clues = state.get_legal_clues()
        legal_clue_to_score = {
            (clue_value, clue_type, target_index): state.evaluate_clue_score(
                clue_value, clue_type, target_index
            )
            for (clue_value, clue_type, target_index) in legal_clues
        }
        legal_hat_clues = sorted(legal_clue_to_score.items(), key=lambda x: x[-1])
        print("All legal clues available:")
        for x, score in legal_hat_clues:
            print(f"{x}: {score}")

        if state.clue_tokens >= 2:
            if 0 <= state.score_pct < 0.24:
                r = {2: 0.79, 3: 0.76, 4: 0.7, 5: 0.6, 6: 0.45, 7: 0.3, 8: 0.0}[
                    min(8, state.clue_tokens + max(0, 4 - state.pace))
                ]
                num_useful_cards_touched = int(r * min(4, state.num_players - 1))
            elif 0.24 <= state.score_pct < 0.48:
                r = {2: 0.7, 3: 0.67, 4: 0.6, 5: 0.48, 6: 0.36, 7: 0.2, 8: 0.0}[
                    min(8, state.clue_tokens + max(0, 4 - state.pace))
                ]
                num_useful_cards_touched = int(r * min(4, state.num_players - 1))
            elif 0.48 <= state.score_pct < 0.72:
                r = {2: 0.6, 3: 0.55, 4: 0.48, 5: 0.4, 6: 0.3, 7: 0.17, 8: 0.0}[
                    min(8, state.clue_tokens + max(0, 4 - state.pace))
                ]
                num_useful_cards_touched = int(r * min(4, state.num_players - 1))
            else:
                r = {2: 0.48, 3: 0.36, 4: 0.24, 5: 0.16, 6: 0.1, 7: 0.05, 8: 0.0}[
                    min(8, state.clue_tokens + max(0, 4 - state.pace))
                ]
                num_useful_cards_touched = int(r * min(4, state.num_players - 1))

            if num_useful_cards >= num_useful_cards_touched:
                for (clue_value, clue_type, target_index), _ in legal_hat_clues:
                    print(f"USEFUL CLUE! Score = {state.score_pct:.3f}, we see {lnhcs}")
                    self.clue(target_index, clue_type, clue_value, table_id)
                    return

        # basic stall in endgame
        if state.endgame_stall_condition:
            for (clue_value, clue_type, target_index), _ in legal_hat_clues:
                print("STALL CLUE!")
                self.clue(target_index, clue_type, clue_value, table_id)
                return

        # discard if nothing better to do
        if state.clue_tokens < 8:
            if len(my_good_actions["trash"]):
                print("X TRASH")
                self.discard(my_good_actions["trash"][-1], table_id)
                return
            if len(my_good_actions["dupe_in_own_hand"]):
                print("X DUPE_IN_OWN_HAND")
                self.discard(my_good_actions["dupe_in_own_hand"][-1], table_id)
                return
            if len(my_good_actions["dupe_in_other_hand"]):
                print("X DUPE_IN_OTHER_HAND")
                self.discard(my_good_actions["dupe_in_other_hand"][-1], table_id)
                return
            if len(my_good_actions["dupe_in_other_hand_or_trash"]):
                print("X DUPE_IN_OTHER_HAND_OR_TRASH")
                self.discard(
                    my_good_actions["dupe_in_other_hand_or_trash"][-1], table_id
                )
                return

        # unless we have no safe actions
        if state.clue_tokens >= 1 and len(legal_hat_clues):
            for (clue_value, clue_type, target_index), _ in legal_hat_clues:
                print("CLUE BECAUSE NO SAFE ACTION!")
                self.clue(target_index, clue_type, clue_value, table_id)
                return

        if state.clue_tokens < 8:
            if len(my_good_actions["seen_in_other_hand"]):
                print("DISCARDING CARD SEEN BUT NOT TOUCHED!")
                self.discard(my_good_actions["seen_in_other_hand"][0], table_id)
                return

            for i, candidates in enumerate(state.our_candidates):
                if state.our_hand[-i - 1].order not in state.hat_clued_card_orders:
                    print("SACRIFICING NON HAT CLUED SLOT " + str(i) + "!")
                    self.discard(state.our_hand[-i - 1].order, table_id)
                    return

            for i, candidates in enumerate(state.our_candidates):
                if (
                    not len(candidates.intersection(state.criticals))
                    or i == len(state.our_candidates) - 1
                ):
                    print("SACRIFICING SLOT " + str(len(state.our_hand) - i - 1) + "!")
                    self.discard(state.our_hand[i].order, table_id)
                    return
        else:
            for i, candidates in enumerate(state.our_candidates):
                if (
                    not len(candidates.intersection(state.criticals))
                    or i == len(state.our_candidates) - 1
                ):
                    print(
                        "STALL BOMBING SLOT " + str(len(state.our_hand) - i - 1) + "!"
                    )
                    self.play(state.our_hand[i].order, table_id)
                    return

    # -----------
    # Subroutines
    # -----------

    def chat_reply(self, message, recipient):
        self.send(
            "chatPM",
            {
                "msg": message,
                "recipient": recipient,
                "room": "lobby",
            },
        )

    def send(self, command, data):
        if not isinstance(data, dict):
            data = {}
        self.ws.send(command + " " + json.dumps(data))

    def remove_card_from_hand(self, state, player_index, order):
        hand = state.hands[player_index]
        card_index = None
        for i in range(len(hand)):
            card = hand[i]
            if card.order == order:
                card_index = i

        if card_index is None:
            raise ValueError(
                "error: unable to find card with order " + str(order) + " in"
                "the hand of player " + str(player_index)
            )

        card = hand[card_index]
        del hand[card_index]
        del state.all_candidates_list[player_index][card_index]
        return card
