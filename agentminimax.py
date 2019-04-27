# This agent uses minimax with alpha-beta pruning
from math import inf
import chess
from agentbase import AgentBase

# In the maps below, index 0 = A8 and index 63 = H1
pawn_map_black=[
    0,0,0,0,0,0,0,0
    ,50,50,50,50,50,50,50,50
    ,10,10,20,30,30,20,10,10
    ,5,5,10,25,25,10,5,5
    ,0,0,0,20,20,0,0,0
    ,5,-5,-10,0,0,-10,-5,5
    ,5,10,10,-20,-20,10,10,5
    ,0,0,0,0,0,0,0,0]
knight_map_black=[
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50]
bishop_map_black = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20]
rook_map_black=[
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0]
queen_map_black=[
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20]
king_map_black = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20]

class AgentMinimax(AgentBase):

    def __init__(self, depth):
        self.depth = depth

    def make_move(self, board, is_white):
        _, moves = self.__choose__(board, is_white, self.depth)
        if len(moves)==None:
            return None
        else:
            return moves[0]

    def __value_with_move__(self, board,move):
        board.push(move)
        val=self.__evaluate__(board)
        board.pop()
        return val

    def __get_sorted_legal_moves__(self, board,is_white):
        legal_moves=[(move,self.__value_with_move__(board,move)) for idx,move in enumerate(board.legal_moves)]
        legal_moves.sort(key=lambda x:x[1])
        if is_white==True:
            legal_moves.reverse()
        sorted_legal_moves=[x[0] for x in legal_moves]
        return sorted_legal_moves

    def __choose__(self, board, is_white, depth, alpha=-inf, beta=inf):
        if depth==0:
            return self.__evaluate__(board),[]
        if is_white==True:
            value = -inf
            moves = []
            sorted_legal_moves=self.__get_sorted_legal_moves__(board,is_white)
            for cur_move in sorted_legal_moves:
                board.push(cur_move)
                cvalue, _ = self.__choose__(board, False, depth-1,alpha,beta)
                board.pop()
                if cvalue>value:
                    value=cvalue
                    moves.clear()
                    moves.append(cur_move)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, moves
        else:
            value = inf
            moves = []
            sorted_legal_moves=sorted_legal_moves=self.__get_sorted_legal_moves__(board,is_white)
            for cur_move in sorted_legal_moves:
                board.push(cur_move)
                cvalue, _ = self.__choose__(board, True,depth-1,alpha,beta)
                board.pop()
                if cvalue<value:
                    value = cvalue
                    moves.clear()
                    moves.append(cur_move)
                beta = min(beta,value)
                if alpha >= beta:
                    break
            return value, moves

    def __value_of_pieces__(self, board, is_white):
        # Count the number of pieces left and give them a value
        # https://www.chessprogramming.org/Simplified_Evaluation_Function
        ret = len(board.pieces(chess.PAWN, is_white)) * 100
        ret += len(board.pieces(chess.KNIGHT, is_white)) * 320
        ret += len(board.pieces(chess.BISHOP,is_white)) * 330
        ret += len(board.pieces(chess.ROOK, is_white)) * 500
        ret += len(board.pieces(chess.QUEEN, is_white)) * 900
        ret += len(board.pieces(chess.KING, is_white)) * 20000
        return ret

    def __value_of_position__(self, board, is_white):
        # Index 0 = A1, index 63 = H8 in the python-chess lib. So, invert for white pieces
        switcher ={
                'p':pawn_map_black,
                'P':pawn_map_black[::-1],
                'n':knight_map_black,
                'N':knight_map_black[::-1],
                'b':bishop_map_black,
                'B':bishop_map_black[::-1],
                'r':rook_map_black,
                'R':rook_map_black[::-1],
                'q':queen_map_black,
                'Q':queen_map_black[::-1],
                'k':king_map_black,
                'K':king_map_black[::-1]}
        pieces=board.piece_map()
        ret=0
        for pos,piece in pieces.items():
            if piece.color==is_white:
                ret+=switcher[piece.symbol()][pos]
        return ret

    def __evaluate__(self, board):
        value_white = self.__value_of_pieces__(board, True)+self.__value_of_position__(board,True)
        value_black = self.__value_of_pieces__(board, False)+self.__value_of_position__(board,False)
        value_total = value_white-value_black
        return value_total

if __name__=="__main__":
    print("Can't run this file directly")