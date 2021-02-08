import json
import os
import tempfile
import unittest

import chess.engine

from opex import settings_loader

# Option(name(str), type(str), default(str, int, bool, None), min(None, int), max(None, int), var(None, List[int]))
TEST_ENGINE_OPTIONS = [chess.engine.Option('uci_chess960', 'check', 'false', None, None, None),  # managed
                       chess.engine.Option('multipv', 'spin', 1, 1, 500, None),  # managed
                       chess.engine.Option('ponder', 'check', 'false', None, None, None),  # managed
                       chess.engine.Option('string_none', 'string', None, None, None, None),
                       chess.engine.Option('string_blank', 'string', '', None, None, None),
                       chess.engine.Option('string_empty', 'string', '<empty>', None, None, None),
                       chess.engine.Option('string_something', 'string', 'something', None, None, None),
                       chess.engine.Option('spin', 'spin', 0, -100, 100, None),
                       chess.engine.Option('combo', 'combo', 'one', None, None, ['one', 'two', 'three']),
                       chess.engine.Option('button_1', 'button', None, None, None, None),
                       chess.engine.Option('button_2', 'button', None, None, None, None),
                       chess.engine.Option('check_true', 'check', 'true', None, None, None),
                       chess.engine.Option('check_false', 'check', 'false', None, None, None)]

# Does not include managed options or options with type `button`
TEST_ENGINE_OPTIONS_DICT = {'string_none': None,
                            'string_blank': '',
                            'string_empty': '<empty>',
                            'string_something': 'something',
                            'spin': 0,
                            'combo': 'one',
                            'check_true': True,
                            'check_false': False}


