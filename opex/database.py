import os
import sqlite3
import sys

from opex import analysis


class Database:

    @staticmethod
    def _dict_factory(cursor, row):
        named_columns = dict()
        for idx, col in enumerate(cursor.description):
            named_columns[col[0]] = row[idx]
        return named_columns

    def _initialize_db(self):
        cursor = self._db.cursor()

        # Expect to find db.schema in same directory as this module
        this_module_dir = os.path.dirname(sys.modules[__name__].__file__)
        schema_path = os.path.join(this_module_dir, 'db.schema')

        with open(schema_path) as schema:
            cursor.executescript(schema.read())

    def __init__(self, path=None):
        if path is None:
            path = ":memory:"

        self._db = sqlite3.connect(path)
        self._db.row_factory = Database._dict_factory
        self._initialize_db()

    def close(self):
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def insert_position(self, position, parent_id):
        self._db.execute('BEGIN')

        child_id = self._db.execute(
            "INSERT INTO openings VALUES (?, ?, ?, ?, ?, ?)",
            (None, position.fen, position.move, position.score, position.depth, position.pv)).lastrowid

        self._db.execute("INSERT INTO game_dag VALUES (?, ?)", (parent_id, child_id))

        position.id = child_id

        self._db.execute('END')

        return position

    @staticmethod
    def _rows_to_positions(cursor):
        positions = []
        for row in cursor:
            positions.append(
                analysis.Position(row['id'], row['fen'], row['move'], row['score'], row['depth'], row['pv']))
        return positions

    def get_position(self, fen):
        cursor = self._db.execute("SELECT * FROM openings WHERE fen = ?", (fen,))
        positions = Database._rows_to_positions(cursor)
        assert len(positions) <= 1
        return None if len(positions) == 0 else positions[0]

    def get_child_positions(self, parent_id):
        cursor = self._db.execute(
            "SELECT openings.* FROM game_dag "
            " JOIN openings "
            " ON game_dag.child_id = openings.id "
            " WHERE game_dag.parent_id = ? ", (parent_id,))
        return Database._rows_to_positions(cursor)

    def update_position(self, position):
        cursor = self._db.execute(
            "UPDATE openings SET score = ?, depth = ?, pv = ?  WHERE id = ?",
            (position.score, position.depth, position.pv, position.id))
        positions = Database._rows_to_positions(cursor)
        assert len(positions) <= 1
        return None if len(positions) == 0 else positions[0]
