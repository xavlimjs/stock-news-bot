import requests
from datetime import datetime, timedelta, timezone

BASE_URL = "https://finnhub.io/api/v1/company-news"


def fetch_articles(config):
    """
    Returns a list of dicts: {id, symbol, headline, source, url, published_at, summary}
    Only articles from allowed sources are returned.
    """
    if not config.finnhub_enabled:
        return []

    if not config.finnhub_api_key or config.finnhub_api_key.startswith("your_"):
        raise RuntimeError("FINNHUB_API_KEY is not set. Add it to your .env file.")

    to_date = datetime.now(timezone.utc).date()
    from_date = to_date - timedelta(days=config.finnhub_lookback_days)

    results = []
    for ticker in config.tickers:
        symbol = ticker["symbol"]
        params = {
            "symbol": symbol,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "token": config.finnhub_api_key,
        }
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        articles = resp.json()

        for a in articles:
            source_name = a.get("source", "")
            if not config.source_allowed(source_name):
                continue
            results.append({
                "id": f"finnhub-{a.get('id')}",
                "symbol": symbol,
                "headline": a.get("headline", "").strip(),
                "source": source_name,
                "url": a.get("url", ""),
                "published_at": datetime.fromtimestamp(
                    a.get("datetime", 0), tz=timezone.utc
                ),
                "summary": a.get("summary", "").strip(),
            })

    return results
