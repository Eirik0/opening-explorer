import unittest

from opex.database import Database


class DatabaseTests(unittest.TestCase):
    # pylint: disable=protected-access
    def test_schema(self):
        db = Database()

        # Assert that both of our tables are created
        cursor = db._db.execute(
            "SELECT count() FROM sqlite_schema WHERE type='table' AND (name='openings' OR name='game_dag')")
        self.assertEqual(2, cursor.fetchone()[0])
        self.assertEqual(None, cursor.fetchone())


if __name__ == "__main__":
    unittest.main()
