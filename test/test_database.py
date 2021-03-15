import unittest

import chess

from opex import analysis
from opex import database

import typing


class DatabaseTests(unittest.TestCase):

    def test_schema(self):
        with database.Database() as db:
            # Assert that both of our tables are created
            # pylint: disable=protected-access
            cursor = db._db.execute(
                'SELECT count() FROM sqlite_master WHERE type=\'table\' AND (name=\'openings\' OR name=\'game_dag\')')
            self.assertEqual(2, cursor.fetchone()['count()'])
            self.assertEqual(None, cursor.fetchone())

    def test_insert_position(self):
        with database.Database() as db:
            board = chess.Board()
            fen = board.fen()  # type: ignore
            id = db.insert_position(analysis.Position(None, fen, None, None, None, None), None)
            self.assertIsNotNone(id)

    def test_get_position(self):
        with database.Database() as db:
            board = chess.Board()
            fen = board.fen()  # type: ignore
            insert_position = db.insert_position(analysis.Position(None, fen, None, None, None, None), None)
            position = typing.cast(analysis.Position, db.get_position(fen))
            self.assertEqual(insert_position.id, position.id)
