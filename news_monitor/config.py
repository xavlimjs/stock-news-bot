import os
import yaml
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self, path="config.yaml"):
        with open(path, "r") as f:
            raw = yaml.safe_load(f)

        self.tickers = raw["tickers"]
        self.poll_interval_minutes = raw.get("poll_interval_minutes", 10)
        self.allowed_sources = [s.lower() for s in raw.get("allowed_sources", [])]

        self.finnhub_enabled = raw["finnhub"]["enabled"]
        self.finnhub_lookback_days = raw["finnhub"].get("lookback_days", 1)

        self.newsapi_enabled = raw["newsapi"]["enabled"]
        self.newsapi_domains = raw["newsapi"].get("domains", [])
        self.newsapi_lookback_hours = raw["newsapi"].get("lookback_hours", 24)

        self.dedup_db_path = raw.get("dedup_db_path", "seen_articles.db")

        # Secrets from environment / .env
        self.finnhub_api_key = os.getenv("FINNHUB_API_KEY", "")
        self.newsapi_api_key = os.getenv("NEWSAPI_API_KEY", "")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        # Gist-based dedup persistence
        self.gist_token = os.getenv("GIST_TOKEN", "")
        self.gist_id = os.getenv("GIST_ID", "")
        self.gist_filename = os.getenv("GIST_FILENAME", "seen_articles.db.b64")

    def source_allowed(self, source_name: str) -> bool:
        """If allowed_sources is empty, allow everything. Otherwise substring match."""
        if not self.allowed_sources:
            return True
        source_name = (source_name or "").lower()
        return any(allowed in source_name for allowed in self.allowed_sources)