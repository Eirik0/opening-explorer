from typing import NamedTuple, Optional

# TODO Create a Position type where id is required and replace Position with some sort of prototype


class Position(NamedTuple):
    id: Optional[int]
    fen: str
    move: Optional[str]
    score: Optional[float]
    depth: Optional[int]
    pv: Optional[str]
