from __future__ import annotations  # PEP 563

import os
import sqlite3
import sys

from opex.analysis import Position

from typing import Any, Dict, List, Optional


def _rows_to_positions(cursor: sqlite3.Cursor) -> List[Position]:
    positions: List[Position] = []
    for row in cursor:
        positions.append(Position(row['id'], row['fen'], row['move'], row['score'], row['depth'], row['pv']))
    return positions


class Database:

    def _initialize_db(self) -> None:
        cursor = self._db.cursor()
        # Expect to find db.schema in same directory as this module
        this_module_dir = os.path.dirname(sys.modules[__name__].__file__)
        schema_path = os.path.join(this_module_dir, 'db.schema')
        with open(schema_path) as schema:
            cursor.executescript(schema.read())

    def __init__(self, path: Optional[str] = None) -> None:
        if path is None:
            path = ':memory:'

        def _dict_factory(cursor: sqlite3.Cursor, row: Any) -> Dict[str, Any]:
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

    def __exit__(self, type: Any, value: Any, traceback: Any) -> None:
        self.close()

    def insert_position(self, position: Position, parent_id: Optional[int]) -> Position:
        self._db.execute('BEGIN')
        child_id = self._db.execute(
            'INSERT INTO openings VALUES (?, ?, ?, ?, ?, ?)',
            (None, position.fen, position.move, position.score, position.depth, position.pv)).lastrowid
        self._db.execute('INSERT INTO game_dag VALUES (?, ?)', (parent_id, child_id))
        self._db.execute('END')
        return position.with_position_id(child_id)

    def get_position(self, fen: str) -> Optional[Position]:
        cursor = self._db.execute('SELECT * FROM openings WHERE fen = ?', (fen,))
        positions = _rows_to_positions(cursor)
        assert len(positions) <= 1
        return None if len(positions) == 0 else positions[0]

    def get_child_positions(self, parent_id: int) -> List[Position]:
        cursor = self._db.execute(
            'SELECT openings.* FROM game_dag '
            ' JOIN openings '
            ' ON game_dag.child_id = openings.id '
            ' WHERE game_dag.parent_id = ? ', (parent_id,))
        return _rows_to_positions(cursor)

    def update_position(self, position: Position) -> Optional[Position]:
        cursor = self._db.execute(
            'UPDATE openings SET score = ?, depth = ?, pv = ?  WHERE id = ?',
            (position.score, position.depth, position.pv, position.position_id))
        positions = _rows_to_positions(cursor)
        assert len(positions) <= 1
        return None if len(positions) == 0 else positions[0]
