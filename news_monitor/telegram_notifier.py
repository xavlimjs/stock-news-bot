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
    Groups articles by ticker symbol and sends one separate message per
    ticker (split further into multiple messages if a ticker's own articles
    exceed Telegram's length limit). Tickers with no new articles still get
    their own message. Sends every poll, even with zero new articles total.
    """
    by_symbol = defaultdict(list)
    for a in articles:
        by_symbol[a["symbol"]].append(a)

    all_symbols = [t["symbol"] for t in config.tickers]
    chunks = _build_digest_chunks(by_symbol, all_symbols)
    for chunk in chunks:
        _send_raw(config, chunk)


def _build_digest_chunks(by_symbol: dict, all_symbols: list) -> list:
    total_count = sum(len(v) for v in by_symbol.values())
    header = f"<b>📰 Stock News Update</b> — {total_count} new article(s)\n"

    # Tickers with articles first (sorted), then empty tickers appended after
    symbols_with_articles = sorted(s for s in all_symbols if by_symbol.get(s))
    symbols_without_articles = sorted(s for s in all_symbols if not by_symbol.get(s))
    ordered_symbols = symbols_with_articles + symbols_without_articles

    # --- Pass 1: each symbol gets its own list of one-or-more chunks. ---
    # raw_chunks: list of (symbol, count, entries_list) — one entry per chunk.
    raw_chunks = []

    for symbol in ordered_symbols:
        articles = by_symbol.get(symbol, [])
        count = len(articles)
        reserved_header = f"\n<b>${escape(symbol)}</b> ({count}){PAGE_SUFFIX_RESERVE}"

        entries = []
        current_len = len(header) + len(reserved_header)

        if count == 0:
            entries.append("\n  No new articles.")
            raw_chunks.append((symbol, count, entries))
            continue

        for a in articles:
            entry = _format_article(a)
            if current_len + len(entry) > MAX_MESSAGE_LENGTH and entries:
                raw_chunks.append((symbol, count, entries))
                entries = []
                current_len = len(header) + len(reserved_header)
            entries.append(entry)
            current_len += len(entry)

        if entries:
            raw_chunks.append((symbol, count, entries))

    # --- Determine total pages per symbol (how many chunks it appears in) ---
    page_counts = {}
    for symbol, _, _ in raw_chunks:
        page_counts[symbol] = page_counts.get(symbol, 0) + 1

    # --- Pass 2: rebuild final text per chunk using real page numbers ---
    seen_so_far = {}
    final_chunks = []
    for symbol, count, entries in raw_chunks:
        seen_so_far[symbol] = seen_so_far.get(symbol, 0) + 1
        page = seen_so_far[symbol]
        total_pages = page_counts[symbol]
        suffix = f" - {page}/{total_pages}" if total_pages > 1 else ""

        text = header + f"\n<b>${escape(symbol)}</b> ({count}){suffix}"
        for entry in entries:
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