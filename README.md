# Stock News Bot

Polls financial news for a fixed list of tickers and pushes alerts to Telegram
when a relevant article shows up from an allowed source (CNBC, Bloomberg,
Reuters, etc.).

## How it sources news

- **Finnhub** (primary): real, per-ticker company news, updated in near
  real-time. Free tier is generous. Each article's `source` field is checked
  against your `allowed_sources` list in `config.yaml`.
- **NewsAPI** (optional, off by default): lets you search specific domains
  directly (`cnbc.com`, `bloomberg.com`, `reuters.com`). Free tier delays
  articles ~24 hours, so treat it as a cross-check, not your main feed.

Raw scraping of Bloomberg/Reuters is intentionally not included — both are
paywalled and block scrapers, so it's not a stable foundation to build on.

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get a Finnhub API key** (free): https://finnhub.io/register

3. **Create a Telegram bot**:
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot`, follow the prompts, copy the token it gives you

4. **Set up your `.env` file**:
   ```bash
   cp .env.example .env
   ```
   Fill in `FINNHUB_API_KEY` and `TELEGRAM_BOT_TOKEN`.

5. **Get your Telegram chat ID**:
   - Send your new bot any message on Telegram (e.g. "hi")
   - Run:
     ```bash
     python get_chat_id.py
     ```
   - Copy the printed `chat_id` into `.env` as `TELEGRAM_CHAT_ID`

6. **Edit `config.yaml`**:
   - Add/remove tickers under `tickers:`
   - Adjust `allowed_sources` (leave `[]` to allow every source)
   - Adjust `poll_interval_minutes`

7. **Run it**:
   ```bash
   python main.py
   ```

   Leave it running (or deploy to a small VPS, e.g. the DigitalOcean/Vultr
   droplet you already use for your trading bot) and it'll check for news on
   the interval you set, forever, sending a Telegram message for each new
   relevant article it hasn't already alerted on.

## Enabling NewsAPI as a second source

1. Get a free key at https://newsapi.org/register
2. Add it to `.env` as `NEWSAPI_API_KEY`
3. In `config.yaml`, set `newsapi.enabled: true` and adjust the `domains` list

## Running it free 24/7 via GitHub Actions (no server, no card)

Instead of `main.py`'s always-on loop, `run_once.py` does a single poll cycle
and exits — built for a scheduler to call repeatedly rather than a process
that stays alive. `.github/workflows/news_check.yml` runs it every ~10
minutes using GitHub Actions, which is free and unlimited for public repos.

1. **Create a public GitHub repo** and push this folder to it:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```
   (`.gitignore` already excludes `.env`, so your real secrets never get
   committed — only `.env.example` with placeholders does.)

2. **Add your secrets** in the repo: Settings → Secrets and variables →
   Actions → "New repository secret". Add these four, one at a time:
   - `FINNHUB_API_KEY`
   - `NEWSAPI_API_KEY` (can be any placeholder value if you're not using it)
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

3. **That's it.** The workflow will start running automatically on its
   schedule. To check on it or trigger a run immediately: go to the "Actions"
   tab in your repo → "Stock News Check" → "Run workflow".

4. **Adjust the schedule** if you want a different interval — edit the
   `cron` line in `.github/workflows/news_check.yml`. Cron syntax is
   `minute hour day month weekday`, so `*/15 * * * *` = every 15 minutes.

Notes specific to this setup:
- Each run commits the updated `seen_articles.db` back to your repo, which
  is also what keeps the schedule from ever auto-disabling due to
  inactivity.
- `allowed_sources` and your ticker list still live in `config.yaml` — since
  it has no secrets in it, it's fine to commit and edit directly on GitHub
  if you want to tweak it from your phone.

## Notes / limitations

- Free-tier API rate limits apply — if you add a lot of tickers, watch your
  daily request count (each ticker = 1 request per source per poll).
- `seen_articles.db` (SQLite) stores which article IDs you've already been
  alerted on, so restarting the bot won't re-send old news.
- To run this 24/7, deploy it the same way as your trading bot (systemd
  service or a simple `nohup python main.py &` on a small VPS).
