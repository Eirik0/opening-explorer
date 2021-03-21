"""A wrapper around communication with a sqlite database."""

from __future__ import annotations  # PEP 563

import os
import sqlite3
import sys

from opex.analysis import Position

from typing import Any, Dict, Optional, Tuple


def _get_position_or_none(cursor: sqlite3.Cursor) -> Optional[Position]:
    """Gets a single position from a cursor and asserts that there is only one."""
    row = cursor.fetchone()
    if row is None:
        return None
    assert cursor.fetchone() is None
    return Position(row['id'], row['fen'], row['score'], row['depth'], row['pv'])


class Database:
    """A wrapper around database input and output."""

    def _initialize_db(self) -> None:
        """Initialize the database."""
        cursor = self._db.cursor()
        # Expect to find db.schema in same directory as this module
        this_module_dir = os.path.dirname(sys.modules[__name__].__file__)
        schema_path = os.path.join(this_module_dir, 'db.schema')
        with open(schema_path) as schema:
            cursor.executescript(schema.read())

    def __init__(self, path: Optional[str] = None) -> None:
        if path is None:
            path = ':memory:'

        def _dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict[str, Any]:
            named_columns: Dict[str, Any] = {}
            for idx, col in enumerate(cursor.description):
                named_columns[col[0]] = row[idx]
            return named_columns

        self._db = sqlite3.connect(path)
        self._db.row_factory = _dict_factory
        self._initialize_db()

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> Database:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
        self.close()

    def insert_position(self, position: Position, parent_child_relation: Optional[Tuple[int, str]]) -> Position:
        """Insert a position into the database."""
        self._db.execute('BEGIN')
        child_id = self._db.execute(
            'INSERT INTO openings VALUES (?, ?, ?, ?, ?)',
            (None, position.fen, position.score, position.depth, position.pv)).lastrowid
        if parent_child_relation is not None:
            (parent_id, move) = parent_child_relation
            self._db.execute('INSERT INTO game_dag VALUES (?, ?, ?)', (parent_id, child_id, move))
        self._db.execute('END')
        return position.with_position_id(child_id)

    def get_position(self, fen: str) -> Optional[Position]:
        """Retrieve a position from the database."""
        cursor = self._db.execute('SELECT * FROM openings WHERE fen = ?', (fen,))
        return _get_position_or_none(cursor)

    def get_child_positions(self, parent_id: int) -> Dict[str, Position]:
        """Retrieve a list of child positions from the database."""
        cursor = self._db.execute(
            'SELECT '
            '  openings.id, '
            '  openings.fen, '
            '  openings.score, '
            '  openings.depth, '
            '  openings.pv, '
            '  game_dag.move '
            'FROM game_dag '
            'JOIN openings '
            'ON game_dag.child_id = openings.id '
            'WHERE game_dag.parent_id = ? ', (parent_id,))

        positions: Dict[str, Position] = {}
        for row in cursor:
            positions[row['move']] = Position(row['id'], row['fen'], row['score'], row['depth'], row['pv'])

        return positions

    def update_position(self, position: Position) -> Optional[Position]:
        """Update a position in the database."""
        cursor = self._db.execute(
            'UPDATE openings SET score = ?, depth = ?, pv = ?  WHERE id = ?',
            (position.score, position.depth, position.pv, position.position_id))
        return _get_position_or_none(cursor)
