import os
import sys
import json
from datetime import datetime, timezone

import socket
import feedparser
import google.generativeai as genai
import requests


def _proxy_is_available(host="127.0.0.1", port=10808, timeout=1):
    """Check if a proxy is actually reachable before using it."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


# Only set proxy if v2rayN (or similar) is actually running
if _proxy_is_available():
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10808"
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:10808"
else:
    os.environ.pop("HTTPS_PROXY", None)
    os.environ.pop("HTTP_PROXY", None)

# ============================================
# Configuration
# ============================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# If env vars not set, try reading from config file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
        GEMINI_API_KEY = cfg.get("gemini_api_key", GEMINI_API_KEY)
        TELEGRAM_BOT_TOKEN = cfg.get("telegram_bot_token", TELEGRAM_BOT_TOKEN)
        TELEGRAM_CHAT_ID = cfg.get("telegram_chat_id", TELEGRAM_CHAT_ID)

if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("ERROR: Missing configuration. Please fill in config.json")
    sys.exit(1)

# ============================================
# RSS Feeds - AI News Sources
# ============================================
FEEDS = [
    # General AI News
    "https://rss.feedburner.com/AI-News",
    "https://www.artificialintelligence-news.com/feed/",
    # Tech blogs with strong AI coverage
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.technologyreview.com/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://arstechnica.com/tag/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://feeds.feedburner.com/GoogleAIBlog", # Google AI Blog
    "https://huggingface.co/blog/feed.xml", # Hugging Face Blog
    "https://openai.com/blog/rss.xml", # OpenAI Blog
    # AI Agents & Tools specific
    "https://www.marktechpost.com/feed/",
    "https://syncedreview.com/feed/",
]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.1-flash-lite')


def get_days_ago(entry):
    """Calculate how many days ago a news item was published."""
    now = datetime.now(timezone.utc)
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        delta = now - pub_date
        days = delta.days
        if days == 0:
            hours = delta.seconds // 3600
            if hours == 0:
                return "minutes ago"
            return f"{hours} hours ago"
        elif days == 1:
            return "1 day ago"
        else:
            return f"{days} days ago"
    return "recently"


def fetch_news():
    """Fetch news from all RSS feeds with dates."""
    news_items = []
    seen_titles = set()

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                title = entry.title.strip()
                # Skip duplicates
                title_key = title.lower()[:50]
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

                days_ago = get_days_ago(entry)
                summary = ""
                if hasattr(entry, 'summary'):
                    summary = entry.summary[:300]
                elif hasattr(entry, 'description'):
                    summary = entry.description[:300]

                news_items.append({
                    "title": title,
                    "summary": summary,
                    "days_ago": days_ago,
                    "source": feed.feed.get("title", url)
                })
        except Exception as e:
            print(f"  [WARN] Skipping {url}: {e}")

    return news_items


def translate_and_format(news_items):
    """Use Gemini to translate and format news in Persian with HTML."""
    # Build structured input for Gemini
    items_text = ""
    for i, item in enumerate(news_items, 1):
        items_text += f"""
--- Item {i} ---
Title: {item['title']}
Published: {item['days_ago']}
Source: {item['source']}
Summary: {item['summary']}
"""

    prompt = f"""You are an expert AI news curator and translator.

Take the following English AI news items and create a Persian news digest.

RULES:
1. Select the TOP 10 to 15 most important/interesting news items.
2. Translate everything into natural, fluent Persian.
3. You MUST use Telegram HTML formatting (NOT markdown). Use these tags ONLY:
   - <b>bold text</b> for headlines
   - <i>italic</i> for emphasis
   - No other HTML tags
4. For each news item, include the "published" time (e.g. "۲ روز پیش" for "2 days ago").
5. Add a source name in parentheses at the end of each item.
6. Use numbered list format (۱. ۲. ۳. ... use Persian numerals).
7. Keep each item concise: headline + 1-2 sentence summary + time + source.
8. Start with a header line like: <b>📰 آخرین اخبار هوش مصنوعی</b>

Here are the news items:

{items_text}
"""

    response = model.generate_content(prompt)
    return response.text


def send_telegram(message):
    """Send message to Telegram using HTML parse mode."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # Telegram message limit is 4096 chars
    # If message is too long, split it
    chunks = []
    while len(message) > 4096:
        split_point = message[:4096].rfind('\n\n')
        if split_point == -1:
            split_point = 4096
        chunks.append(message[:split_point])
        message = message[split_point:].strip()
    chunks.append(message)

    results = []
    for chunk in chunks:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        resp = requests.post(url, json=payload)
        results.append((resp.status_code, resp.text))
    return results


def main():
    print("=" * 50)
    print("  AI News Bot - Daily Persian Digest")
    print("=" * 50)

    print("\n[1/3] Fetching AI news from RSS feeds...")
    news_items = fetch_news()
    print(f"  -> Found {len(news_items)} unique news items from {len(FEEDS)} sources")

    if not news_items:
        print("ERROR: No news items fetched. Check your internet connection.")
        sys.exit(1)

    print("\n[2/3] Translating and formatting with Gemini 3.1 Flash Lite...")
    summary = translate_and_format(news_items)
    print(f"  -> Got summary ({len(summary)} chars)")

    print("\n[3/3] Sending to Telegram...")
    results = send_telegram(summary)
    for i, (status, body) in enumerate(results):
        if status == 200:
            print(f"  -> Part {i+1}: OK")
        else:
            print(f"  -> Part {i+1}: FAILED ({status}): {body[:200]}")

    if all(s == 200 for s, _ in results):
        print("\nSUCCESS! Check your Telegram for the news digest.")
    else:
        print("\nSome parts failed to send. Check the errors above.")


if __name__ == "__main__":
    main()
