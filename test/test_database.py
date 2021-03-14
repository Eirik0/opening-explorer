import unittest

import chess

from opex import analysis
from opex import database


class DatabaseTests(unittest.TestCase):
    # pylint: disable=protected-access
    def test_schema(self):
        with database.Database() as db:
            # Assert that both of our tables are created
            cursor = db._db.execute(
                'SELECT count() FROM sqlite_master WHERE type=\'table\' AND (name=\'openings\' OR name=\'game_dag\')')
            self.assertEqual(2, cursor.fetchone()['count()'])
            self.assertEqual(None, cursor.fetchone())

    def test_insert_position(self):
        with database.Database() as db:
            board = chess.Board()
            id = db.insert_position(analysis.Position(None, board.fen(), None, None, None, None), None)
            self.assertIsNotNone(id)

    def test_get_position(self):
        with database.Database() as db:
            board = chess.Board()
            insert_position = db.insert_position(analysis.Position(None, board.fen(), None, None, None, None), None)
            get_position = db.get_position(board.fen())
            self.assertEqual(insert_position.id, get_position.id)
