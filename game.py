from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context
from random import random
from time import sleep
from threading import Thread, Event
import chess
import chess.svg
from agentminimax import AgentMinimax
from agentuct import AgentUCT
from player import Player


player_one = Player(False, AgentMinimax(2))
player_two = Player(False, AgentUCT(10, 10))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
#app.config['DEBUG'] = True

socketio = SocketIO(app)

thread = Thread()


def scale_svg(svg_data, width_px=800):
    # Inject a width-attribute to control the size of the SVG
    svg = svg_data[:5]+"width=\"" + str(width_px) + "px\""+svg_data[5:]
    return svg


def send_message(msg):
    socketio.emit('newmsg', {'msg': msg}, namespace='/chessgame')


class GameThread(Thread):
    def __init__(self):
        super(GameThread, self).__init__()
        self.svgs = []
        self.input_move = None
        self.board = chess.Board()
        self.__thread_stop_event__ = Event()

    def register_human_move(self, move_string):
        legal_moves = [move.uci()
                       for idx, move in enumerate(self.board.legal_moves)]
        print(legal_moves)
        if move_string in legal_moves:
            self.input_move = move_string
        else:
            print("INVALID MOVE")

    def get_human_move(self):
        move = chess.Move.from_uci(self.input_move)
        self.input_move = None
        return move

    def move(self, is_white):
        if ((is_white == True) and (player_one.is_human)) or ((is_white == False) and (player_two.is_human)):
            while self.input_move == None:
                sleep(1)  # Sleep for a second and check again
            chosen_move = self.get_human_move()
        else:
            if is_white:
                chosen_move = player_one.agent.make_move(self.board, True)
            else:
                chosen_move = player_two.agent.make_move(self.board, False)
            if chosen_move == None:
                print("NO MORE MOVES!")
                print(self.board.legal_moves)
        self.board.push(chosen_move)

    def board_to_svg(self):
        svg = chess.svg.board(board=self.board)
        return scale_svg(svg)

    def emit(self):
        socketio.emit('newsvg', {'svgs': self.svgs}, namespace='/chessgame')

    def run(self):
        svg = self.board_to_svg()
        self.svgs.append(svg)
        self.emit()
        while not self.__thread_stop_event__.isSet():
            self.move(True)
            self.svgs.append(self.board_to_svg())
            self.emit()
            if self.board.is_game_over():
                self.game_over()
                break
            self.move(False)
            self.svgs.append(self.board_to_svg())
            self.emit()
            if self.board.is_game_over():
                self.game_over()
                break
        print("QUIT")

    def game_over(self):
        print("GAME OVER")
        send_message('gameover')

    def do_stop(self):
        self.__thread_stop_event__.set()


@app.route('/')
def index():
    # The client will be connected as soon as we return this page
    return render_template('index.html')


def start_game():
    global thread
    print("Starting Game")
    # Stop running thread if it's initiated already
    if type(thread) == GameThread:
        thread.do_stop()
    thread = GameThread()
    thread.start()


@socketio.on('connect', namespace='/chessgame')
def connect():
    global thread
    send_message('connected')
    if not thread.is_alive():
        start_game()
    else:
        thread.emit()


@socketio.on('disconnect', namespace='/chessgame')
def disconnect():
    print('Client disconnected')


@socketio.on('human_move', namespace='/chessgame')
def human_move(json):
    global thread
    thread.register_human_move(json['data'])


@socketio.on('restart', namespace='/chessgame')
def restart():
    start_game()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
