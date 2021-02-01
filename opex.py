#!/usr/bin/env python

import analysis
import chess  # pip install chess
from chess import engine
import database
import json
import os.path
import sys
import sqlite3


def load_settings():
    """Copy default settings if the settings file does not exist."""
    if not os.path.isfile('settings.json'):
        if not os.path.isfile('settings.json.default'):
            sys.exit('Missing settings.json.default')
        with open('settings.json.default') as default_settings_file:
            default_settings = json.load(default_settings_file)
            default_settings['output_directory'] = "%s\\%s" % (
                os.getcwd(), 'output_directory')
            print('generating settings.json...')
            with open('settings.json', 'w') as settings_file:
                json.dump(default_settings, settings_file, indent=4)
            print(json.dumps(default_settings, indent=2))
            print('...done')
    with open('settings.json') as settings_file:
        return json.load(settings_file)


def check_engine_settings(settings):
    """Error if no engines or if there are duplicates."""
    nicknames = [engine['nickname'] for engine in settings['engines']]
    engines = settings['engines']
    if len(engines) == 0 or len(engines[0]['nickname']) == 0 or len(engines[0]['path']) == 0:
        sys.exit('No engines configured in settings.json')
    for nickname in nicknames:
        if nicknames.count(nickname) > 1:
            sys.exit('duplicate nickname: ' + nickname)


def load_engine_options(options_file_path, default_options):
    """Loads engine options file optionally creating one with default parameters.
    Includes comments about settings in settings file.
    Does not return default values."""
    if not os.path.isfile(options_file_path):
        parent_directory = os.path.dirname(options_file_path)
        if not os.path.isdir(parent_directory):
            os.mkdir(parent_directory)
        # TODO extract a method that takes a list of settings and param for append
        with open(options_file_path, 'w') as settings_file:
            # Find max string length for nice formatting
            max_setting_string_len = 0
            for option_name in default_options:
                option_value = default_options[option_name].default
                if option_value is None:
                    option_value = ''
                name_and_val = "%s=%s" % (option_name, option_value)
                max_setting_string_len = max(
                    max_setting_string_len, len(name_and_val))
            # Save default options
            for option_name in default_options:
                option = default_options[option_name]
                if (option.min or option.max) and option.var:
                    additional_comment = ', min=%d, max=%d, var=%s' % (
                        option.min, option.max, option.var)
                elif option.min or option.max:
                    additional_comment = ', min=%d, max=%d' % (
                        option.min, option.max)
                elif option.var:
                    additional_comment = ', var=%s' % (option.var)
                else:
                    additional_comment = ''
                option_value = default_options[option_name].default
                if option_value is None:
                    option_value = ''
                name_and_val = "%s=%s" % (option_name, option_value)
                settings_file.write("%s # type=%s%s\n" % (
                    name_and_val.ljust(max_setting_string_len + 10), option.type, additional_comment))
    with open(options_file_path) as settings_file:
        options = dict()
        for setting in settings_file.readlines():
            # TODO Missing settings & erroneous settings
            setting = setting.strip()
            if len(setting) == 0 or setting.startswith('#'):
                continue
            setting = setting.split('#')[0].rstrip()
            setting_split = setting.split('=')
            if len(setting_split) == 2:
                name = setting_split[0]
                value = setting_split[1]
                default_value = default_options[name].default
                if default_value is None:
                    default_value = ''
                else:
                    default_value = str(default_value)

                if value != default_value:
                    options[name] = value
        return options


def load_all_engine_options(settings):
    engine_options = dict()
    for engine in settings['engines']:
        with chess.engine.SimpleEngine.popen_uci(engine['path']) as uci_engine:
            nickname = engine['nickname']
            options_file_path = ("%s\\%s.uci") % (
                settings['output_directory'], nickname)
            engine_options[nickname] = load_engine_options(
                options_file_path, uci_engine.options)
    return engine_options

def open_engine_with_options(path, options):
    """Opens UCI engine with the specified dictionary of opening options"""
    engine = chess.engine.SimpleEngine.popen_uci(path)
    engine.configure(options)
    return engine

def main():
    settings = load_settings()

    check_engine_settings(settings)

    engine_options = load_all_engine_options(settings)
    first_engine_settings = settings['engines'][0]

    # WIP select arbitrary engine from list
    with open_engine_with_options(
        first_engine_settings['path'],
        engine_options[first_engine_settings['nickname']]) as engine, database.Database() as db:
        board = chess.Board()
        print(db.insert(analysis.Position(
            None,
            None,
            board.fen(),
            None,
            None,
            None,
            None
        )))
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
