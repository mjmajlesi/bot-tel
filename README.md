# 📰 Bot-Tel — Persian Telegram News Bots

**A collection of AI-powered Telegram bots that deliver curated, categorized news digests in Persian — covering AI, finance, and politics.**

---

## 🤖 What's Inside

| Project | Description |
|---------|-------------|
| [`ai-news-bot/`](ai-news-bot/) | Curates the latest **AI news** from 12+ global sources, **classifies by category** (tools, research, companies, regulations, applications), translates via Gemini, and sends a Persian digest to Telegram |
| [`financial-political-news-bot/`](financial-political-news-bot/) | Delivers a comprehensive **financial market + political news** briefing — Iranian exchange rates, gold, crypto, and geopolitical headlines — with **automatic news categorization** |

Both bots share the same core pipeline:

```
Multiple Data Sources  →  News Classification  →  AI Summarization (Google Gemini)  →  Telegram Delivery
```

---

## ✨ Key Features

- **🆕 Keyword-based news classification** — Automatic categorization of every news item
- **AI-powered summarization** — Google Gemini translates and summarizes in natural Persian
- **Grouped output** — Digests organized by topic category for easy scanning
- **Proxy auto-detection** — Automatic local proxy support (v2rayN)
- **HTTP retry mechanism** — Exponential backoff for resilient data fetching
- **Structured logging** — Timestamped logs with severity levels

## ⚡ Quick Comparison

| | AI News Bot | Financial & Political Bot |
|---|---|---|
| **Focus** | AI / Tech news | Markets + Political news |
| **Data sources** | 12 RSS feeds (TechCrunch, OpenAI, HuggingFace, etc.) | TGJU scraping, Nobitex API, CoinGecko, 4 RSS feeds |
| **AI model** | Gemini 2.0 Flash Lite | Gemini 2.0 Flash Lite |
| **News categories** | 6 (Tools, Research, Companies, Regulations, Applications, Other) | 6 (Foreign Policy, Domestic, Economy, Science, Human Rights, Other) |
| **Config method** | `config.json` | `.env` file |
| **Language** | Persian | Persian |
| **Output** | Categorized numbered news digest | Market dashboard + categorized news summary |

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
pip install -r requirements.txt
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
├── LICENSE                            # MIT License
├── ai-news-bot/                       # AI news digest bot
│   ├── news_bot.py                    # Main script (with classifier)
│   ├── config.json                    # API keys & Telegram config
│   ├── requirements.txt              # Python dependencies
│   ├── run_ai_news.bat                # Windows launcher
│   ├── venv/                          # Virtual environment
│   └── README.md
└── financial-political-news-bot/      # Financial + political news bot
    ├── news_bot.py                    # Main script (with classifier)
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
- **requests** — HTTP calls with retry/backoff (TGJU, Nobitex, CoinGecko, Telegram)
- **python-dotenv** — Environment variable management
- **Keyword classifier** — Rule-based news categorization

---
