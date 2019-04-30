from agentbase import AgentBase
import time
import random
import math
import operator
import  multiprocessing as mp
import os

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
    def __init__(self, board, level, start_legal_move=None,max_legal_moves=None):
        self.legal_moves = [move for _, move in enumerate(board.legal_moves)]
        if start_legal_move!=None:
            self.legal_moves=self.legal_moves[start_legal_move:start_legal_move+max_legal_moves]
            print(self.legal_moves)
            print('Count: {}'.format(len(self.legal_moves)))
        super().__init__(len(self.legal_moves), level)

    def get_child(self, board, min_tries_per_node):
        new_node_created=False
        if self.must_explore(min_tries_per_node):
            idx, child_node, cur_move = self.get_move_to_explore()
            if child_node==None:
                # Perform the move here to get the possible moves for initialization
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

    def run_it(self, board, is_white, root_part, t_start,pid,out_queue):
        print("Start job " + str(pid))
        while (time.time()-t_start<self.t_max):
            self.uct(board, is_white, root_part)
        print("Finished loop for pid {}".format(pid))
        idx_max, val_max = max([(idx, val.value/val.visits) for idx, val in enumerate(root_part.children) if val and val.value>0], key=operator.itemgetter(1))
        for idx, node in enumerate(root_part.children):
            if node == None:
                print('Node %02d doesn\'t exist. Increase run time')
            else:
                print('Node %02d:\tValue: %.2f\tVisited:%d\tucb:%f' % (idx, node.value, node.visits, node.ucb_value(self.no_nodes)))
        out_queue.put((root_part.legal_moves[idx_max],val_max))
        print("End job " + str(pid))

    def make_move(self, board, is_white):
        t_start = time.time()
        self.reset()
        #root = ChessNode(board, 0)
        print('The current system have {} CPUs of which {} are usable'.format(mp.cpu_count(),len(os.sched_getaffinity(0))))
        no_processes = 3
        no_legal_moves=board.legal_moves.count()
        legal_moves_per_process=math.ceil(no_legal_moves/no_processes)
        processes=[]
        root_parts=[]
        out_queue=mp.Queue()
        for i in range(0,no_processes):
            root_parts.append(ChessNode(board.copy(),0,i*legal_moves_per_process,legal_moves_per_process))
            processes.append(mp.Process(target=self.run_it,args=(board.copy(),is_white,root_parts[-1],t_start,i+1,out_queue)))
            processes[-1].start()
        for p in processes:
            p.join()
        max_val,max_val_move=-math.inf,None
        for i in range(0,no_processes):
            cur_max_move, cur_max_val = out_queue.get()
            print(cur_max_move,cur_max_val)
            if cur_max_val>max_val:
                max_val=cur_max_val
                max_val_move=cur_max_move
        print("Done with all the jobs")

        move = max_val_move
        print('Chose move {} with value/visits={}. Node count: {} Max depth: {}'.format
                (max_val_move, max_val, self.no_nodes, self.max_level))
        return move


if __name__ == "__main__":
    print("Can't run this file directly")
