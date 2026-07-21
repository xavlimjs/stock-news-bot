import time
import logging
import traceback

from news_monitor.config import Config
from news_monitor.dedup import SeenStore
from news_monitor import finnhub_source
from news_monitor import newsapi_source
from news_monitor import telegram_notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("stock_news_bot")


def poll_once(config: Config, store: SeenStore):
    all_articles = []

    try:
        all_articles.extend(finnhub_source.fetch_articles(config))
    except Exception:
        log.error("Finnhub fetch failed:\n%s", traceback.format_exc())

    try:
        all_articles.extend(newsapi_source.fetch_articles(config))
    except Exception:
        log.error("NewsAPI fetch failed:\n%s", traceback.format_exc())

    new_articles = [a for a in all_articles if store.is_new(a["id"])]

    if not new_articles:
        log.info("No new relevant articles this poll.")
        return

    try:
        telegram_notifier.send_digest(config, new_articles)
        for article in new_articles:
            store.mark_seen(article["id"])
        log.info("Sent digest with %d new article(s).", len(new_articles))
    except Exception:
        log.error("Failed to send digest:\n%s", traceback.format_exc())
        # Articles are NOT marked seen here, so they'll be retried next poll.


def main():
    config = Config("config.yaml")
    store = SeenStore(config.dedup_db_path)

    tickers = ", ".join(t["symbol"] for t in config.tickers)
    log.info("Starting stock news monitor for: %s", tickers)
    log.info("Polling every %d minute(s).", config.poll_interval_minutes)

    while True:
        poll_once(config, store)
        time.sleep(config.poll_interval_minutes * 60)


if __name__ == "__main__":
    main()
