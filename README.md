# 📰 Bot-Tel — Persian Telegram News Bots

**A collection of AI-powered Telegram bots that deliver curated news digests in Persian — covering AI, finance, and politics.**

---

## 🤖 What's Inside

| Project | Description |
|---------|-------------|
| [`ai-news-bot/`](ai-news-bot/) | Curates the latest **AI news** from 12+ global sources, translates via Gemini, and sends a Persian digest to Telegram |
| [`financial-political-news-bot/`](financial-political-news-bot/) | Delivers a comprehensive **financial market + political news** briefing — Iranian exchange rates, gold, crypto, and geopolitical headlines |

Both bots share the same core pipeline:

```
Multiple Data Sources  →  AI Summarization (Google Gemini)  →  Telegram Delivery
```

---

## ⚡ Quick Comparison

| | AI News Bot | Financial & Political Bot |
|---|---|---|
| **Focus** | AI / Tech news | Markets + Political news |
| **Data sources** | 12 RSS feeds (TechCrunch, OpenAI, HuggingFace, etc.) | TGJU scraping, Nobitex API, CoinGecko, 4 RSS feeds |
| **AI model** | Gemini 3.1 Flash Lite | Gemini 1.5 Flash |
| **Config method** | `config.json` | `.env` file |
| **Language** | Persian | Persian |
| **Output** | Numbered news digest | Market dashboard + news summary |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Google Gemini API key → [Get one here](https://aistudio.google.com/apikey)
- Telegram Bot token → [via @BotFather](https://t.me/BotFather)
- Your Telegram chat ID

### Setup (either bot)

```bash
cd ai-news-bot    # or financial-political-news-bot

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt    # if available
# or
pip install feedparser google-generativeai requests python-dotenv
```

Then configure your API keys (see each project's README for details) and run:

```bash
python news_bot.py
```

---

## 📁 Repository Structure

```
bot-tel/
├── README.md                          # ← You are here
├── ai-news-bot/                       # AI news digest bot
│   ├── news_bot.py                    # Main script
│   ├── config.json                    # API keys & Telegram config
│   ├── run_ai_news.bat                # Windows launcher
│   ├── venv/                          # Virtual environment
│   └── README.md
└── financial-political-news-bot/      # Financial + political news bot
    ├── news_bot.py                    # Main script
    ├── requirements.txt               # Python dependencies
    ├── .env.example                   # Environment template
    ├── .gitignore                     # Git ignore rules
    ├── history.json                   # 30-day price history (auto-generated)
    ├── run_bot.bat                    # Windows launcher
    ├── venv/                          # Virtual environment
    └── README.md
```

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **Google Gemini** — AI summarization & Persian translation
- **Telegram Bot API** — HTML-formatted message delivery
- **feedparser** — RSS/Atom feed parsing
- **requests** — HTTP calls to APIs (TGJU, Nobitex, CoinGecko, Telegram)
- **python-dotenv** — Environment variable management

---
