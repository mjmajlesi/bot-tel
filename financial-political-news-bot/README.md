# 📊 Financial & Political News Bot

**A Telegram bot that delivers a comprehensive daily briefing of Iranian financial markets and political news — powered by AI summarization via Google Gemini.**

---

## ✨ Features

### 💹 Financial Market Data
- **Dollar rate** from TGJU (Tehran Gold & Jewelry Exchange) — the official reference
- **Dollar rate** from Nobitex (Iranian crypto exchange) — USDT/IRT pair
- **Gold 18K price** per gram
- **Imam Coin (سکه امامی)** price
- **Crypto prices** — BTC, ETH with 24h/7d percentage changes via CoinGecko
- **Trend tracking** — daily & weekly percentage changes with 📈/📉 indicators
- **30-day history** stored in `history.json` for comparative analysis

### 📰 Political News Intelligence
- **Multi-source aggregation** from BBC Persian, Radio Farda, Al Jazeera, Reuters
- **Iran-focused filtering** for international sources (Al Jazeera, Reuters)
- **AI-powered summarization** — casual, conversational Persian tone (خودمونی)
- **Relative timestamps** in Persian (e.g., "۳ ساعت و ۱۵ دقیقه پیش")

### 🔧 Technical Highlights
- **Persian numeral conversion** throughout all outputs
- **TGJU HTML scraping** with regex patterns and fallback mechanisms
- **Graceful degradation** — continues if any single data source fails
- **Smart message splitting** for Telegram's 4096-char limit
- **Rate limit handling** for CoinGecko (auto-retry on 429)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- A Google Gemini API key ([get one here](https://aistudio.google.com/apikey))
- A Telegram bot token ([via @BotFather](https://t.me/BotFather))
- Your Telegram chat ID

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd financial-political-news-bot

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
GEMINI_API_KEY=AIzaSy...
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyz
TELEGRAM_CHAT_ID=-1001234567890
```

### Running

```bash
python news_bot.py
```

## 📋 How It Works

```
┌─────────────────────┐     ┌──────────────────────┐
│  Financial Sources  │     │   News Sources        │
│                     │     │                       │
│  • TGJU (scraping)  │     │  • BBC Persian        │
│  • Nobitex API      │     │  • Radio Farda        │
│  • CoinGecko API    │     │  • Al Jazeera         │
└─────────┬───────────┘     │  • Reuters            │
          │                 └──────────┬────────────┘
          ▼                            ▼
┌─────────────────────┐     ┌──────────────────────┐
│  Market Analysis    │     │  News Fetching       │
│  • Price parsing    │     │  • RSS parsing       │
│  • Trend calc       │     │  • Iran filtering    │
│  • History update   │     │  • Deduplication     │
└─────────┬───────────┘     └──────────┬───────────┘
          │                            │
          ▼                            ▼
┌─────────────────────┐     ┌──────────────────────┐
│  Formatted Report   │     │  Gemini AI Summary   │
│  (HTML for TG)      │     │  (casual Persian)    │
└─────────┬───────────┘     └──────────┬───────────┘
          │                            │
          └──────────┬─────────────────┘
                     ▼
            ┌─────────────────┐
            │  Telegram API   │
            │  (send message) │
            └─────────────────┘
```

## 📂 Project Structure

```
financial-political-news-bot/
├── news_bot.py          # Main bot (all logic)
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── .gitignore           # Git ignore rules
├── history.json         # 30-day price history (auto-generated)
├── README.md            # This file
└── venv/                # Python virtual environment
```

## 📊 Sample Output

```
📊 وضعیت بازار (Market Update)

💵 دلار (TGJU): ۱,۷۹۶,۹۵۰ تومان
   نسبت به دیروز: 📈 ۰.۸٪

🔗 دلار (نوبیتکس): ۱,۷۹۸,۰۰۰ تومان
   نسبت به دیروز: 📈 ۰.۹٪

🪙 طلا ۱۸ عیار: ۱۷۶,۴۹۷,۰۰۰ تومان
   نسبت به دیروز: 📈 ۱.۰٪

💰 سکه امامی: ۱,۷۸۵,۰۵۰,۰۰۰ تومان
   نسبت به دیروز: 📉 ۱.۴٪

₿ BTC: ۶۳,۸۳۱ USD (24h: ۲.۱٪)
₿ ETH: ۱,۷۹۸ USD (24h: ۱.۳٪)

📰 گزارش خبری (News Briefing)

• مذاکرات هسته‌ای به توافق نزدیک شد (۲ ساعت پیش)
• شاخص‌های اقتصادی بهبود یافتند (۳ ساعت پیش)
• ...
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| AI Model | Google Gemini 1.5 Flash |
| Iranian Market Data | TGJU scraping + Nobitex API |
| Crypto Prices | CoinGecko API |
| News Feeds | feedparser (RSS/Atom) |
| Messaging | Telegram Bot API (HTML mode) |
| Environment | python-dotenv |

## ⚠️ Notes

- **TGJU scraping** depends on the current HTML structure — if TGJU changes their layout, regex patterns may need updating
- **CoinGecko** has rate limits; the bot auto-retries after a 30s cooldown on 429 errors
- **Nobitex** may be unreachable from certain regions; the bot silently continues without it
- **History** is retained for 30 days in `history.json` (auto-pruned)

---

**Maintainer:** [MatinSenPaii](https://github.com/MatinSenPaii)
**License:** MIT
