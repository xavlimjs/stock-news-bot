import requests
from collections import defaultdict
from html import escape

API_URL_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LENGTH = 3800  # stay under Telegram's 4096 char limit with margin


def _send_raw(config, text: str):
    if not config.telegram_bot_token or config.telegram_bot_token.startswith("your_"):
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Add it to your .env file.")
    if not config.telegram_chat_id or config.telegram_chat_id.startswith("your_"):
        raise RuntimeError("TELEGRAM_CHAT_ID is not set. Add it to your .env file.")

    url = API_URL_TEMPLATE.format(token=config.telegram_bot_token)
    payload = {
        "chat_id": config.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()


def send_digest(config, articles: list):
    """
    Groups articles by ticker symbol and sends one (or more, if long)
    organized digest message(s) instead of one message per article.
    """
    if not articles:
        return

    by_symbol = defaultdict(list)
    for a in articles:
        by_symbol[a["symbol"]].append(a)

    chunks = _build_digest_chunks(by_symbol)
    for chunk in chunks:
        _send_raw(config, chunk)


def _build_digest_chunks(by_symbol: dict) -> list:
    total_count = sum(len(v) for v in by_symbol.values())
    header = f"<b>📰 Stock News Update</b> — {total_count} new article(s)\n"

    chunks = []
    current = header

    for symbol in sorted(by_symbol.keys()):
        articles = by_symbol[symbol]
        section_header = f"\n<b>${escape(symbol)}</b> ({len(articles)})"

        # Add section header, splitting first if it won't fit
        if len(current) + len(section_header) > MAX_MESSAGE_LENGTH and current != header:
            chunks.append(current.rstrip())
            current = header
        current += section_header

        for a in articles:
            entry = _format_article(a)
            if len(current) + len(entry) > MAX_MESSAGE_LENGTH and current != header:
                chunks.append(current.rstrip())
                current = header + section_header  # repeat symbol header on continuation
            current += entry

    if current.strip():
        chunks.append(current.rstrip())

    return chunks


def _format_article(a: dict) -> str:
    summary = escape((a.get("summary") or "")[:180])
    summary_line = f"\n  {summary}" if summary else ""
    return (
        f"\n• <i>{escape(a['source'])}</i> — {escape(a['headline'])}"
        f"{summary_line}\n  {escape(a['url'])}"
    )