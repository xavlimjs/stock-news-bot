import requests

API_URL_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"


def send_alert(config, article: dict):
    if not config.telegram_bot_token or config.telegram_bot_token.startswith("your_"):
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Add it to your .env file.")
    if not config.telegram_chat_id or config.telegram_chat_id.startswith("your_"):
        raise RuntimeError("TELEGRAM_CHAT_ID is not set. Add it to your .env file.")

    text = format_message(article)
    url = API_URL_TEMPLATE.format(token=config.telegram_bot_token)
    payload = {
        "chat_id": config.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()


def format_message(article: dict) -> str:
    published = article.get("published_at", "")
    summary = article.get("summary", "")
    summary_line = f"\n{summary[:280]}" if summary else ""

    return (
        f"<b>${article['symbol']}</b> — {article['source']}\n"
        f"{article['headline']}"
        f"{summary_line}\n"
        f"{published}\n"
        f"{article['url']}"
    )
