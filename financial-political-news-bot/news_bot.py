import os
import sys
import json
import logging
import re
import time
import socket
from datetime import datetime, timezone, timedelta

import requests
import feedparser
import google.generativeai as genai
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Proxy Detection ─────────────────────────────────────────────────────────
def _proxy_is_available(host="127.0.0.1", port=10808, timeout=1):
    """Check if a proxy is actually reachable before using it."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


if _proxy_is_available():
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10808"
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:10808"
    logger.info("Proxy detected at 127.0.0.1:10808 — using it")
else:
    os.environ.pop("HTTPS_PROXY", None)
    os.environ.pop("HTTP_PROXY", None)
    logger.info("No proxy detected — connecting directly")

# ─── Load env variables ──────────────────────────────────────────────────────
load_dotenv()

# ─── Configuration ───────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

TELEGRAM_MAX_LENGTH = 4096

# ─── Validate required environment variables ─────────────────────────────────
def validate_env():
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please create a .env file or set them in your environment.")
        logger.error("See .env.example for the required format.")
        sys.exit(1)

validate_env()

# ─── Gemini Setup ────────────────────────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3.1-flash-lite")

# ─── HTTP Session with Retry ─────────────────────────────────────────────────
http_session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
http_session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
http_session.mount("http://", HTTPAdapter(max_retries=retry_strategy))


# ─── Utility Functions ───────────────────────────────────────────────────────
def to_persian_num(n):
    """Convert a number to Persian numeral string."""
    if n is None:
        return "N/A"
    try:
        val = int(float(str(n).replace(",", "")))
        formatted = f"{val:,}"
    except (ValueError, TypeError):
        return str(n)

    persian_digits = {
        "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
        "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
    }
    return "".join(persian_digits.get(c, c) for c in formatted)


def format_price(value, currency="تومان"):
    """Format a price with Persian numerals, handling None gracefully."""
    if value is None or value == 0:
        return "داده موجود نیست"
    return f"{to_persian_num(value)} {currency}"


# ─── News Category Classification (Keyword-Based) ───────────────────────────
NEWS_CATEGORIES = {
    "🌍 سیاست خارجی و بین‌الملل": {
        "keywords": [
            "nuclear", "هسته", "مذاکر", "برجام", "jcpoa", "sanction",
            "تحریم", "diplomacy", "دیپلماسی", "summit", "نشست",
            "treaty", "توافق", "nato", "ناتو", "united nations",
            "سازمان ملل", "foreign", "خارجی", "ambassador", "سفیر",
            "bilateral", "multilateral", "geopolitic", "international",
            "بین‌المللی", "war", "جنگ", "peace", "صلح", "conflict",
            "منازعه", "ceasefire", "آتش‌بس", "ukraine", "اوکراین",
            "gaza", "غزه", "israel", "اسرائیل", "palestine", "فلسطین",
        ],
        "emoji": "🌍",
    },
    "🏛️ سیاست داخلی": {
        "keywords": [
            "مجلس", "parliament", "election", "انتخابات", "رئیس‌جمهور",
            "president", "دولت", "government", "وزیر", "minister",
            "قانون", "law", "اعتراض", "protest", "بازداشت", "arrest",
            "دادگاه", "court", "حکم", "verdict", "رهبر", "leader",
            "سپاه", "irgc", "بسیج", "شورای نگهبان", "guardian council",
            "reform", "اصلاح", "conservative", "محافظه‌کار",
        ],
        "emoji": "🏛️",
    },
    "💹 اقتصاد و بازار": {
        "keywords": [
            "economy", "اقتصاد", "inflation", "تورم", "gdp",
            "budget", "بودجه", "trade", "تجارت", "export", "صادرات",
            "import", "واردات", "oil", "نفت", "opec", "اوپک",
            "stock", "بورس", "market", "بازار", "bank", "بانک",
            "currency", "ارز", "subsidy", "یارانه", "tax", "مالیات",
            "unemployment", "بیکاری", "growth", "رشد",
        ],
        "emoji": "💹",
    },
    "🔬 علم و فناوری": {
        "keywords": [
            "technology", "فناوری", "science", "علم", "internet",
            "اینترنت", "cyber", "سایبر", "satellite", "ماهواره",
            "nuclear energy", "انرژی هسته‌ای", "research", "پژوهش",
            "innovation", "نوآوری", "ai", "هوش مصنوعی", "space",
            "فضا", "startup", "استارتاپ",
        ],
        "emoji": "🔬",
    },
    "👥 اجتماعی و حقوق بشر": {
        "keywords": [
            "human rights", "حقوق بشر", "women", "زنان", "freedom",
            "آزادی", "journalist", "روزنامه‌نگار", "media", "رسانه",
            "refugee", "پناهنده", "immigration", "مهاجرت",
            "execution", "اعدام", "prison", "زندان", "activist",
            "فعال", "ngo", "civil society", "جامعه مدنی",
        ],
        "emoji": "👥",
    },
}


def classify_political_news(title, source_name):
    """Classify a political news item into a category using keyword matching.

    Returns (category_name, emoji) or ("📰 سایر اخبار", "📰") as fallback.
    """
    text = f"{title}".lower()
    scores = {}
    for cat_name, cat_info in NEWS_CATEGORIES.items():
        score = sum(1 for kw in cat_info["keywords"] if kw in text)
        if score > 0:
            scores[cat_name] = score

    if scores:
        best = max(scores, key=scores.get)
        return best, NEWS_CATEGORIES[best]["emoji"]
    return "📰 سایر اخبار", "📰"


# ─── CoinGecko Crypto Data ──────────────────────────────────────────────────
def get_crypto_data():
    """Fetches real crypto prices and 24h changes from CoinGecko API."""
    try:
        url = (
            "https://api.coingecko.com/api/v3/coins/markets"
            "?vs_currency=usd"
            "&ids=bitcoin,ethereum,binancecoin,solana"
            "&order=market_cap_desc&per_page=4&page=1"
            "&sparkline=false"
            "&price_change_percentage=24h,7d"
        )
        response = http_session.get(url, timeout=15)
        if response.status_code == 429:
            logger.warning("CoinGecko rate limited (429). Waiting 30s and retrying...")
            time.sleep(30)
            response = http_session.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        result = {}
        for item in data:
            symbol = item["symbol"].upper()
            result[symbol] = {
                "price": item["current_price"],
                "change_24h": item.get("price_change_percentage_24h"),
                "change_7d": item.get("price_change_percentage_7d_in_currency"),
            }
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching crypto data: {e}")
        return {}
    except (KeyError, json.JSONDecodeError, TypeError) as e:
        logger.error(f"Error parsing crypto data: {e}")
        return {}


# ─── TGJU Iranian Market Data ───────────────────────────────────────────────
def get_iran_market_data():
    """Scrapes USD and Gold from TGJU with updated data-price patterns."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        )
    }
    result = {"USD": None, "Gold18k": None, "Seke": None}

    try:
        resp = http_session.get(
            "https://www.tgju.org/",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        text = resp.text

        # TGJU now uses data-market-row with data-price attributes
        # ── USD (دلار آزاد) ──
        usd_pat = r'data-market-row="price_dollar_rl".*?data-price="([\d,]+)"'
        m = re.search(usd_pat, text, re.DOTALL)
        if m:
            result["USD"] = int(m.group(1).replace(",", ""))

        # ── Gold 18k (گرم طلای ۱۸ عیار) ──
        gold_pat = r'data-market-row="geram18".*?data-price="([\d,]+)"'
        m = re.search(gold_pat, text, re.DOTALL)
        if m:
            result["Gold18k"] = int(m.group(1).replace(",", ""))

        # ── Seke (سکه امامی) ──
        seke_pat = r'data-market-row="sekee".*?data-price="([\d,]+)"'
        m = re.search(seke_pat, text, re.DOTALL)
        if m:
            result["Seke"] = int(m.group(1).replace(",", ""))

        # Fallback: td.nf class
        if result["USD"] is None:
            fallback_usd = r'data-market-row="price_dollar_rl".*?<td class="nf">([\d,]+)</td>'
            m = re.search(fallback_usd, text, re.DOTALL)
            if m:
                result["USD"] = int(m.group(1).replace(",", ""))

        if result["Gold18k"] is None:
            fallback_gold = r'data-market-row="geram18".*?<td class="nf">([\d,]+)</td>'
            m = re.search(fallback_gold, text, re.DOTALL)
            if m:
                result["Gold18k"] = int(m.group(1).replace(",", ""))

        if result["Seke"] is None:
            fallback_seke = r'data-market-row="sekee".*?<td class="nf">([\d,]+)</td>'
            m = re.search(fallback_seke, text, re.DOTALL)
            if m:
                result["Seke"] = int(m.group(1).replace(",", ""))

    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping TGJU: {e}")

    for key in ["USD", "Gold18k", "Seke"]:
        if result[key] is None:
            logger.warning(f"Could not scrape {key} price from TGJU.")

    return result


# ─── Nobitex USD Price ───────────────────────────────────────────────────────
def get_nobitex_usd():
    """Fetch USDT/IRT price from Nobitex API. Returns Toman price or None."""
    try:
        url = "https://api.nobitex.ir/v2/orderbook/USDTIRT"
        resp = http_session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "ok":
            price = data.get("lastTradePrice")
            if price:
                return int(float(price))
    except requests.exceptions.RequestException:
        pass  # Silently ignore — Nobitex may be unreachable in some regions
    return None


# ─── History / Trend Tracking ────────────────────────────────────────────────
def update_history(current_data):
    """Updates the history.json file and returns comparisons."""
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    history = json.loads(content)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not read history file: {e}")
            history = {}

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    history[today_str] = current_data

    dates = sorted(history.keys(), reverse=True)
    if len(dates) > 30:
        for d in dates[30:]:
            del history[d]

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.warning(f"Could not write history file: {e}")

    yesterday_str = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    last_week_str = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

    comparisons = {}
    for key in current_data:
        comparisons[key] = {
            "yesterday": history.get(yesterday_str, {}).get(key),
            "last_week": history.get(last_week_str, {}).get(key),
        }
    return comparisons


# ─── Trend Formatting ────────────────────────────────────────────────────────
def format_trend(current, previous):
    """Format a percentage trend with emoji."""
    if current is None or previous is None or previous == 0:
        return ""
    try:
        diff = float(current) - float(previous)
        percent = (diff / float(previous)) * 100
        emoji = "📈" if diff >= 0 else "📉"
        return f"{emoji} {abs(percent):.1f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return ""


# ─── Financial Section ───────────────────────────────────────────────────────
def get_financial_section():
    iran_data = get_iran_market_data()
    crypto_data = get_crypto_data()
    nobitex_usd = get_nobitex_usd()

    current_map = {
        "USD_TGJU": iran_data.get("USD"),
        "USD_NOBITEX": nobitex_usd,
        "Gold": iran_data.get("Gold18k"),
        "Seke": iran_data.get("Seke"),
        "BTC": crypto_data.get("BTC", {}).get("price"),
        "ETH": crypto_data.get("ETH", {}).get("price"),
    }
    comps = update_history(current_map)

    msg = "<b>📊 وضعیت بازار (Market Update)</b>\n\n"

    # ── USD TGJU ──
    usd_price = iran_data["USD"]
    usd_y = comps["USD_TGJU"]["yesterday"]
    msg += f"💵 دلار (TGJU): <b>{format_price(usd_price)}</b>\n"
    msg += f"   نسبت به دیروز: {format_trend(usd_price, usd_y) or 'بدون داده'}\n\n"

    # ── USD Nobitex (optional) ──
    if nobitex_usd is not None:
        nob_y = comps["USD_NOBITEX"]["yesterday"]
        msg += f"🔗 دلار (نوبیتکس): <b>{format_price(nobitex_usd)}</b>\n"
        msg += f"   نسبت به دیروز: {format_trend(nobitex_usd, nob_y) or 'بدون داده'}\n\n"

    # ── Gold ──
    gold_price = iran_data["Gold18k"]
    gold_y = comps["Gold"]["yesterday"]
    msg += f"🪙 طلا ۱۸ عیار: <b>{format_price(gold_price)}</b>\n"
    msg += f"   نسبت به دیروز: {format_trend(gold_price, gold_y) or 'بدون داده'}\n\n"

    # ── Seke ──
    seke_price = iran_data["Seke"]
    seke_y = comps["Seke"]["yesterday"]
    msg += f"💰 سکه امامی: <b>{format_price(seke_price)}</b>\n"
    msg += f"   نسبت به دیروز: {format_trend(seke_price, seke_y) or 'بدون داده'}\n\n"

    # ── Crypto ──
    for sym in ["BTC", "ETH"]:
        c = crypto_data.get(sym)
        if c:
            price = c["price"]
            y_price = comps[sym]["yesterday"]
            trend = format_trend(price, y_price)
            if not trend and c.get("change_24h") is not None:
                trend = f"24h: {c['change_24h']:.1f}%"
            msg += f"₿ {sym}: <b>{to_persian_num(price)} USD</b> ({trend})\n"

    return msg


# ─── Political News ──────────────────────────────────────────────────────────
def fetch_political_news():
    feeds = [
        ("بی‌بی‌سی فارسی", "https://feeds.bbci.co.uk/persian/rss.xml"),
        ("رادیو فردا", "https://www.radiofarda.com/rss"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("Reuters", "https://www.reuters.com/arc/outboundfeeds/v1/topic/iran/?outputType=xml"),
    ]
    news = []
    seen = set()
    now = datetime.now(timezone.utc)

    for name, url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.title.strip()

                if name in ("Al Jazeera", "Reuters"):
                    if "iran" not in title.lower() and "iran" not in entry.get("summary", "").lower():
                        continue

                title_key = title.lower()[:50]
                if title_key not in seen:
                    time_ago_str = "نامشخص"
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        pub_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        diff = now - pub_dt

                        hours = diff.seconds // 3600
                        minutes = (diff.seconds % 3600) // 60

                        if diff.days > 0:
                            time_ago_str = f"{to_persian_num(diff.days)} روز پیش"
                        elif hours > 0:
                            time_ago_str = f"{to_persian_num(hours)} ساعت و {to_persian_num(minutes)} دقیقه پیش"
                        else:
                            time_ago_str = f"{to_persian_num(minutes)} دقیقه پیش"

                    category, emoji = classify_political_news(title, name)

                    news.append(
                        {
                            "title": title,
                            "link": entry.link,
                            "source": name,
                            "time_ago": time_ago_str,
                            "category": category,
                            "category_emoji": emoji,
                        }
                    )
                    seen.add(title_key)
            logger.info(f"Fetched news from {name}")
        except Exception as e:
            logger.warning(f"Failed to parse feed '{name}': {e}")
            continue
    return news[:15]


# ─── AI Summary ──────────────────────────────────────────────────────────────
def get_ai_summary(news_list):
    if not news_list:
        return "خبر سیاسی مهمی یافت نشد."

    # Group news by category
    grouped = {}
    for n in news_list:
        cat = n["category"]
        grouped.setdefault(cat, []).append(n)

    formatted_news = ""
    for cat_name, items in grouped.items():
        formatted_news += f"\n=== CATEGORY: {cat_name} ===\n"
        for n in items:
            formatted_news += f"- {n['title']} (Source: {n['source']}, Time Ago: {n['time_ago']}, Link: {n['link']})\n"

    prompt = f"""You are an expert news curator. Summarize these Iranian political news items for a Telegram channel.
The news items are already grouped by category. PRESERVE these category groupings in your output.
Tone: VERY casual, friendly, conversational Persian (خودمونی).
Rules:
1. Summarize EACH item in exactly 1 short line.
2. At the end of EACH line, include the time ago info provided (e.g., ۲ ساعت پیش).
3. Format using HTML tags:
   Use category headers like: <b>[emoji] [category name]</b>
   Then each item:
   <b>• [خلاصه خبر]</b> ([زمان])
   🔗 <a href="[LINK]">منبع: [نام منبع]</a>
4. Use Persian numerals for numbers.
5. Keep it engaging.

News Items (grouped by category):
{formatted_news}
"""
    try:
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            return response.text
        else:
            return "⚠️ پاسخ هوش مصنوعی خالی بود."
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return f"خطا در پردازش هوش مصنوعی: {e}"


# ─── Telegram Sender ─────────────────────────────────────────────────────────
def send_to_telegram(text):
    """Send a message to Telegram, splitting if it exceeds the 4096 char limit."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    chunks = []
    while text:
        if len(text) <= TELEGRAM_MAX_LENGTH:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, TELEGRAM_MAX_LENGTH)
        if split_at == -1:
            split_at = TELEGRAM_MAX_LENGTH
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    for i, chunk in enumerate(chunks):
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = http_session.post(url, json=payload, timeout=30)
            if resp.status_code != 200:
                logger.error(
                    f"Telegram API error on chunk {i+1}/{len(chunks)}: "
                    f"{resp.status_code} — {resp.text[:200]}"
                )
            else:
                logger.info(f"Message part {i+1}/{len(chunks)}: sent OK")
            if i < len(chunks) - 1:
                time.sleep(1)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 50)
    logger.info("  Financial & Political News Bot")
    logger.info("=" * 50)

    logger.info("Aggregating markets and news...")
    financial_msg = get_financial_section()

    news_items = fetch_political_news()
    logger.info(f"Found {len(news_items)} news items.")

    # Log category stats
    stats = {}
    for item in news_items:
        cat = item["category"]
        stats[cat] = stats.get(cat, 0) + 1
    if stats:
        logger.info("News category breakdown:")
        for cat, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {cat}: {count} items")

    news_summary = get_ai_summary(news_items)

    final_message = (
        f"{financial_msg}\n"
        f"<b>📰 گزارش خبری (News Briefing)</b>\n\n"
        f"{news_summary}"
    )

    send_to_telegram(final_message)
    logger.info("Task completed successfully.")


if __name__ == "__main__":
    main()
