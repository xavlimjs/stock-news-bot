import requests
from collections import defaultdict

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

    sections = []
    for symbol in sorted(by_symbol.keys()):
        section = _format_ticker_section(symbol, by_symbol[symbol])
        sections.append(section)

    # Pack sections into chunks that stay under Telegram's length limit
    chunks = []
    current = header
    for section in sections:
        if len(current) + len(section) > MAX_MESSAGE_LENGTH and current != header:
            chunks.append(current.rstrip())
            current = header  # repeat header on continuation messages
        current += "\n" + section
    if current.strip():
        chunks.append(current.rstrip())

    return chunks


def _format_ticker_section(symbol: str, articles: list) -> str:
    lines = [f"\n<b>${symbol}</b> ({len(articles)})"]
    for a in articles:
        summary = (a.get("summary") or "")[:180]
        summary_line = f"\n  {summary}" if summary else ""
        lines.append(
            f"• <i>{a['source']}</i> — {a['headline']}"
            f"{summary_line}\n  {a['url']}"
        )
    return "\n".join(lines)
