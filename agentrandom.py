from agentbase import AgentBase
import random


class AgentRandom(AgentBase):
    def make_move(self, board, is_white):
        legal_moves = [move for _, move in enumerate(board.legal_moves)]
        move = random.choice(legal_moves)
        return move


if __name__ == "__main__":
    print("Can't run this file directly")
