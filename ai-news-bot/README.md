# 🤖 AI News Bot

**A Telegram bot that curates the latest AI news from top sources worldwide, translates them into Persian using Google Gemini, and delivers a beautifully formatted daily digest.**

---

## ✨ Features

- **Multi-source aggregation** — Fetches from 12+ reputable AI news RSS feeds
- **AI-powered summarization** — Google Gemini selects the top 10–15 stories and writes a Persian digest
- **Persian output** — Natural, fluent Persian with Persian numerals (۱۲۳)
- **Telegram HTML formatting** — Clean, readable messages optimized for Telegram
- **Smart deduplication** — Avoids duplicate headlines across sources
- **Date awareness** — Each item includes relative publish time (e.g., "۲ روز پیش")
- **Long message splitting** — Automatically chunks messages exceeding Telegram's 4096-char limit

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
pip install feedparser google-generativeai requests
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
│  Gemini Flash    │  Select top stories, translate to Persian,
│  (AI Summarize)  │  format as numbered list with HTML
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
├── run_ai_news.bat      # Windows batch launcher
├── README.md            # This file
└── venv/                # Python virtual environment
```

## ⚙️ Customization

**Adding feeds:** Edit the `FEEDS` list in `news_bot.py` — just add RSS URLs.

**Changing the AI model:** Modify the `genai.GenerativeModel('gemini-3.1-flash-lite')` line.

**Adjusting digest size:** Edit the prompt in `translate_and_format()` to request more or fewer items.

## 📊 Sample Output

```
📰 آخرین اخبار هوش مصنوعی

۱. گوپل مدل جدید Gemini 2.0 را معرفی کرد
   این مدل قابلیت‌های جدیدی در پردازش تصویر و متن دارد.
   (۳ ساعت پیش — TechCrunch)

۲. متا ابزار جدید هوش مصنوعی برای کدنویسی عرضه کرد
   ... 
```

## 🛠️ Tech Stack

- **Python 3.11+**
- **feedparser** — RSS/Atom feed parsing
- **google-generativeai** — Gemini API client
- **requests** — HTTP calls to Telegram API

---

**Maintainer:** [MatinSenPaii](https://github.com/MatinSenPaii)
**License:** MIT
