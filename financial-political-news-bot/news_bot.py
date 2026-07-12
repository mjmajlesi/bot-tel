import os
import sys
import requests
import json
import feedparser
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
import time

# Load env variables
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
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Please create a .env file or set them in your environment.")
        print("See .env.example for the required format.")
        sys.exit(1)

validate_env()

# ─── Gemini Setup ────────────────────────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# ─── Utility Functions ───────────────────────────────────────────────────────
def to_persian_num(n):
    """Convert a number to Persian numeral string."""
    if n is None:
        return "N/A"
    try:
        val = int(float(str(n).replace(',', '')))
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
        response = requests.get(url, timeout=15)
        if response.status_code == 429:
            print("CoinGecko rate limited (429). Waiting 30s and retrying...")
            time.sleep(30)
            response = requests.get(url, timeout=15)
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
        print(f"Error fetching crypto data: {e}")
        return {}
    except (KeyError, json.JSONDecodeError, TypeError) as e:
        print(f"Error parsing crypto data: {e}")
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
        resp = requests.get(
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

    except Exception as e:
        print(f"Error scraping TGJU: {e}")

    if result["USD"] is None:
        print("Warning: Could not scrape USD price from TGJU.")
    if result["Gold18k"] is None:
        print("Warning: Could not scrape Gold price from TGJU.")
    if result["Seke"] is None:
        print("Warning: Could not scrape Seke price from TGJU.")

    return result


# ─── Nobitex USD Price ───────────────────────────────────────────────────────
def get_nobitex_usd():
    """Fetch USDT/IRT price from Nobitex API. Returns Toman price or None."""
    try:
        url = "https://api.nobitex.ir/v2/orderbook/USDTIRT"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "ok":
            price = data.get("lastTradePrice")
            if price:
                return int(float(price))
    except Exception:
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
            print(f"Warning: Could not read history file: {e}")
            history = {}

    today_str = datetime.now().strftime("%Y-%m-%d")
    history[today_str] = current_data

    dates = sorted(history.keys(), reverse=True)
    if len(dates) > 30:
        for d in dates[30:]:
            del history[d]

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Warning: Could not write history file: {e}")

    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    last_week_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

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
    except:
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
    now = datetime.utcnow()
    
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
                        pub_dt = datetime(*entry.published_parsed[:6])
                        diff = now - pub_dt
                        
                        hours = diff.seconds // 3600
                        minutes = (diff.seconds % 3600) // 60
                        
                        if diff.days > 0:
                            time_ago_str = f"{to_persian_num(diff.days)} روز پیش"
                        elif hours > 0:
                            time_ago_str = f"{to_persian_num(hours)} ساعت و {to_persian_num(minutes)} دقیقه پیش"
                        else:
                            time_ago_str = f"{to_persian_num(minutes)} دقیقه پیش"

                    news.append({
                        "title": title,
                        "link": entry.link,
                        "source": name,
                        "time_ago": time_ago_str
                    })
                    seen.add(title_key)
        except Exception as e:
            print(f"Warning: Failed to parse feed '{name}': {e}")
            continue
    return news[:12]


# ─── AI Summary ──────────────────────────────────────────────────────────────
def get_ai_summary(news_list):
    if not news_list:
        return "خبر سیاسی مهمی یافت نشد."

    formatted_news = "\n".join(
        f"- {n['title']} (Source: {n['source']}, Time Ago: {n['time_ago']}, Link: {n['link']})"
        for n in news_list
    )

    prompt = f"""You are an expert news curator. Summarize these Iranian political news items for a Telegram channel.
Tone: VERY casual, friendly, conversational Persian (خودمونی).
Rules:
1. Summarize EACH item in exactly 1 short line.
2. At the end of EACH line, include the time ago info provided (e.g., ۲ ساعت پیش).
3. Format using HTML tags:
   <b>• [خلاصه خبر]</b> ([زمان])
   🔗 <a href="[LINK]">منبع: [نام منبع]</a>
4. Use Persian numerals for numbers.
5. Keep it engaging.

News Items:
{formatted_news}
"""
    try:
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            return response.text
        else:
            return "⚠️ پاسخ هوش مصنوعی خالی بود."
    except Exception as e:
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
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code != 200:
                print(f"Telegram API error on chunk {i+1}/{len(chunks)}: {resp.status_code} — {resp.text}")
            if i < len(chunks) - 1:
                time.sleep(1)
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print("Aggregating markets and news...")
    financial_msg = get_financial_section()
    news_items = fetch_political_news()
    print(f"Found {len(news_items)} news items.")
    news_summary = get_ai_summary(news_items)

    final_message = (
        f"{financial_msg}\n"
        f"<b>📰 گزارش خبری (News Briefing)</b>\n\n"
        f"{news_summary}"
    )

    send_to_telegram(final_message)
    print("Task completed successfully.")

if __name__ == "__main__":
    main()
