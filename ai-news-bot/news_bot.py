import os
import sys
import json
import logging
import socket
from datetime import datetime, timezone

import feedparser
import google.generativeai as genai
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================================
# Logging Setup
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================================
# Proxy Detection
# ============================================
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
    logger.info("Proxy detected at 127.0.0.1:10808 — using it")
else:
    os.environ.pop("HTTPS_PROXY", None)
    os.environ.pop("HTTP_PROXY", None)
    logger.info("No proxy detected — connecting directly")

# ============================================
# HTTP Session with Retry
# ============================================
http_session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
http_session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
http_session.mount("http://", HTTPAdapter(max_retries=retry_strategy))

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
    logger.error("Missing configuration. Please fill in config.json or set env vars.")
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
    "https://feeds.feedburner.com/GoogleAIBlog",
    "https://huggingface.co/blog/feed.xml",
    "https://openai.com/blog/rss.xml",
    # AI Agents & Tools specific
    "https://www.marktechpost.com/feed/",
    "https://syncedreview.com/feed/",
]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3.1-flash-lite")

# ============================================
# News Category Classification (Keyword-Based)
# ============================================
CATEGORIES = {
    "🛠️ ابزارها و محصولات جدید": {
        "keywords": [
            "launch", "release", "announce", "tool", "app", "platform",
            "product", "feature", "update", "api", "sdk", "plugin",
            "integration", "service", "deploy", "chatbot", "assistant",
            "copilot", "agent", "framework", "library", "open-source",
            "opens", "introduces", "unveils", "debuts", "rolls out",
            "now available", "beta", "preview", "generally available",
        ],
        "emoji": "🛠️",
    },
    "📄 مقالات پژوهشی": {
        "keywords": [
            "research", "paper", "study", "arxiv", "findings", "experiment",
            "benchmark", "dataset", "model", "training", "fine-tune",
            "transformer", "neural", "architecture", "algorithm",
            "breakthrough", "novel", "propose", "evaluate", "sota",
            "state-of-the-art", "preprint", "peer-review", "journal",
            "conference", "icml", "neurips", "iclr", "cvpr", "aaai",
            "acl", "emnlp", "published", "researchers",
        ],
        "emoji": "📄",
    },
    "🏢 اخبار شرکت‌ها": {
        "keywords": [
            "google", "openai", "microsoft", "meta", "amazon", "apple",
            "nvidia", "anthropic", "mistral", "deepmind", "stability",
            "hugging face", "cohere", "databricks", "salesforce",
            "ibm", "intel", "amd", "tesla", "samsung", "baidu",
            "alibaba", "tencent", "xai", "startup", "funding",
            "acquisition", "partnership", "hire", "layoff", "ceo",
            "valuation", "ipo", "revenue", "investment", "series",
            "billion", "million", "deal", "merge",
        ],
        "emoji": "🏢",
    },
    "⚖️ قوانین و اخلاق هوش مصنوعی": {
        "keywords": [
            "regulation", "law", "policy", "ethics", "bias", "safety",
            "alignment", "governance", "ban", "restrict", "compliance",
            "copyright", "privacy", "gdpr", "eu ai act", "senate",
            "congress", "legislation", "lawsuit", "court", "legal",
            "responsible", "transparency", "accountability", "risk",
            "deepfake", "misinformation", "disinformation",
        ],
        "emoji": "⚖️",
    },
    "🤖 کاربردهای هوش مصنوعی": {
        "keywords": [
            "healthcare", "medical", "diagnosis", "drug", "climate",
            "education", "autonomous", "self-driving", "robotics",
            "manufacturing", "agriculture", "finance", "art",
            "music", "video", "image", "generation", "creative",
            "gaming", "security", "cybersecurity", "military",
            "defense", "space", "energy", "transportation",
        ],
        "emoji": "🤖",
    },
}


def classify_news(title, summary):
    """Classify a news item into a category using keyword matching.

    Returns (category_name, emoji) or ("📰 سایر اخبار", "📰") as fallback.
    """
    text = f"{title} {summary}".lower()
    scores = {}
    for cat_name, cat_info in CATEGORIES.items():
        score = sum(1 for kw in cat_info["keywords"] if kw in text)
        if score > 0:
            scores[cat_name] = score

    if scores:
        best = max(scores, key=scores.get)
        return best, CATEGORIES[best]["emoji"]
    return "📰 سایر اخبار", "📰"


