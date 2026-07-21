"""
Single-run entrypoint, for use with a scheduler that invokes the script
periodically (e.g. GitHub Actions cron) instead of a persistent process.
Unlike main.py, this does NOT loop or sleep - it does one poll cycle and exits.
"""
from news_monitor.config import Config
from news_monitor.dedup import SeenStore
from main import poll_once, log

if __name__ == "__main__":
    config = Config("config.yaml")
    store = SeenStore(config.dedup_db_path)

    tickers = ", ".join(t["symbol"] for t in config.tickers)
    log.info("Running single poll for: %s", tickers)

    poll_once(config, store)
