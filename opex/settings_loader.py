import json
import os.path

from chess import engine

import typing
from typing import Dict, List, TextIO, Tuple, Union

Json = Dict[str, 'JsonValue']
JsonValue = Union[str, int, bool, Json, List['JsonValue']]

EngineOptions = Dict[str, Union[str, int, bool]]

DEFAULT_SETTINGS_FILE_NAME = 'opex-default-settings.json'

## Methods for loading json settings


def _json_from_file(file: TextIO) -> Json:
    if os.path.getsize(file.name) > 0:
        return typing.cast(Json, json.load(file))
    return {}


def load_default_settings() -> Json:
    with open(DEFAULT_SETTINGS_FILE_NAME) as settings_file:
        return _json_from_file(settings_file)


def load_settings_simple(settings_file: TextIO):
    return _json_from_file(settings_file)


def _merge_settings(default_settings: JsonValue, user_settings: JsonValue, use_default_values: bool) -> JsonValue:
    if isinstance(default_settings, dict):
        user_settings = typing.cast(Json, user_settings)
        for key, default_value in default_settings.items():
            if key not in user_settings:
                user_settings[key] = _merge_settings(default_value, {}, use_default_values)
            elif isinstance(default_value, (dict, list)):
                user_settings[key] = _merge_settings(default_value, user_settings[key], use_default_values)
            elif user_settings[key] == '' and use_default_values:
                user_settings[key] = default_value
        return user_settings
    if isinstance(default_settings, list):
        # In this case, assume that there is only one item in default_settings
        user_settings = typing.cast(List[JsonValue], user_settings)
        if user_settings is None or len(user_settings) == 0:
            return default_settings
        updated_settings: List[JsonValue] = []
        for setting in user_settings:
            updated_settings.append(_merge_settings(default_settings[0], setting, use_default_values))
        return updated_settings
    return default_settings if use_default_values else ''


def load_settings(user_settings_file: TextIO, use_default_values: bool = True):
    default_settings = load_default_settings()
    user_settings = load_settings_simple(user_settings_file)
    return _merge_settings(default_settings, user_settings, use_default_values)


## Methods for loading engine settings and options


def _raise_if_duplicates(counts: Dict[str, int]) -> None:
    duplicates: List[str] = []
    for nickname, count in counts.items():
        if count > 1:
            duplicates.append(nickname)
    if len(duplicates) > 0:
        # TODO This is not always nickname
        raise ValueError(f'\'nickname\' not unique {duplicates}')


def check_engine_settings(engine_settings_list: List[Json]) -> None:
    if len(engine_settings_list) == 0:
        raise ValueError('Engine list was empty')
    nickname_counts: Dict[str, int] = {}
    for i, engine_settings in enumerate(engine_settings_list):
        for key in ['nickname', 'path']:
            if key not in engine_settings:
                raise ValueError(f'Engine[{i}] missing \'{key}\'')
            if engine_settings[key] == '':
                raise ValueError(f'Engine[{i}] missing value for \'{key}\'')
        # Count duplicates
        nickname = typing.cast(str, engine_settings['nickname'])
        if nickname not in nickname_counts:
            nickname_counts[nickname] = 0
        nickname_counts[nickname] = nickname_counts[nickname] + 1
    _raise_if_duplicates(nickname_counts)


def load_engine_options_simple(engine_options_file: TextIO) -> EngineOptions:
    options: EngineOptions = {}
    name_counts: Dict[str, int] = {}
    for line_in_file in engine_options_file.read().splitlines():
        line = line_in_file.strip()
        if line == '' or line.startswith('#'):
            continue
        line = line.split('#')[0].rstrip()
        if '=' not in line:
            raise ValueError(f'Missing \'=\' on line \'{line_in_file}\'')
        if line.startswith('='):
            raise ValueError(f'Missing option name on line \'{line_in_file}\'')
        (name, value) = line.split('=', maxsplit=1)
        if name in options:
            raise ValueError(f'Duplicate engine option \'{name}\'')
        lower_case_value = value.lower()
        if lower_case_value in ('true', 'false'):
            value = lower_case_value == 'true'
        else:
            try:
                value = int(value)
            except ValueError:
                pass
        options[name] = value
        # Count duplicates
        if name not in name_counts:
            name_counts[name] = 0
        name_counts[name] = name_counts[name] + 1
    _raise_if_duplicates(name_counts)
    return options


