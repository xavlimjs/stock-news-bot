import sqlite3
import logging
from contextlib import contextmanager

log = logging.getLogger("stock_news_bot")


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

    def prune_old(self, days: int = 3):
        """
        Deletes article IDs older than `days` days, based on seen_at.
        Keeps the dedup store (and the Gist it's synced to) from growing
        indefinitely. Safe to call every run.
        """
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM seen_articles WHERE seen_at < datetime('now', ?)",
                (f"-{days} days",),
            )
            deleted = cursor.rowcount
        if deleted:
            log.info("Pruned %d article ID(s) older than %d day(s) from dedup store.", deleted, days)