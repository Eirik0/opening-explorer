import json
import os.path

import chess
import chess.engine

DEFAULT_SETTINGS_FILE_NAME = 'opex-default-settings.json'


def _json_from_file(file):
    return json.load(file) if os.path.getsize(file.name) > 0 else dict()


def load_default_settings():
    with open(DEFAULT_SETTINGS_FILE_NAME) as settings_file:
        return _json_from_file(settings_file)


def load_settings_simple(settings_file):
    return _json_from_file(settings_file)


def _merge_settings(default_settings, user_settings, use_default_values):
    if isinstance(default_settings, dict):
        if user_settings is None:
            user_settings = dict()
        for key, default_value in default_settings.items():
            if key not in user_settings:
                user_settings[key] = _merge_settings(default_value, None, use_default_values)
            elif isinstance(default_value, (dict, list)):
                user_settings[key] = _merge_settings(default_value, user_settings[key], use_default_values)
            elif user_settings[key] == '' and use_default_values:
                user_settings[key] = default_value
        return user_settings
    if isinstance(default_settings, list):
        # Assume that there is only one item in default_settings
        if user_settings is None or len(user_settings) == 0:
            return default_settings
        updated_settings = []
        for setting in user_settings:
            updated_settings.append(_merge_settings(default_settings[0], setting, use_default_values))
        return updated_settings
    return default_settings if use_default_values else ''


def load_settings(user_settings_file, use_default_values=True):
    default_settings = load_default_settings()
    user_settings = load_settings_simple(user_settings_file)
    return _merge_settings(default_settings, user_settings, use_default_values)


def check_engine_settings(engine_settings_list):
    if len(engine_settings_list) == 0:
        raise ValueError('Engine list was empty')
    nickname_counts = dict()
    for i, engine_settings in enumerate(engine_settings_list):
        for key in ['nickname', 'path']:
            if key not in engine_settings:
                raise ValueError('Engine[%d] missing \'%s\'' % (i, key))
            if engine_settings[key] == '':
                raise ValueError('Engine[%d] missing value for \'%s\'' % (i, key))
        nickname = engine_settings['nickname']
        if nickname not in nickname_counts:
            nickname_counts[nickname] = 0
        nickname_counts[nickname] = nickname_counts[nickname] + 1
    duplicates = []
    for nickname, count in nickname_counts.items():
        if count > 1:
            duplicates.append(nickname)
    if len(duplicates) > 0:
        raise ValueError('\'nickname\' not unique %s' % (duplicates))


# def _uci_options_from_file(file):
#     pass


# def load_engine_options(default_options, options_file, exclude_default_values=True):
#     pass


# pylint: disable=too-many-locals,too-many-branches
def load_engine_options2(default_options, options_file_path):
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
                    name_and_val.ljust(max_setting_string_len + 10),
                    option.type,
                    additional_comment))

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
            options_file_path = ("%s\\%s.uci") % (settings['engine_options_directory'], nickname)
            engine_options[nickname] = load_engine_options2(uci_engine.options, options_file_path)
    return engine_options