def load_engine_options(
        default_options: List[engine.Option],
        options_file: TextIO,
        exclude_default_values: bool = True) -> EngineOptions:

    def is_empty(value: engine.ConfigValue):
        return value is None or value == '<empty>'

    engine_options: EngineOptions = {}
    full_engine_options = load_engine_options_simple(options_file)
    for option in default_options:
        default_value = option.default
        if option.is_managed() or option.type == 'button':
            continue
        name = option.name
        if name in full_engine_options:
            value = full_engine_options[name]
            if exclude_default_values and (default_value == value or (is_empty(default_value) and value == '')):
                continue
            engine_options[name] = value
        elif not exclude_default_values:
            engine_options[name] = default_value if default_value is not None else ''
    return engine_options


def check_engine_options(default_options: List[engine.Option], engine_options: EngineOptions) -> None:

    def check_check(value: engine.ConfigValue):
        if not isinstance(value, bool):
            raise ValueError(f'Value \'{value}\' for \'{name}\' not a boolean')

    def check_spin(option: engine.Option, value: engine.ConfigValue):
        if not isinstance(value, int):
            raise ValueError(f'Value \'{value}\' for \'{name}\' not an integer')
        if value < typing.cast(int, option.min) or value > typing.cast(int, option.max):
            raise ValueError(f'Value \'{value}\' for \'{name}\' not in range [{option.min}, {option.max}]')

    def check_combo(option: engine.Option, value: engine.ConfigValue):
        if value not in option.var:
            raise ValueError(f'Value \'{value}\' for \'{name}\' not in {option.var}')

    managed_options: List[str] = []
    button_options: List[str] = []
    found_names = set()
    for option in default_options:
        name = option.name
        if name not in engine_options:
            continue
        if option.is_managed():
            managed_options.append(name)
            continue
        if option.type == 'button':
            button_options.append(name)
            continue
        value = engine_options[name]
        if option.type == 'check':
            check_check(value)
        elif option.type == 'spin':
            check_spin(option, value)
        elif option.type == 'combo':
            check_combo(option, value)
        found_names.add(name)
    if len(managed_options) > 0:
        raise ValueError(f'Cannot set managed options {managed_options}')
    if len(button_options) > 0:
        raise ValueError(f'Cannot set button options {button_options}')
    unknown_names = [name for name in engine_options if name not in found_names]
    if len(unknown_names) > 0:
        raise ValueError(f'Unknown options {unknown_names}')


def _engine_option_string_and_comment(option: engine.Option, value: engine.ConfigValue) -> Tuple[str, str]:
    if value is None:
        value = ''
    name_equals_val = f'{option.name}={value}'
    if option.type == 'check' or option.type == 'string' or option.type == 'button':
        return (name_equals_val, f'type={option.type}')
    if option.type == 'spin':
        return (name_equals_val, f'type=spin, min={option.min}, max={option.max}')
    if option.type == 'combo':
        return (name_equals_val, f'type=combo, var={option.var}')
    return (name_equals_val, 'type=unknown')


def engine_options_file_lines(default_options: List[engine.Option], user_options: EngineOptions) -> List[str]:
    option_infos: List[Tuple[str, str]] = []
    for option in default_options:
        if option.is_managed() or option.type == 'button':
            continue
        value = user_options[option.name] if option.name in user_options else option.default
        option_infos.append(_engine_option_string_and_comment(option, value))
    max_name_and_val_length = max([len(option_info[0]) for option_info in option_infos])
    lines: List[str] = []
    for name_and_val, comment in option_infos:
        lines.append(f'{name_and_val.ljust(max_name_and_val_length + 10)} # {comment}\n')
    return lines
