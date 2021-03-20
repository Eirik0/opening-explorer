"""Semigraphical user interface."""

from abc import ABC
from abc import abstractmethod

import blessed

# BOX DRAWINGS LIGHT HORIZONTAL                  U+2500   ─
# BOX DRAWINGS LIGHT VERTICAL                    U+2502   │
# BOX DRAWINGS LIGHT DOWN AND RIGHT              U+250c   ┌
# BOX DRAWINGS LIGHT DOWN AND LEFT               U+2514   ┐
# BOX DRAWINGS LIGHT UP AND RIGHT                U+250c   └
# BOX DRAWINGS LIGHT UP AND LEFT                 U+2518   ┘
# BOX DRAWINGS LIGHT VERTICAL AND RIGHT          U+251c   ├
# BOX DRAWINGS LIGHT VERTICAL AND LEFT           U+2524   ┤
# BOX DRAWINGS LIGHT DOWN AND HORIZONTAL         U+252c   ┬
# BOX DRAWINGS LIGHT UP AND HORIZONTAL           U+2534   ┴
# BOX DRAWINGS LIGHT VERTICAL AND HORIZONTAL     U+253c   ┼
# FULL BLOCK                                     U+2588   █
# WHITE CHESS KING                               U+2654   ♔
# WHITE CHESS QUEEN                              U+2655   ♕
# WHITE CHESS ROOK                               U+2656   ♖
# WHITE CHESS BISHOP                             U+2657   ♗
# WHITE CHESS KNIGHT                             U+2658   ♘
# WHITE CHESS PAWN                               U+2659   ♙
# BLACK CHESS KING                               U+265A   ♚
# BLACK CHESS QUEEN                              U+265B   ♛
# BLACK CHESS ROOK                               U+265C   ♜
# BLACK CHESS BISHOP                             U+265D   ♝
# BLACK CHESS KNIGHT                             U+265E   ♞
# BLACK CHESS PAWN                               U+265F   ♟︎


class TextGrid:
    pass


class GuiState(ABC):
    """Abstraction for the state of the user interface."""

    @abstractmethod
    def set_size(self, width: int, height: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def handle_user_input(self, user_input: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw(self) -> TextGrid:
        raise NotImplementedError


class Gui:
    """Draws the interface and handles user input."""

    def __init__(self, term: blessed.Terminal, state: GuiState) -> None:
        self.term: blessed.Terminal = term
        self.state = state
        self.is_running: bool = True

    def set_state(self, state: GuiState) -> None:
        self.state = state
