# 🤖 AI News Bot

**A Telegram bot that curates the latest AI news from top sources worldwide, translates them into Persian using Google Gemini, and delivers a beautifully formatted daily digest — now with automatic news categorization.**

---

## ✨ Features

- **Multi-source aggregation** — Fetches from 12+ reputable AI news RSS feeds
- **🆕 Keyword-based news classification** — Automatically categorizes each news item into:
  - 🛠️ ابزارها و محصولات جدید (New Tools & Products)
  - 📄 مقالات پژوهشی (Research Papers)
  - 🏢 اخبار شرکت‌ها (Company News)
  - ⚖️ قوانین و اخلاق هوش مصنوعی (AI Regulations & Ethics)
  - 🤖 کاربردهای هوش مصنوعی (AI Applications)
  - 📰 سایر اخبار (Other News)
- **AI-powered summarization** — Google Gemini selects the top 10–15 stories and writes a Persian digest
- **Grouped output** — News items are organized by category in the final digest
- **Persian output** — Natural, fluent Persian with Persian numerals (۱۲۳)
- **Telegram HTML formatting** — Clean, readable messages optimized for Telegram
- **Smart deduplication** — Avoids duplicate headlines across sources
- **Date awareness** — Each item includes relative publish time (e.g., "۲ روز پیش")
- **Long message splitting** — Automatically chunks messages exceeding Telegram's 4096-char limit
- **🆕 Proper logging** — Structured logging with timestamps instead of bare `print()`
- **🆕 HTTP retry mechanism** — Automatic retry with exponential backoff for failed requests
- **🆕 Proxy auto-detection** — Detects and uses local proxy (v2rayN) if available

## 📰 News Sources

| Source | Focus |
|--------|-------|
| AI News (FeedBurner) | General AI |
| Artificial Intelligence News | General AI |
| TechCrunch | AI & Tech |
| MIT Technology Review | Deep Tech |
| VentureBeat | AI & Enterprise |
| Ars Technica | AI & Science |
| The Verge | AI & Consumer Tech |
| Google AI Blog | Google Research |
| Hugging Face Blog | Open Source AI |
| OpenAI Blog | OpenAI Updates |
| MarkTechPost | ML & Research |
| Synced Review | AI Research |

## 🏷️ News Classification

The bot uses a **keyword-based classifier** to automatically categorize each news item before sending it to Gemini. This ensures the final digest is **organized by topic**, making it easier to scan.

**How it works:**
1. Each news item's title + summary is scanned against keyword lists for each category
2. Keywords are weighted by occurrence count — the category with the most keyword hits wins
3. Items with no keyword matches fall into "📰 سایر اخبار" (Other News)
4. Gemini receives pre-grouped items and preserves the category structure in its output

**Example output:**
```
📰 آخرین اخبار هوش مصنوعی

🛠️ ابزارها و محصولات جدید
۱. گوگل ابزار جدید Gemini 2.0 را معرفی کرد ...
۲. متا یک فریمورک اوپن‌سورس جدید عرضه کرد ...

📄 مقالات پژوهشی
۳. محققان MIT مدل جدیدی برای پردازش زبان طبیعی ارائه دادند ...

🏢 اخبار شرکت‌ها
۴. OpenAI سرمایه‌گذاری ۱۰ میلیارد دلاری جذب کرد ...
```

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
cd ai-news-bot

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `config.json` in the project root:

```json
{
  "gemini_api_key": "AIzaSy...",
  "telegram_bot_token": "123456789:ABCdefGhIJKlmNoPQRsTUVwxyz",
  "telegram_chat_id": "your_chat_id"
}
```

> You can also set these as environment variables: `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

### Running

```bash
python news_bot.py
```

Or on Windows, double-click `run_ai_news.bat`.

## 📋 How It Works

```
RSS Feeds (12 sources)
        │
        ▼
┌──────────────────┐
│  Fetch & Dedupe  │  Parse feeds, extract titles + summaries + dates
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Classify News   │  Keyword-based categorization into 6 categories
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Gemini Flash    │  Select top stories, translate to Persian,
│  (AI Summarize)  │  format as grouped numbered list with HTML
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Telegram API    │  Send HTML-formatted digest (split if needed)
└──────────────────┘
```

## 📂 Project Structure

```
ai-news-bot/
├── news_bot.py          # Main bot script
├── config.json          # API keys & chat config
├── requirements.txt     # Python dependencies
├── run_ai_news.bat      # Windows batch launcher
├── README.md            # This file
└── venv/                # Python virtual environment
```

## ⚙️ Customization

**Adding feeds:** Edit the `FEEDS` list in `news_bot.py` — just add RSS URLs.

**Adding categories:** Edit the `CATEGORIES` dict in `news_bot.py` — add new keyword groups.

**Changing the AI model:** Modify the `genai.GenerativeModel(...)` line.

**Adjusting digest size:** Edit the prompt in `translate_and_format()` to request more or fewer items.

## 🛠️ Tech Stack

- **Python 3.11+**
- **feedparser** — RSS/Atom feed parsing
- **google-generativeai** — Gemini API client
- **requests** — HTTP calls with retry mechanism

---

**Maintainer:** [MatinSenPaii](https://github.com/MatinSenPaii)
**License:** MIT
