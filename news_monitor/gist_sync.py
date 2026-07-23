import base64
import logging
import requests

GITHUB_API = "https://api.github.com"
log = logging.getLogger("stock_news_bot")


def pull_db(config):
    """Download seen_articles.db content from the Gist and write it locally."""
    if not config.gist_token or not config.gist_id:
        log.warning("GIST_TOKEN/GIST_ID not set — skipping dedup pull, using local file if present.")
        return

    headers = {
        "Authorization": f"Bearer {config.gist_token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(f"{GITHUB_API}/gists/{config.gist_id}", headers=headers, timeout=15)
    resp.raise_for_status()
    files = resp.json().get("files", {})
    file_data = files.get(config.gist_filename)

    if not file_data or not file_data.get("content"):
        log.info("No existing dedup data in Gist yet — starting fresh.")
        return

    raw = base64.b64decode(file_data["content"])
    with open(config.dedup_db_path, "wb") as f:
        f.write(raw)
    log.info("Restored seen_articles.db from Gist.")


def push_db(config):
    """Upload the local seen_articles.db content back to the Gist."""
    if not config.gist_token or not config.gist_id:
        log.warning("GIST_TOKEN/GIST_ID not set — skipping dedup push.")
        return

    with open(config.dedup_db_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")

    headers = {
        "Authorization": f"Bearer {config.gist_token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"files": {config.gist_filename: {"content": encoded}}}
    resp = requests.patch(f"{GITHUB_API}/gists/{config.gist_id}", headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    log.info("Pushed updated seen_articles.db to Gist.")