import chess
from player import Player
from agentminimax import AgentMinimax
from agentuct import AgentUCT
from agentrandom import AgentRandom

player_one = Player(False, AgentMinimax(2))
player_two = Player(False, AgentUCT(300, 10))


def print_board(board, fname, no_plys):
    print(board)
    print('Number of plys: %d' % (no_plys))
    print()
    print_to_file(board, fname, no_plys)
    if board.is_game_over():
        print("GAME OVER")


def print_to_file(board, fname, no_plys):
    f = open(fname, "a+")
    f.write(board.__str__())
    f.write('\nNumber of plys: %d\n\n' % (no_plys))
    f.close()


def run(board, is_white, fname, no_plys=0):
    if is_white:
        chosen_move = player_one.agent.make_move(board, True)
    else:
        chosen_move = player_two.agent.make_move(board, False)
    board.push(chosen_move)
    no_plys += 1
    print_board(board, fname, no_plys)
    if board.is_game_over():
        print("GAME OVER")
        return
    else:
        run(board, not is_white, fname, no_plys)


if __name__ == "__main__":
    board = chess.Board()
    no_games = 3
    for i in range(0, no_games):
        run(board, True, 'rungame{}.txt'.format(i+1))