class SettingsLoaderTests(unittest.TestCase):
    def test_default_settings_file__exits(self):
        self.assertTrue(os.path.isfile(settings_loader.DEFAULT_SETTINGS_FILE_NAME))

    def test_default_settings__has_expected_keys(self):
        settings = settings_loader.load_default_settings()
        self.assertTrue('data_directory' in settings)
        self.assertTrue('engine_options_directory' in settings)
        self.assertTrue('engines' in settings)
        self.assertEqual(1, len(settings['engines']))
        self.assertTrue('nickname' in settings['engines'][0])
        self.assertTrue('path' in settings['engines'][0])

    def test_load_settings__empty_file__loads_defaults(self):
        with tempfile.NamedTemporaryFile() as settings_file:
            default_settings = settings_loader.load_default_settings()
            self.assertEqual(default_settings, settings_loader.load_settings(settings_file))

    def test_load_settings__use_defaults_false__empty_file__loads_default_keys(self):
        with tempfile.NamedTemporaryFile() as settings_file:
            default_settings = settings_loader.load_default_settings()
            default_settings['data_directory'] = ''
            default_settings['engine_options_directory'] = ''
            self.assertEqual(default_settings, settings_loader.load_settings(settings_file, False))

    def test_load_settings__use_defaults_false__after_save__loads_default_keys(self):
        with tempfile.NamedTemporaryFile(mode='r+') as settings_file:
            default_settings = settings_loader.load_default_settings()
            default_settings['data_directory'] = ''
            default_settings['engine_options_directory'] = ''
            settings = settings_loader.load_settings(settings_file, False)
            json.dump(settings, settings_file)
            settings_file.seek(0)
            self.assertEqual(default_settings, settings_loader.load_settings(settings_file, False))

    def test_load_settings__missing_key__is_populated(self):
        with tempfile.NamedTemporaryFile(mode='r+') as settings_file:
            settings = settings_loader.load_settings(settings_file)
            del settings['data_directory']
            json.dump(settings, settings_file)
            settings_file.seek(0)
            self.assertEqual(settings_loader.load_default_settings(), settings_loader.load_settings(settings_file))

    def test_load_settings__missing_key_to_dict__is_populated(self):
        with tempfile.NamedTemporaryFile(mode='r+') as settings_file:
            settings = settings_loader.load_settings(settings_file)
            del settings['data_directory']
            json.dump(settings, settings_file)
            settings_file.seek(0)
            self.assertEqual(settings_loader.load_default_settings(), settings_loader.load_settings(settings_file))

    def test_load_settings__missing_subkey__is_populated(self):
        with tempfile.NamedTemporaryFile(mode='r+') as settings_file:
            settings = settings_loader.load_settings(settings_file)
            del settings['engines'][0]['nickname']
            json.dump(settings, settings_file)
            settings_file.seek(0)
            self.assertEqual(settings_loader.load_default_settings(), settings_loader.load_settings(settings_file))

    def test_load_settings__missing_key_in_list__other_keys_preserved(self):
        with tempfile.NamedTemporaryFile(mode='r+') as settings_file:
            settings = settings_loader.load_settings(settings_file)
            settings['engines'][0]['nickname'] = 'test1'
            settings['engines'].append({'nickname': 'test2'})
            json.dump(settings, settings_file)
            settings_file.seek(0)
            settings = settings_loader.load_settings(settings_file)
            self.assertTrue('engines' in settings)
            self.assertEqual(2, len(settings['engines']))
            self.assertEqual({'nickname': 'test1', 'path': ''}, settings['engines'][0])
            self.assertEqual({'nickname': 'test2', 'path': ''}, settings['engines'][1])

    def test_load_settings__after_save__default_values_are_populates(self):
        with tempfile.NamedTemporaryFile(mode='r+') as settings_file:
            settings = settings_loader.load_settings(settings_file, False)
            json.dump(settings, settings_file)
            settings_file.seek(0)
            self.assertEqual(settings_loader.load_default_settings(), settings_loader.load_settings(settings_file))

    def test_check_engine_settings__no_engines(self):
        with self.assertRaises(ValueError) as error:
            settings_loader.check_engine_settings([])
        self.assertTrue('Engine list was empty' in str(error.exception))

    def test_check_engine_settings__one_engine_no_nickname(self):
        with self.assertRaises(ValueError) as error:
            settings_loader.check_engine_settings([{'path': 'test'}])
        self.assertTrue('Engine[0] missing \'nickname\'' in str(error.exception))

    def test_check_engine_settings__one_engine_no_path(self):
        with self.assertRaises(ValueError) as error:
            settings_loader.check_engine_settings([{'nickname': 'test'}])
        self.assertTrue('Engine[0] missing \'path\'' in str(error.exception))

    def test_check_engine_settings__one_engine_nickname_not_set(self):
        with self.assertRaises(ValueError) as error:
            settings_loader.check_engine_settings([{'nickname': '', 'path': 'test'}])
        self.assertTrue('Engine[0] missing value for \'nickname\'' in str(error.exception))

    def test_check_engine_settings__second_engine_path_not_set(self):
        with self.assertRaises(ValueError) as error:
            settings_loader.check_engine_settings(
                [{'nickname': 'test', 'path': 'test'}, {'nickname': 'test', 'path': ''}])
        self.assertTrue('Engine[1] missing value for \'path\'' in str(error.exception))

    def test_check_engine_settings__duplicate_nicknames(self):
        with self.assertRaises(ValueError) as error:
            settings_loader.check_engine_settings(
                [{'nickname': 'test', 'path': 'test'}, {'nickname': 'test', 'path': 'test'}])
        self.assertTrue('\'nickname\' not unique [\'test\']' in str(error.exception))

    def test_check_engine_settings__multiple_duplicate_nicknames(self):
        with self.assertRaises(ValueError) as error:
            settings_loader.check_engine_settings(
                [{'nickname': 'test1', 'path': 'test'}, {'nickname': 'test1', 'path': 'test'},
                 {'nickname': 'test2', 'path': 'test'},
                 {'nickname': 'test3', 'path': 'test'}, {'nickname': 'test3', 'path': 'test'}])
        self.assertTrue('\'nickname\' not unique [\'test1\', \'test3\']' in str(error.exception))

    def test_load_engine_options__empty_file__loads_empty_options(self):
        with tempfile.NamedTemporaryFile() as options_file:
            options = settings_loader.load_engine_options(TEST_ENGINE_OPTIONS, options_file)
            self.assertEqual(dict(), options)

    def test_load_engine_options__exlucde_defaults_false__empty_file__loads_defaults(self):
        with tempfile.NamedTemporaryFile() as options_file:
            options = settings_loader.load_engine_options(TEST_ENGINE_OPTIONS, options_file, False)
            self.assertEqual(TEST_ENGINE_OPTIONS_DICT, options)

    def test_load_engine_options__after_save__loads_empty_options(self):
        with tempfile.NamedTemporaryFile(mode='r+') as options_file:
            options_file.write(
                settings_loader.engine_options_file_string(TEST_ENGINE_OPTIONS, TEST_ENGINE_OPTIONS_DICT))
            options_file.seek(0)
            options = settings_loader.load_engine_options(TEST_ENGINE_OPTIONS, options_file)
            self.assertEqual(dict(), options)

    def test_load_engine_options__exlucde_defaults_false__after_save__loads_defaults(self):
        with tempfile.NamedTemporaryFile(mode='r+') as options_file:
            options_file.write(
                settings_loader.engine_options_file_string(TEST_ENGINE_OPTIONS, TEST_ENGINE_OPTIONS_DICT))
            options_file.seek(0)
            options = settings_loader.load_engine_options(TEST_ENGINE_OPTIONS, options_file, False)
            self.assertEqual(TEST_ENGINE_OPTIONS_DICT, options)

    def test_load_engine_options__modified_options__after_save__loads_modified_options(self):
        with tempfile.NamedTemporaryFile(mode='r+') as options_file:
            modified_options = {'string_none': 'test', 'spin': 100, 'combo': 'two', 'check_true': False}
            options_file.write(settings_loader.engine_options_file_string(TEST_ENGINE_OPTIONS, modified_options))
            options_file.seek(0)
            options = settings_loader.load_engine_options(TEST_ENGINE_OPTIONS, options_file)
            self.assertEqual(modified_options, options)

    def test_load_engine_options__exlucde_defaults_false__modified_options__after_save__loads_modified_options(self):
        with tempfile.NamedTemporaryFile(mode='r+') as options_file:
            modified_options = {'string_none': 'test', 'spin': 100, 'combo': 'two', 'check_true': False}
            options_file.write(settings_loader.engine_options_file_string(TEST_ENGINE_OPTIONS, modified_options))
            options_file.seek(0)
            options = settings_loader.load_engine_options(TEST_ENGINE_OPTIONS, options_file, False)
            all_options = {key: modified_options['key'] if key in modified_options else value
                           for key, value in TEST_ENGINE_OPTIONS_DICT.items()}
            self.assertEqual(all_options, options)

    def test_load_engine_options__after_save__default_option_added__loads_updated_options(self):
        with tempfile.NamedTemporaryFile(mode='r+') as options_file:
            options_file.write(
                settings_loader.engine_options_file_string(TEST_ENGINE_OPTIONS, TEST_ENGINE_OPTIONS_DICT))
            options_file.seek(0)
            updated_default_options = TEST_ENGINE_OPTIONS.copy()
            updated_default_options.append(chess.engine.Option('new', 'string', None, None, None, None))
            options = settings_loader.load_engine_options(TEST_ENGINE_OPTIONS, options_file, False)
            expected_options = TEST_ENGINE_OPTIONS_DICT.copy()
            expected_options['new'] = ''
            self.assertEqual(expected_options, options)

    def test_engine_options_file_string__default_options(self):
        expected_file_string = (
            'string_none=                         # type=string\n'
            'string_blank=                        # type=string\n'
            'string_empty=<empty>                 # type=string\n'
            'string_something=something           # type=string\n'
            'spin=0                               # type=spin, min=-100, max=100\n'
            'combo=one                            # type=combo, var=[\'one\', \'two\', \'three\']\n'
            'check_true=True                      # type=check\n'
            'check_false=False                    # type=check\n')
        self.assertEqual(expected_file_string,
                         settings_loader.engine_options_file_string(TEST_ENGINE_OPTIONS, TEST_ENGINE_OPTIONS_DICT))

    def test_engine_options_file_string__longer_string__more_whitespace(self):
        expected_file_string = (
            'string_none=                                       # type=string\n'
            'string_blank=                                      # type=string\n'
            'string_empty=<empty>                               # type=string\n'
            'string_something=this is a longer string           # type=string\n'
            'spin=0                                             # type=spin, min=-100, max=100\n'
            'combo=one                                          # type=combo, var=[\'one\', \'two\', \'three\']\n'
            'check_true=True                                    # type=check\n'
            'check_false=False                                  # type=check\n')
        modified_options = TEST_ENGINE_OPTIONS_DICT.copy()
        modified_options['string_something'] = 'this is a longer string'
        self.assertEqual(expected_file_string,
                         settings_loader.engine_options_file_string(TEST_ENGINE_OPTIONS, modified_options))

    def test_engine_options__duplicate_option__error_when_loading(self):
        with self.assertRaises(ValueError) as error:
            with tempfile.NamedTemporaryFile(mode='r+') as options_file:
                file_string = (
                    'string_none=           # type=string\n'
                    'string_none=           # type=string\n')
                options_file.write(file_string)
                options_file.seek(0)
        self.assertTrue('Duplicate engine options [\'string_none\']' in str(error.exception))

    def test_engine_options__multiple_duplicate_option__error_when_loading(self):
        with self.assertRaises(ValueError) as error:
            with tempfile.NamedTemporaryFile(mode='r+') as options_file:
                file_string = (
                    'string_none=            # type=string\n'
                    'string_none=            # type=string\n'
                    'string_blank=           # type=string\n'
                    'string_blank=           # type=string\n')
                options_file.write(file_string)
                options_file.seek(0)
        self.assertTrue('Duplicate engine options [\'string_none\', \'string_blank\']' in str(error.exception))

    def test_check_engine_options__managed_option(self):
        with self.assertRaises(ValueError) as error:
            options = TEST_ENGINE_OPTIONS_DICT.copy()
            options['uci_chess960'] = True
            options['uci_variant'] = None
            options['multipv'] = 2
            options['ponder'] = True
            settings_loader.check_engine_options(TEST_ENGINE_OPTIONS, options)
        error_msg = 'Cannot set managed options [\'uci_chess960\', \'uci_variant\', \'multipv\', \'ponder\']'
        self.assertTrue(error_msg in str(error.exception))

    def test_check_engine_options__button_option(self):
        with self.assertRaises(ValueError) as error:
            options = TEST_ENGINE_OPTIONS_DICT.copy()
            options['button1'] = None
        self.assertTrue('Cannot set button options [\'button1\']' in str(error.exception))

    def test_check_engine_options__multiple_button_option(self):
        with self.assertRaises(ValueError) as error:
            options = TEST_ENGINE_OPTIONS_DICT.copy()
            options['button1'] = None
            options['button2'] = None
        self.assertTrue('Cannot set button options [\'button1\', \'button2\']' in str(error.exception))

    def test_check_engine_options__spin_type__value_out_of_range(self):
        with self.assertRaises(ValueError) as error:
            options = TEST_ENGINE_OPTIONS_DICT.copy()
            options['spin'] = -101
            settings_loader.check_engine_options(TEST_ENGINE_OPTIONS, options)
        self.assertTrue('Value \'-101\' for \'spin\' not in range [-100, 100]' in str(error.exception))

    def test_check_engine_options__spin_type__not_integer(self):
        with self.assertRaises(ValueError) as error:
            options = TEST_ENGINE_OPTIONS_DICT.copy()
            options['spin'] = 'test'
            settings_loader.check_engine_options(TEST_ENGINE_OPTIONS, options)
        self.assertTrue('Value \'test\' for \'spin\' not an integer' in str(error.exception))

    def test_check_engine_options__combo_type__not_in_list(self):
        with self.assertRaises(ValueError) as error:
            options = TEST_ENGINE_OPTIONS_DICT.copy()
            options['combo'] = 'four'
            settings_loader.check_engine_options(TEST_ENGINE_OPTIONS, options)
        self.assertTrue('Value \'four\' for \'combo\' not in [\'one\', \'two\', \'three\']' in str(error.exception))