# ============================================
# Feed Fetching
# ============================================
def get_days_ago(entry):
    """Calculate how many days ago a news item was published."""
    now = datetime.now(timezone.utc)
    if hasattr(entry, "published_parsed") and entry.published_parsed:
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
    """Fetch news from all RSS feeds with dates and categories."""
    news_items = []
    seen_titles = set()

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            source_name = feed.feed.get("title", url)
            for entry in feed.entries[:8]:
                title = entry.title.strip()
                # Skip duplicates
                title_key = title.lower()[:50]
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

                days_ago = get_days_ago(entry)
                summary = ""
                if hasattr(entry, "summary"):
                    summary = entry.summary[:300]
                elif hasattr(entry, "description"):
                    summary = entry.description[:300]

                category, emoji = classify_news(title, summary)

                news_items.append(
                    {
                        "title": title,
                        "summary": summary,
                        "days_ago": days_ago,
                        "source": source_name,
                        "category": category,
                        "category_emoji": emoji,
                    }
                )
            logger.info(f"Fetched {min(8, len(feed.entries))} items from {source_name}")
        except Exception as e:
            logger.warning(f"Skipping {url}: {e}")

    logger.info(f"Total unique items: {len(news_items)}")
    return news_items


# ============================================
# Category Statistics
# ============================================
def get_category_stats(news_items):
    """Return a dict of category -> count."""
    stats = {}
    for item in news_items:
        cat = item["category"]
        stats[cat] = stats.get(cat, 0) + 1
    return stats


# ============================================
# AI Translation & Formatting
# ============================================
def translate_and_format(news_items):
    """Use Gemini to translate and format news in Persian with HTML, grouped by category."""
    # Group items by category
    grouped = {}
    for item in news_items:
        cat = item["category"]
        grouped.setdefault(cat, []).append(item)

    # Build structured input for Gemini
    items_text = ""
    for cat_name, items in grouped.items():
        items_text += f"\n=== CATEGORY: {cat_name} ===\n"
        for i, item in enumerate(items, 1):
            items_text += f"""
--- Item {i} ---
Title: {item['title']}
Published: {item['days_ago']}
Source: {item['source']}
Summary: {item['summary']}
"""

    prompt = f"""You are an expert AI news curator and translator.

Take the following English AI news items (already grouped by category) and create a Persian news digest.

RULES:
1. Select the TOP 10 to 15 most important/interesting news items across all categories.
2. Translate everything into natural, fluent Persian.
3. You MUST use Telegram HTML formatting (NOT markdown). Use these tags ONLY:
   - <b>bold text</b> for headlines and category headers
   - <i>italic</i> for emphasis
   - No other HTML tags
4. For each news item, include the "published" time (e.g. "۲ روز پیش" for "2 days ago").
5. Add a source name in parentheses at the end of each item.
6. Use numbered list format (۱. ۲. ۳. ... use Persian numerals).
7. Keep each item concise: headline + 1-2 sentence summary + time + source.
8. Start with a header line: <b>📰 آخرین اخبار هوش مصنوعی</b>
9. GROUP the news by their categories. Use the category name (with its emoji) as a section header.
   For example:
   <b>🛠️ ابزارها و محصولات جدید</b>
   ۱. ...
   ۲. ...
   
   <b>📄 مقالات پژوهشی</b>
   ۳. ...

Here are the news items grouped by category:

{items_text}
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return f"⚠️ خطا در ارتباط با Gemini: {e}"


# ============================================
# Telegram Sender
# ============================================
def send_telegram(message):
    """Send message to Telegram using HTML parse mode with retry."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # Telegram message limit is 4096 chars — split if needed
    chunks = []
    while len(message) > 4096:
        split_point = message[:4096].rfind("\n\n")
        if split_point == -1:
            split_point = message[:4096].rfind("\n")
        if split_point == -1:
            split_point = 4096
        chunks.append(message[:split_point])
        message = message[split_point:].strip()
    chunks.append(message)

    results = []
    for i, chunk in enumerate(chunks):
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = http_session.post(url, json=payload, timeout=30)
            results.append((resp.status_code, resp.text))
            if resp.status_code == 200:
                logger.info(f"Message part {i+1}/{len(chunks)}: sent OK")
            else:
                logger.error(f"Message part {i+1}/{len(chunks)}: {resp.status_code} — {resp.text[:200]}")
        except requests.RequestException as e:
            logger.error(f"Failed to send message part {i+1}: {e}")
            results.append((0, str(e)))

    return results


# ============================================
# Main
# ============================================
def main():
    logger.info("=" * 50)
    logger.info("  AI News Bot — Daily Persian Digest")
    logger.info("=" * 50)

    logger.info("[1/3] Fetching AI news from RSS feeds...")
    news_items = fetch_news()
    logger.info(f"Found {len(news_items)} unique news items from {len(FEEDS)} sources")

    if not news_items:
        logger.error("No news items fetched. Check your internet connection.")
        sys.exit(1)

    # Log category stats
    stats = get_category_stats(news_items)
    logger.info("Category breakdown:")
    for cat, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {cat}: {count} items")

    logger.info("[2/3] Translating and formatting with Gemini...")
    summary = translate_and_format(news_items)
    logger.info(f"Got summary ({len(summary)} chars)")

    logger.info("[3/3] Sending to Telegram...")
    results = send_telegram(summary)

    if all(s == 200 for s, _ in results):
        logger.info("SUCCESS! Check your Telegram for the news digest.")
    else:
        logger.warning("Some parts failed to send. Check the errors above.")


if __name__ == "__main__":
    main()
