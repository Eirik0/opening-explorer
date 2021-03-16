from __future__ import annotations  # PEP 563

from typing import NamedTuple, Optional

# TODO Create a Position type where id is required and replace Position with some sort of prototype


class Position(NamedTuple):
    position_id: Optional[int]
    fen: str
    move: Optional[str]
    score: Optional[float]
    depth: Optional[int]
    pv: Optional[str]

    def with_position_id(self, position_id: int) -> Position:
        return Position(position_id, self.fen, self.move, self.score, self.depth, self.pv)
