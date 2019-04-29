from agentbase import AgentBase
import time
import random
import math
import operator


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

    def get_promising_children(self, reverse):
        nodes_with_values = [(idx, child.ucb_value(self.visits))
                             for idx, child in enumerate(self.children)]
        nodes_with_values.sort(key=lambda x: x[1], reverse=reverse)
        node_idx = nodes_with_values[0][0]
        return node_idx, self.children[node_idx]

    def must_explore(self, min_tries_per_node):
        return ((None in self.children) or (min(list(map(lambda x: x.visits, self.children))) < min_tries_per_node))

    def ucb_value(self, number_of_visits_parent):
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

    def get_move_to_explore(self):
        idx, node = self.get_node_to_explore()
        return idx, node, self.legal_moves[idx]

    def get_promising_children(self, is_white):
        idx, node = super().get_promising_children(is_white)
        return idx, node, self.legal_moves[idx]


class AgentUCT(AgentBase):
    """ Based on UCT ( = MCTS + UCB) described here: http://mcts.ai/about/
    """

    def __init__(self, t_max, min_tries_per_node):
        self.t_max = t_max
        self.no_nodes = 0
        self.min_tries_per_node = min_tries_per_node
        self.max_level = 0

    def reset(self):
        self.no_nodes = 0

    def create_node(self, board, level):
        self.no_nodes += 1
        self.max_level = max(self.max_level, level)
        return ChessNode(board, level)

    def uct(self, board, is_white, node):
        if board.is_game_over():
            return {'1-0': 1, '1/2-1/2': 0.5, '0-1': 0}[board.result()]
        else:
            if node.must_explore(self.min_tries_per_node):
                idx, child_node, cur_move = node.get_move_to_explore()
            else:
                idx, child_node, cur_move = node.get_promising_children(
                    is_white)
            board.push(cur_move)
            if child_node == None:
                child_node = self.create_node(board, node.level+1)
                node.children[idx] = child_node
            result = self.uct(board, not is_white, child_node)
            board.pop()
            # Black should get one point when black wins. Since the returned result for black win is 0,
            #   we subtract it from 1. This will also handle the case of a draw
            if is_white:
                node.value += result
            else:
                node.value += (1-result)
            node.visits += 1
            return result

    def make_move(self, board, is_white):
        t_start = time.time()
        self.reset()
        root = self.create_node(board, 0)
        while (time.time()-t_start < self.t_max):
            self.uct(board, is_white, root)
        idx_max, val_max = max([(idx, val.value) for idx, val in enumerate(
            root.children) if val], key=operator.itemgetter(1))
        idx_min, val_min = min([(idx, val.value) for idx, val in enumerate(
            root.children) if val], key=operator.itemgetter(1))
        if is_white:
            chosen_node_idx, chosen_node_value = idx_max, val_max
        else:
            chosen_node_idx, chosen_node_value = idx_min, val_min
        for idx, node in enumerate(root.children):
            if node == None:
                print('Node %02d doesn\'t exist. Increase run time')
            else:
                print('Node %02d:\tValue: %.2f\tVisited:%d\tucb:%f' %
                      (idx, node.value, node.visits, node.ucb_value(self.no_nodes)))
        print('Chose node with idx=%d and value %f. Created a total of %d nodes. Max level %d' %
              (chosen_node_idx, chosen_node_value, self.no_nodes, self.max_level))
        move = root.legal_moves[chosen_node_idx]
        return move


if __name__ == "__main__":
    print("Can't run this file directly")
