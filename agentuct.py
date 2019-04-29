from agentbase import AgentBase
import time
import random
import math
import operator
import threading
from concurrent.futures import ThreadPoolExecutor, wait

class MCTSNode:
    # level 0 = root
    def __init__(self, number_of_children, level):
        self.children = [None for x in range(0, number_of_children)]
        self.visits = 0  # Number of times this node is visited
        self.value = 0.  # Add 1 for white win, 0 for draw, -1 for black win
        self.level = level

    def get_node_to_explore(self):
        if None in self.children:
            idxs = [i for i, e in enumerate(self.children) if e == None]
            idx = random.choice(idxs)
            return idx, None
        else:
            visit_count = list(map(lambda x: x.visits, self.children))
            min_val = min(visit_count)
            idxs = [i for i, e in enumerate(
                self.children) if e.visits == min_val]
            idx = random.choice(idxs)
            return idx, self.children[idx]

    def get_promising_children(self):
        nodes_with_values = [(idx, child.ucb_value(self.visits))
                             for idx, child in enumerate(self.children)]
        nodes_with_values.sort(key=lambda x: x[1], reverse=True)
        node_idx = nodes_with_values[0][0]
        return node_idx, self.children[node_idx]

    def must_explore(self, min_tries_per_node):
        return ((None in self.children) or (min(list(map(lambda x: x.visits, self.children))) < min_tries_per_node))

    def ucb_value(self, number_of_visits_parent):
        if self.visits == 0:
            return 0
        # TODO: C should be determined empirically. Found that sqrt(2) should be good somewhere
        c = math.sqrt(2)
        number_of_visits = self.visits
        vi = self.value/number_of_visits
        value = vi + c * \
            math.sqrt(math.log(number_of_visits_parent)/number_of_visits)
        return value


class ChessNode(MCTSNode):
    def __init__(self, board, level):
        self.legal_moves = [move for _, move in enumerate(board.legal_moves)]
        super().__init__(len(self.legal_moves), level)
        self._lock = threading.Lock()

    def get_child(self, board, min_tries_per_node):
        with self._lock:
            new_node_created=False
            if self.must_explore(min_tries_per_node):
                idx, child_node, cur_move = self.get_move_to_explore()
                if child_node==None:
                    board.push(cur_move)
                    child_node = ChessNode(board, self.level+1)
                    board.pop()
                    self.children[idx]=child_node
                    new_node_created=True
            else:
                idx, child_node, cur_move = self.get_promising_children()
        return idx, child_node, cur_move, new_node_created

    def get_move_to_explore(self):
        idx, node = self.get_node_to_explore()
        return idx, node, self.legal_moves[idx]

    def get_promising_children(self):
        idx, node = super().get_promising_children()
        return idx, node, self.legal_moves[idx]


class AgentUCT(AgentBase):
    """ Based on UCT ( = MCTS + UCB) described here: http://mcts.ai/about/
    """

    def __init__(self, t_max, min_tries_per_node):
        self.t_max = t_max
        self.min_tries_per_node = min_tries_per_node
        self.max_level=0
        self.no_nodes = 0

    def reset(self):
        self.max_level=0
        self.no_nodes=0

    def uct(self, board, is_white, node):
        if board.is_game_over():
            return {'1-0': 1, '1/2-1/2': 0.5, '0-1': 0}[board.result()]
        elif node.level==150:
            return 2
        else:
            idx, child_node, cur_move, new_node_created = node.get_child(board, self.min_tries_per_node)
            if new_node_created:
                self.no_nodes += 1
            self.max_level=max(self.max_level,child_node.level)
            board.push(cur_move)
            result = self.uct(board, not is_white, child_node)
            board.pop()
            # Black should get one point when black wins. Since the returned result for black win is 0,
            #   we subtract it from 1. This will also handle the case of a draw
            # Less than two: This is to keep a break at 150 moves (tweakable parameter)
            if result<2:
                if is_white:
                 node.value += result
                else:
                    node.value += (1-result)
                node.visits += 1
            return result

    def run_it(self, board, is_white, root, t_start,id):
        print("Start job " + str(id))
        while (time.time()-t_start<self.t_max):
            self.uct(board, is_white, root)
        print("End job " + str(id))

    def make_move(self, board, is_white):
        t_start = time.time()
        self.reset()
        root = ChessNode(board, 0)
        futures=[]
        no_threads = 4
        with ThreadPoolExecutor(max_workers=no_threads) as executor:
            for i in range(0,no_threads):
                futures.append(executor.submit(self.run_it, board.copy(), is_white, root, t_start,i+1))
        wait(futures)
        print("Done with all the jobs")
        idx_max, val_max = max([(idx, val.value/val.visits) for idx, val in enumerate(
            root.children) if val and val.value>0], key=operator.itemgetter(1))
        chosen_node_idx, chosen_node_value = idx_max, val_max
        for idx, node in enumerate(root.children):
            if node == None:
                print('Node %02d doesn\'t exist. Increase run time')
            else:
                print('Node %02d:\tValue: %.2f\tVisited:%d\tucb:%f' %
                      (idx, node.value, node.visits, node.ucb_value(self.no_nodes)))
        print('Chose node with idx=%d and value/visits=%f. Total %d nodes. Max level %d' %
              (chosen_node_idx, chosen_node_value, self.no_nodes, self.max_level))
        move = root.legal_moves[chosen_node_idx]
        return move


if __name__ == "__main__":
    print("Can't run this file directly")
