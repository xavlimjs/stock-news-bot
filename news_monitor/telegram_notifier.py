import requests
from collections import defaultdict
from html import escape

API_URL_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LENGTH = 3800  # stay under Telegram's 4096 char limit with margin
PAGE_SUFFIX_RESERVE = " - 99/99"  # conservative width reserved during layout


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

    # --- Pass 1: lay out chunks using a conservative reserved width for the
    # page suffix (" - 99/99"), so real page numbers always fit afterward. ---
    raw_chunks = []
    current_chunk = []
    current_len = len(header)

    for symbol in sorted(by_symbol.keys()):
        articles = by_symbol[symbol]
        count = len(articles)
        reserved_header = f"\n<b>${escape(symbol)}</b> ({count}){PAGE_SUFFIX_RESERVE}"

        if current_len + len(reserved_header) > MAX_MESSAGE_LENGTH and current_chunk:
            raw_chunks.append(current_chunk)
            current_chunk = []
            current_len = len(header)

        current_chunk.append({"symbol": symbol, "count": count, "entries": []})
        current_len += len(reserved_header)

        for a in articles:
            entry = _format_article(a)
            if current_len + len(entry) > MAX_MESSAGE_LENGTH and current_chunk:
                raw_chunks.append(current_chunk)
                current_chunk = []
                current_len = len(header)
                current_chunk.append({"symbol": symbol, "count": count, "entries": []})
                current_len += len(reserved_header)
            current_chunk[-1]["entries"].append(entry)
            current_len += len(entry)

    if current_chunk:
        raw_chunks.append(current_chunk)

    # --- Determine total pages per symbol (how many chunks it appears in) ---
    page_counts = {}
    for chunk in raw_chunks:
        for sec in chunk:
            page_counts[sec["symbol"]] = page_counts.get(sec["symbol"], 0) + 1

    # --- Pass 2: rebuild final text using real page numbers ---
    seen_so_far = {}
    final_chunks = []
    for chunk in raw_chunks:
        text = header
        for sec in chunk:
            symbol = sec["symbol"]
            seen_so_far[symbol] = seen_so_far.get(symbol, 0) + 1
            page = seen_so_far[symbol]
            total_pages = page_counts[symbol]
            suffix = f" - {page}/{total_pages}" if total_pages > 1 else ""
            text += f"\n<b>${escape(symbol)}</b> ({sec['count']}){suffix}"
            for entry in sec["entries"]:
                text += entry
        final_chunks.append(text.rstrip())

    return final_chunks


def _format_article(a: dict) -> str:
    summary = escape((a.get("summary") or "")[:180])
    summary_line = f"\n  {summary}" if summary else ""
    return (
        f"\n• <i>{escape(a['source'])}</i> — {escape(a['headline'])}"
        f"{summary_line}\n  {escape(a['url'])}"
    )