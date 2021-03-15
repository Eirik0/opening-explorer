from typing import List, Optional


class Position:

    def __init__(
            self, id: Optional[int], fen: Optional[str], move: Optional[str], score: Optional[float],
            depth: Optional[int], pv: Optional[List[str]]):
        self.id = id
        self.fen = fen
        self.move = move
        self.score = score
        self.depth = depth
        self.pv = pv
