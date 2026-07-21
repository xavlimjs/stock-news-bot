import sqlite3
from contextlib import contextmanager


class SeenStore:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_articles (
                    id TEXT PRIMARY KEY,
                    seen_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def is_new(self, article_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_articles WHERE id = ?", (article_id,)
            ).fetchone()
            return row is None

    def mark_seen(self, article_id: str):
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen_articles (id) VALUES (?)", (article_id,)
            )
