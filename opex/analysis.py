"""Analysis related classes and methods."""

from __future__ import annotations  # PEP 563

from typing import NamedTuple, Optional

# TODO Create a Position type where id is required and replace Position with some sort of prototype


class Position(NamedTuple):
    """Information nececessary to store the analysis of a position."""
    position_id: Optional[int]
    fen: str
    score: float
    depth: int
    pv: str

    def with_position_id(self, position_id: int) -> Position:
        return Position(position_id, self.fen, self.score, self.depth, self.pv)
