"""Tests for db_wrapper."""

import unittest

import chess

from opex import db_wrapper
from opex.analysis import ParentRelationship
from opex.analysis import Position

import typing


class TestDBWrapper(unittest.TestCase):

    def test_schema(self):
        with db_wrapper.Database() as database:
            # Assert that both of our tables are created
            # pylint: disable=protected-access
            cursor = database._db.execute(
                'SELECT count() FROM sqlite_master WHERE type=\'table\' AND (name=\'openings\' OR name=\'game_dag\')')
            self.assertEqual(2, cursor.fetchone()['count()'])
            self.assertEqual(None, cursor.fetchone())

    def test_insert_position(self):
        with db_wrapper.Database() as database:
            board = chess.Board()
            fen = board.fen()  # type: ignore
            position_id = database.insert_position(Position(None, fen, 0.0, 1, 'e4'), ParentRelationship(0, 'e2e4'))
            self.assertIsNotNone(position_id)

    def test_get_position(self):
        with db_wrapper.Database() as database:
            board = chess.Board()
            fen = board.fen()  # type: ignore
            insert_position = database.insert_position(Position(None, fen, 0.0, 1, 'e4'), ParentRelationship(0, 'e2e4'))
            position = typing.cast(Position, database.get_position(fen))
            self.assertEqual(insert_position.position_id, position.position_id)
