#!/usr/bin/env python3

import json
import os

import chess
import chess.engine

from opex import analysis
from opex import database
from opex import settings_loader


def open_engine_with_options(path, options):
    """Opens UCI engine with the specified dictionary of opening options"""
    engine = chess.engine.SimpleEngine.popen_uci(path)
    engine.configure(options)
    return engine


def back_propagate(position):  # pylint: disable=unused-argument
    # TODO
    pass


def search(db, engine, board):
    position = db.get_position(board.fen())
    if position is None:  # This should only happen for root searches
        position = db.insert_position(
            analysis.Position(
                None,  # id
                board.fen(),  # fen
                None,  # move
                None,  # score
                None,  # depth
                None),  # pv
            None)  # TODO This should be something in the case that the root search is not from the initial position

    children = db.get_child_positions(position.id)

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
        # In this case we do not analyze, but still need to update game_dag
        info = engine.analyse(board, chess.engine.Limit(depth=20))
        # TODO mating score
        score = info['score'].relative.score()
        pv = ' '.join([str(move) for move in info['pv']])
        db.insert_position(analysis.Position(None, board.fen(), move_str, score, 20, pv), position.id)
        board.pop()

    back_propagate(position)


def ensure_file_exists(file_path):
    parent_directory = os.path.dirname(file_path)
    if parent_directory != '' and not os.path.isdir(parent_directory):
        os.mkdir(parent_directory)
    if not os.path.isfile(file_path):
        with open(file_path, 'w+') as file:
            file.write('')


def load_settings():
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


def load_all_engine_options(settings):
    engine_options = dict()
    for engine_setting in settings['engines']:
        nickname = engine_setting['nickname']
        path = engine_setting['path']
        with chess.engine.SimpleEngine.popen_uci(path) as uci_engine:
            default_options = [option for _, option in uci_engine.options.items()]
        engine_options_directory = settings['engine_options_directory']
        options_file_path = f'{engine_options_directory}\\{nickname.uci}'
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
    settings = load_settings()

    settings_loader.check_engine_settings(settings['engines'])

    engine_options = load_all_engine_options(settings)
    first_engine_settings = settings['engines'][0]

    with open_engine_with_options(
            first_engine_settings['path'],
            engine_options[first_engine_settings['nickname']]) as engine, database.Database() as db:
        search(db, engine, chess.Board())
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


if __name__ == "__main__":
    main()
