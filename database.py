import sqlite3
import os

class Database:
    def _initialize_db(self):
        # TODO: indices
        c = self._db.cursor()
        with open('db.schema') as schema:
            c.executescript(schema.read())

    def __init__(self, path=None):
        if path is None:
            path = ":memory:"

        self._db = sqlite3.connect(path)
        self._initialize_db()

    def close(self):
        print("openings table:")
        cursor = self._db.execute("SELECT * FROM openings")
        for row in cursor:
            print(row)

        print("game_dag table:")
        cursor = self._db.execute("SELECT * FROM game_dag")
        for row in cursor:
            print(row)

        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def insert(self, position):
        child_id = self._db.execute("INSERT INTO openings VALUES (?, ?, ?, ?, ?, ?)", (
            None,
            position.fen,
            position.move,
            position.score,
            position.depth,
            position.pv)).lastrowid

        self._db.execute("INSERT INTO game_dag VALUES (?, ?)", (position.parent_id, child_id))

        return child_id