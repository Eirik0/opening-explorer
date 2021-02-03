class Position:
    def __init__(self, id, fen, move, score, depth, pv):
        self.id = id
        self.fen = fen
        self.move = move
        self.score = score
        self.depth = depth
        self.pv = pv


class DagNode:
    def __init__(self, parent_id, child_id):
        self.parent_id = parent_id
        self.child_id = child_id
