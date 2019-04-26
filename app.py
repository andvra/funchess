"""
Demo Flask application to test the operation of Flask with socket.io
Aim is to create a webpage that is constantly updated with random numbers from a background python process.
30th May 2014
===================
Updated 13th April 2018
+ Upgraded code to Python 3
+ Used Python3 SocketIO implementation
+ Updated CDN Javascript and CSS sources
"""




# Start with a basic flask app webpage.
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context
from random import random
from time import sleep
from threading import Thread, Event
import chess
import chess.svg
import random
from math import inf
import time

# The maps below, found online, is represented in an inverted way.
# So, reverse back when applying to the white pieces.
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

class Node:
    def __init__(self, value=None, children=None):
        self.children = children
        self.value = value

def value_with_move(board,move):
    board.push(move)
    val=evaluate(board)
    board.pop()
    return val

max_depth=4
def choose(board, is_white, depth=max_depth, alpha=-inf, beta=inf):
    if depth==0:
        return evaluate(board),[]
    if is_white==True:
        value = -inf
        moves = []
        legal_moves=[(move,value_with_move(board,move)) for idx,move in enumerate(board.legal_moves)]
        legal_moves.sort(key=lambda x:-x[1])
        sorted_legal_moves=[x[0] for x in legal_moves]
        for cur_move in sorted_legal_moves:
            #if depth==max_depth:
            #    print()
            #    print("###"+cur_move.uci())
            board.push(cur_move)
            cvalue, cmove = choose(board, False, depth-1,alpha,beta)
            #if depth<max_depth:
            #    print(cur_move.uci() + ": " + str(cvalue),end=" ")
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
        for cur_idx,cur_move in enumerate(board.legal_moves):
            #if depth==max_depth:
            #    print()
            #    print("###"+cur_move.uci())
            board.push(cur_move)
            cvalue, cmove = choose(board, True,depth-1,alpha,beta)
            #if depth<max_depth:
            #    print(cur_move.uci() + ": "+ str(cvalue),end=" ")
            board.pop()
            if cvalue<value:
                value = cvalue
                moves.clear()
                moves.append(cur_move)
            beta = min(beta,value)
            if alpha >= beta:
                break
        return value, moves

def value_of_pieces(board, is_white):
    # Count the number of pieces left and give them a value
    # https://www.chessprogramming.org/Simplified_Evaluation_Function
    ret = len(board.pieces(chess.PAWN, is_white)) * 100
    ret += len(board.pieces(chess.KNIGHT, is_white)) * 320
    ret += len(board.pieces(chess.BISHOP,is_white)) * 330
    ret += len(board.pieces(chess.ROOK, is_white)) * 500
    ret += len(board.pieces(chess.QUEEN, is_white)) * 900
    ret += len(board.pieces(chess.KING, is_white)) * 20000
    return ret

def value_of_position(board, is_white):
    # Index 0 = A1, index 63 = H8 in the python-chess lib.
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

def evaluate(board):
    value_white = value_of_pieces(board, True)+value_of_position(board,True)
    value_black = value_of_pieces(board, False)+value_of_position(board,False)
    value_total = value_white-value_black
    return value_total

human_player=True
number_of_round=200


__author__ = 'slynn'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

#turn the flask app into a socketio app
socketio = SocketIO(app)

#random number Generator Thread
thread = Thread()
thread_stop_event = Event()

class RandomThread(Thread):
	def __init__(self):
		super(RandomThread, self).__init__()
		self.svgs=[]
		self.input_move=None
		self.board=chess.Board()
		
	def register_human_move(self,move_string):
		legal_moves=[move.uci() for idx,move in enumerate(self.board.legal_moves)]
		print(legal_moves)
		if move_string in legal_moves:
			self.input_move=move_string
		else:
			print("NOT VALID MOVE")
		
	def get_human_move(self):
		move = chess.Move.from_uci(self.input_move)
		self.input_move=None
		return move
	
	def move(self,is_white):
		if (is_white==False) and (human_player==True):
			while self.input_move==None:
				sleep(1)	# Wait a second for human input
			move=self.get_human_move()
		else:
			if is_white==False:
				# Reduce the ability of the black player
				value, moves = choose(self.board, is_white,depth=3)
			else:
				value, moves = choose(self.board, is_white)
			if len(moves)==0:
				print("NO MORE MOVES!")
				print(self.board.legal_moves)
			move=random.sample(moves,1)[0]
		self.board.push(move)
		
	def board_to_svg(self):
		svg=chess.svg.board(board=self.board)
		svg=svg[:5]+"width='800px' "+svg[5:]
		return svg
		
	def emit(self):
		socketio.emit('newsvg', {'svgs': self.svgs}, namespace='/test')
		
	def randomNumberGenerator(self):
		svg=self.board_to_svg()
		self.svgs.append(svg)
		self.emit()
		while not thread_stop_event.isSet():
			self.move(True)
			self.svgs.append(self.board_to_svg())
			self.emit()
			if self.board.is_game_over():
				print("GAME OVER")
				break
			self.move(False)
			self.svgs.append(self.board_to_svg())
			self.emit()
			if self.board.is_game_over():
				print("GAME OVER")
				break
		print("QUIT")
	def run(self):
		self.randomNumberGenerator()


@app.route('/')
def index():
	#only by sending this page first will the client be connected to the socketio instance
	return render_template('index.html')

def start_game():
	global thread
	print("Starting Game")
	thread = RandomThread()
	thread.start()
	
@socketio.on('connect', namespace='/test')
def test_connect():
	# need visibility of the global thread object
	global thread
	print('Client connected')

	#Start the random number generator thread only if the thread has not been started before.
	if not thread.isAlive():
		start_game()
	else:
		thread.emit()

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
	print('Client disconnected')

@socketio.on('move', namespace='/test')
def test_move(json):
	global thread
	thread.register_human_move(json['data'])
	
@socketio.on('restart', namespace='/test')
def restart():
	start_game()
	
if __name__ == '__main__':
	socketio.run(app,host='0.0.0.0')