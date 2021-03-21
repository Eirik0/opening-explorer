"""A chess opening explorer."""

#!/usr/bin/env python3

import json
import os

import chess
from chess import engine
from chess import Move

from opex import db_wrapper
from opex import settings_loader
from opex.analysis import ParentRelationship
from opex.analysis import Position
from opex.settings_loader import Json

import typing
from typing import Dict, List


def get_fen(board: chess.Board) -> str:
    return board.fen()  # type: ignore


# def back_propagate(position):
#     # TODO
#     pass


def select_child_move(children: Dict[str, Position]) -> str:
    # TODO make this smarter
    return next(iter(children.keys()))


class OpeningExplorer:
    """Uses a uci engine to create analysis which is then stored in a databse."""

    def __init__(self, database: db_wrapper.Database, uci_engine: engine.SimpleEngine) -> None:
        self.database = database
        self.uci_engine = uci_engine

    def analyze_board(self, board: chess.Board):
        """Analyzes the board with the uci_engine and creates a Position."""
        print('Analyzing')
        info = self.uci_engine.analyse(board, engine.Limit(depth=20))
        assert 'score' in info and 'pv' in info
        pv = ' '.join([str(move) for move in info['pv']])
        score = info['score'].relative.score(mate_score=10000)
        print(f'score={score}, pv={pv}')
        return Position(None, get_fen(board), score, 20, pv)

    def search(self, board: chess.Board) -> None:
        """Recursive tree search."""
        print('Searching root')
        position = self.database.get_position(get_fen(board))

        if position is None:
            # This position has no known parent/child (may be root).
            # Analyze and insert the root position for this subtree.
            self.database.insert_position(self.analyze_board(board), None)
            return

        self.search_position(board, position)

    def search_position(self, board: chess.Board, position: Position) -> None:
        """Recursive tree search with an already loaded position."""
        print('Searching position')
        position_id = typing.cast(int, position.position_id)

        children = self.database.get_child_positions(position_id)
        legal_moves = list(board.legal_moves)

        if len(children) == len(legal_moves):
            # This position is full, recurse on one of the children
            move = select_child_move(children)
            print(f'Making move {move}')
            board.push(Move.from_uci(move))
            self.search_position(board, children[move])
            board.pop()
            print('pop move')
            return

        unanalyzed_moves = [move for move in legal_moves if move.uci() not in children]
        move = unanalyzed_moves[0]
        print(f'Making move {move}')
        board.push(move)
        self.database.insert_position(self.analyze_board(board), ParentRelationship(position_id, move.uci()))
        print('pop move')
        board.pop()
        if len(unanalyzed_moves) == 1:
            print('Back progogate')
            # TODO back propogate (unmake move ?)


def open_engine_with_options(path: str, options: engine.ConfigMapping):
    """Opens UCI engine with the specified dictionary of opening options."""
    uci_engine = engine.SimpleEngine.popen_uci(path)
    uci_engine.configure(options)
    return uci_engine


def ensure_file_exists(file_path: str) -> None:
    """Create a file and its parent directories if it does not exist."""
    parent_directory = os.path.dirname(file_path)
    if parent_directory and not os.path.isdir(parent_directory):
        os.mkdir(parent_directory)
    if not os.path.isfile(file_path):
        with open(file_path, 'w+') as file:
            file.write('')


def load_settings() -> Json:
    """Loads json settings."""
    ensure_file_exists('opex-settings.json')
    with open('opex-settings.json', 'r+') as settings_file:
        settings_simple = settings_loader.load_settings_simple(settings_file)
        settings_file.seek(0)
        settings_no_defaults = settings_loader.load_settings(settings_file, False)
        settings_file.seek(0)
        if settings_simple != settings_no_defaults:
            json.dump(settings_no_defaults, settings_file, indent=4, sort_keys=True)
            settings_file.seek(0)
        return settings_loader.load_settings(settings_file)


def load_all_engine_options(settings: Json) -> Dict[str, engine.ConfigMapping]:
    """Loads engine options."""
    engine_options: Dict[str, engine.ConfigMapping] = {}
    for engine_setting in typing.cast(List[Json], settings['engines']):
        nickname = typing.cast(str, engine_setting['nickname'])
        path = typing.cast(str, engine_setting['path'])
        with engine.SimpleEngine.popen_uci(path) as uci_engine:
            default_options = [option for _, option in uci_engine.options.items()]
        engine_options_directory = settings['engine_options_directory']
        options_file_path = f'{engine_options_directory}\\{nickname}.uci'
        ensure_file_exists(options_file_path)
        with open(options_file_path, 'r+') as options_file:
            simple_options = settings_loader.load_engine_options_simple(options_file)
            settings_loader.check_engine_options(default_options, simple_options)
            options_file.seek(0)
            options_with_defaults = settings_loader.load_engine_options(default_options, options_file, False)
            options_file.seek(0)
            if simple_options != options_with_defaults:
                options_file.writelines(
                    settings_loader.engine_options_file_lines(default_options, options_with_defaults))
                options_file.seek(0)
            engine_options[nickname] = settings_loader.load_engine_options(default_options, options_file)
    return engine_options


def main():
    """Chess opening explorer."""
    settings = load_settings()

    # TODO create a type for settings
    engine_settings = typing.cast(List[Json], settings['engines'])

    settings_loader.check_engine_settings(engine_settings)

    engine_options = load_all_engine_options(settings)
    first_engine_settings = engine_settings[0]

    engine_path = typing.cast(str, first_engine_settings['path'])
    nickname = typing.cast(str, first_engine_settings['nickname'])
    with open_engine_with_options(engine_path, engine_options[nickname]) as uci_engine:
        with db_wrapper.Database() as database:
            opex = OpeningExplorer(database, uci_engine)
            board = chess.Board()
            while True:
                opex.search(board)


if __name__ == '__main__':
    main()
