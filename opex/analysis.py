from typing import List


class Position:

    def __init__(self, id: int, fen: str, move: str, score: float, depth: int, pv: List[str]):
        self.id = id
        self.fen = fen
        self.move = move
        self.score = score
        self.depth = depth
        self.pv = pv
