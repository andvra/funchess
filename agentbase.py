import chess
from abc import ABC, abstractmethod


class AgentBase(ABC):
    def __init__(self):
        super(AgentBase, self).__init__()

    @abstractmethod
    def make_move(self, board: chess.Board, is_white: bool):
        pass


if __name__ == "__main__":
    print("Can't run this file directly")
