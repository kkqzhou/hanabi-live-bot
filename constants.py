import enum
from typing import Tuple

# Client constants must match the server constants:
# https://github.com/Zamiell/hanabi-live/blob/master/server/src/constants.go


class ACTION(int, enum.Enum):
    PLAY = 0
    DISCARD = 1
    COLOR_CLUE = 2
    RANK_CLUE = 3


class TextInt(int):
    str_ = ""

    def set_str(self, str_):
        self.str_ = str_

    def __str__(self):
        return self.str_
    
    def __repr__(self):
        return self.__str__()


MAX_CLUE_NUM = 8
COLOR_CLUE = TextInt(0)
COLOR_CLUE.set_str("COLOR")
RANK_CLUE = TextInt(1)
RANK_CLUE.set_str("RANK")

CardTuple = Tuple[int, int]
ClueTuple = Tuple[TextInt, int]
