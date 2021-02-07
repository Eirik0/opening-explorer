import json
import os
import tempfile
import unittest

from opex import settings_loader


def remove_values(settings):
    if isinstance(settings, dict):
        for key, value in settings.items():
            settings[key] = remove_values(value)
        return settings
    if isinstance(settings, list):
        return settings
    return ''


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
            default_settings = remove_values(settings_loader.load_default_settings())
            self.assertEqual(default_settings, settings_loader.load_settings(settings_file, False))

    def test_load_settings__use_defaults_false__after_safe__loads_default_keys(self):
        with tempfile.NamedTemporaryFile(mode='r+') as settings_file:
            default_settings = remove_values(settings_loader.load_default_settings())
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

    def test_load_engine_options__exlucde_defaults_false__empty_file__loads_defaults(self):
        pass

    def test_load_engine_options__empty_file__loads_empty_options(self):
        pass

    # TODO check excludes managed options

    # TODO save file with defaults then check empty options

    # TODO save and override one

    # TODO tests for saving to file with nice formatting
