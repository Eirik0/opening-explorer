from typing import Optional

class Position:
    # pylint: disable=unsubscriptable-object
    def __init__(self, id: Optional[int], fen: str, move: str, score: int, depth: int, pv: str) -> None:
        self.id = id
        self.fen = fen
        self.move = move
        self.score = score
        self.depth = depth
        self.pv = pv
