"""A chess opening explorer"""

#!/usr/bin/env python3

import json
import os

import chess
from chess import engine

from opex import db_wrapper
from opex import settings_loader
from opex.analysis import Position
from opex.settings_loader import Json

import typing
from typing import Any, Dict, List


def open_engine_with_options(path: str, options: engine.ConfigMapping):
    """Opens UCI engine with the specified dictionary of opening options"""
    uci_engine = engine.SimpleEngine.popen_uci(path)
    uci_engine.configure(options)
    return uci_engine


# def back_propagate(position):
#     # TODO
#     pass


def search(database: db_wrapper.Database, uci_engine: engine.SimpleEngine, board: chess.Board):
    """Recursive tree search"""
    fen = board.fen()  # type: ignore
    position = database.get_position(fen)
    if position is None:  # This should only happen for root searches
        position = database.insert_position(
            Position(
                None,  # position_id
                fen,  # fen
                None,  # move
                None,  # score
                None,  # depth
                None),  # pv
            None)  # TODO This should be something in the case that the root search is not from the initial position
    children = database.get_child_positions(typing.cast(int, position.position_id))

    legal_moves = list(board.legal_moves)
    if len(children) == len(legal_moves):
        # TODO find best child and expand
        return

    analyzed_children = {child.move for child in children}

    # TODO Defer inserting the last child until we propagate

    for move in legal_moves:
        move_str = str(move)
        print(move_str)
        if move_str in analyzed_children:
            continue
        board.push(move)
        # TODO try to load this fen as it may be a transposition.
        #  In this case we do not analyze, but still need to update game_dag
        # The following cast should be unnecessary - seems similar to board.fen() type errors
        info = typing.cast(dict[str, Any], uci_engine.analyse(board, engine.Limit(depth=20)))
        # TODO mating score
        fen = board.fen()  # type: ignore
        score = info['score'].relative.score()
        pv = ' '.join([str(move) for move in info['pv']])
        database.insert_position(Position(None, fen, move_str, score, 20, pv), position.position_id)
        board.pop()

    # back_propagate(position)


def ensure_file_exists(file_path: str) -> None:
    """Create a file and its parent directories if it does not exist"""
    parent_directory = os.path.dirname(file_path)
    if parent_directory and not os.path.isdir(parent_directory):
        os.mkdir(parent_directory)
    if not os.path.isfile(file_path):
        with open(file_path, 'w+') as file:
            file.write('')


def load_settings() -> Json:
    """Loads json settings"""
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
    """Loads engine options"""
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
    """Chess opening explorer"""
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
            search(database, uci_engine, chess.Board())
            # for move in board.legal_moves:
            #     board.push(move)
            #     print(info)
            #     board.pop()

    # open database
    # In database, we store:  id, FEN, move (e.g. Nf3), parent id, score, depth, PV
    # tree search algorithm
    #  - evaluate existing at greater depth
    #  - evaluate everything at a fixed depth up to move no
    #    - possibly filter bad moves
    # - can always either add more moves or go deeper
    # - start with depth 10, 20, 30 , 40 , 45 , 50?
    #     -

    # board = chess.Board()
    # limit = 1
    # while True:
    #     search(opening)

    # def search(position):
    #     id = get or create row for position
    #     load rows positions with that id as their parent id
    #     if None
    #         check no legal moves?
    #         expand()
    #         multi pv search for number of moves up to depth 40
    #         create rows
    #         back propagate
    #          - update parents score depth and pv
    #     else
    #         check existance of all rows if one missing start there
    #         find best move
    #         best score = score + uncertainty
    #         position.push(move)
    #         search(position)


if __name__ == '__main__':
    main()
