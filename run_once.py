"""
Single-run entrypoint, for use with an external scheduler (e.g. cron-job.org
triggering a GitHub Actions workflow_dispatch) instead of a persistent process.
Unlike main.py, this does NOT loop or sleep - it does one poll cycle and exits.
Dedup state (seen_articles.db) is pulled from / pushed to a GitHub Gist around
the poll, so it survives across runs without ever touching git history.
"""
from news_monitor import gist_sync
from news_monitor.config import Config
from news_monitor.dedup import SeenStore
from main import poll_once, log

if __name__ == "__main__":
    config = Config("config.yaml")
    gist_sync.pull_db(config)

    store = SeenStore(config.dedup_db_path)

    tickers = ", ".join(t["symbol"] for t in config.tickers)
    log.info("Running single poll for: %s", tickers)

    try:
        poll_once(config, store)
    finally:
        gist_sync.push_db(config)