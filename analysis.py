class Position:
    def __init__(self, id, parent_id, fen, move, score, depth, pv):
        self.id = id
        self.parent_id = parent_id
        self.fen = fen
        self.move = move
        self.score = score
        self.depth = depth
        self.pv = pv