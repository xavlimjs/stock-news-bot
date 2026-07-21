import requests
from datetime import datetime, timedelta, timezone

BASE_URL = "https://newsapi.org/v2/everything"


def fetch_articles(config):
    """
    Returns a list of dicts in the same shape as finnhub_source.fetch_articles.
    Searches config.newsapi_domains for each ticker's company name.
    Note: NewsAPI's free developer tier delays articles by ~24 hours.
    """
    if not config.newsapi_enabled:
        return []

    if not config.newsapi_api_key or config.newsapi_api_key.startswith("your_"):
        raise RuntimeError("NEWSAPI_API_KEY is not set. Add it to your .env file.")

    from_time = datetime.now(timezone.utc) - timedelta(hours=config.newsapi_lookback_hours)
    domains = ",".join(config.newsapi_domains)

    results = []
    for ticker in config.tickers:
        symbol = ticker["symbol"]
        query = ticker.get("name", symbol)

        params = {
            "q": query,
            "domains": domains,
            "from": from_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": config.newsapi_api_key,
        }
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        for a in data.get("articles", []):
            source_name = a.get("source", {}).get("name", "")
            if not config.source_allowed(source_name):
                continue
            url = a.get("url", "")
            results.append({
                "id": f"newsapi-{url}",
                "symbol": symbol,
                "headline": (a.get("title") or "").strip(),
                "source": source_name,
                "url": url,
                "published_at": a.get("publishedAt", ""),
                "summary": (a.get("description") or "").strip(),
            })

    return results
