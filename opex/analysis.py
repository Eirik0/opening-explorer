class Position:
    def __init__(self, id, fen, move, score, depth, pv):
        self.id = id
        self.fen = fen
        self.move = move
        self.score = score
        self.depth = depth
        self.pv = pv


