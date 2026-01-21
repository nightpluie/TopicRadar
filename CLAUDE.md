# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Topic Radar (專題雷達) is an AI-powered news monitoring dashboard for investigative journalists. It tracks abstract topics by scraping RSS feeds, filtering with multilingual keywords (ZH/EN/JA), translating international news, and generating AI summaries.

**Live Site**: https://topicradar.bonnews.net (hosted on Render)

**Tech Stack**:
- Backend: Python Flask, APScheduler
- Frontend: Vanilla JS/HTML/CSS
- AI: Perplexity (summaries), Gemini (keywords + translation)
- Hosting: Render.com

## Development Commands

```bash
# Setup & Run
cd ~/Desktop/TopicRadar
source venv/bin/activate
python3 app.py  # http://localhost:5001

# Install Dependencies
pip install -r requirements.txt

# Quick Start (using shell script)
./start_server.sh

# Update Keywords for All Topics (batch operation)
python3 update_keywords.py
```

## Environment Variables (`.env`)

```ini
PERPLEXITY_API_KEY=pplx-...   # Summaries (https://www.perplexity.ai/settings/api)
PERPLEXITY_MODEL=sonar
GEMINI_API_KEY=AIza...        # Keywords + Translation
TZ=Asia/Taipei                # Timezone for scheduler
```

Note: `.env.example` contains template with Chinese comments. `ANTHROPIC_API_KEY` is deprecated but referenced in `update_keywords.py`.

## Architecture

### Core Data Flow

1. **RSS Scraping** → 8 TW sources + 4 intl sources (Guardian, BBC, NHK, Asahi)
2. **Keyword Filtering** → Multilingual: ZH for Taiwan, EN/JA for international
3. **Translation** → Gemini translates EN/JA headlines to Traditional Chinese
4. **AI Summary** → Perplexity generates 200-word "latest progress" summary

### Data Storage Model

**In-Memory State** (`DATA_STORE` dict):
- `topics`: Taiwan news per topic (max 10 recent items)
- `international`: International news per topic (max 10 recent items)
- `summaries`: AI-generated summaries with timestamps
- `last_update`: ISO timestamp of last news update

**Persisted** (`topics_config.json`):
- Topic configurations (name, keywords in ZH/EN/JA, negative_keywords, icon)
- Structured as `{topic_id: {name, keywords: {zh: [], en: [], ja: []}, negative_keywords: [], icon}}`

**Important**: Server restart clears all news data. Only topic configs persist.

### Key Files

| File | Purpose |
|------|---------|
| `app.py:760-772` | Initialization: loads topics, starts scheduler, first update |
| `app.py:442-566` | `update_topic_news()`: RSS fetch, filter, translate, deduplicate |
| `app.py:252-315` | `generate_topic_summary()`: Perplexity API integration |
| `app.py:116-193` | `generate_keywords_with_ai()`: Gemini keyword generation |
| `app.py:196-248` | `translate_with_gemini()`: Gemini translation with retry logic |
| `app.py:415-440` | `keyword_match()`: Filtering logic with negative keyword support |
| `topics_config.json` | Persisted topic database |
| `index.html` | Frontend dashboard |
| `admin.html` | Admin interface (CRUD topics) |
| `update_keywords.py` | Batch keyword regeneration script (uses deprecated Claude API) |

### Scheduler Configuration

```python
# News: every 30 minutes
scheduler.add_job(update_topic_news, 'interval', minutes=30)

# AI Summaries: daily at 08:00 and 18:00 (Taipei time)
scheduler.add_job(update_all_summaries, 'cron', hour=8, minute=0)
scheduler.add_job(update_all_summaries, 'cron', hour=18, minute=0)
```

All times use `TAIPEI_TZ = ZoneInfo('Asia/Taipei')` for consistency.

### RSS Sources

**Taiwan** (8 sources in `RSS_SOURCES_TW`):
- UDN (聯合報, 聯合報財經)
- LTN (自由時報, 自由財經)
- ETtoday (即時, 財經)
- 報導者, Google News TW, 公視新聞, 鏡週刊

**International** (4 sources in `RSS_SOURCES_INTL`):
- BBC News, The Guardian (English)
- NHK, 朝日新聞 (Japanese)

**Google News Fallback**: If filtered news < 10 items, `fetch_google_news_by_keywords()` supplements with keyword search results (app.py:359-413).

### API Endpoints

| Method | Endpoint | Purpose | Notes |
|--------|----------|---------|-------|
| GET | `/api/all` | All topics + news + summaries | Main data endpoint for dashboard |
| POST | `/api/refresh` | Trigger news update | Calls `update_topic_news()` |
| POST | `/api/refresh-summary` | Trigger AI summary | Calls `update_all_summaries()` |
| GET | `/api/admin/topics` | Get topics config | Includes news_count, summary |
| POST | `/api/admin/topics` | Create topic | Auto-generates keywords with Gemini |
| PUT | `/api/admin/topics/<tid>` | Update keywords | Updates both keywords and negative_keywords |
| DELETE | `/api/admin/topics/<tid>` | Delete topic | Removes from config |

### Deduplication Logic

Uses MD5 hash of news titles to prevent duplicates (app.py:478, 504, 511, 542). Existing hashes are preserved when merging new items with in-memory storage.

### Translation & Rate Limiting

- Gemini translation has 3 retries with exponential backoff (2s, 4s, 6s) for 429 errors (app.py:197-248)
- 0.5s delay between international news translations to avoid rate limits (app.py:551)
- Perplexity summary: 1s delay between topics (app.py:575)

### Keyword Filtering

**Positive Keywords** (app.py:415-440):
- Match any keyword in title or summary (case-insensitive)
- Taiwan news: uses `keywords.zh` array
- International news: uses combined `keywords.en + keywords.ja` arrays

**Negative Keywords**:
- Excludes news matching any negative keyword (e.g., "藝人", "明星" to filter entertainment)
- Checked before positive keywords for efficiency

**Format Compatibility**:
- Old format: `keywords: []` (plain array)
- New format: `keywords: {zh: [], en: [], ja: []}` (multilingual dict)
- Code handles both formats (app.py:459-467, 648-652, 681-686)

## Deployment (Render.com)

**URL**: https://topicradar.onrender.com

**Custom Domain**: topicradar.bonnews.net

**Files**:
- `requirements.txt` - Dependencies
- `render.yaml` - Render config (1 worker, 2 threads)
- `.gitignore` - Excludes .env, venv, __pycache__

**Start Command**:
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2
```

**Environment**: Set API keys via Render dashboard (Secret Files or Environment Variables). `TZ=Asia/Taipei` is defined in `render.yaml`.

**Cold Start**: Render free tier sleeps after 15min idle, ~30s cold start. Scheduler resumes automatically.

## AI Integration

### Gemini (Keywords + Translation)
- Model: `gemini-2.0-flash`
- Generates 10-15 ZH keywords, 8-10 EN/JA keywords for each topic
- Translation prompt: "請將以下新聞標題翻譯成繁體中文，只輸出翻譯結果"
- Rate limit handling: 0.5s delay between requests, 3 retries with backoff
- API endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`

### Perplexity (Summaries)
- Model: `sonar` (configurable via `PERPLEXITY_MODEL`)
- Generates 200-word "progress report" style summaries (NOT introductory explainers)
- System prompt: "你是一位資深專題記者，正在為已經熟悉議題背景的同事更新最新進展"
- Runs at 08:00 and 18:00 daily (Taipei time)
- Removes markdown symbols ([1], [2], **, *, #) from output (app.py:302-309)
- API endpoint: `https://api.perplexity.ai/chat/completions`

## Important Implementation Details

- **No Database**: All news data is in-memory (`DATA_STORE`). Only `topics_config.json` persists.
- **Port**: 5001 (avoid conflicts with common dev servers)
- **SSL Warnings Disabled**: `urllib3.disable_warnings()` for RSS scraping (app.py:756-757)
- **Timezone Consistency**: All datetime objects use `TAIPEI_TZ` (app.py:19, 278, 338-345, 602-616)
- **Gunicorn Config**: `use_reloader=False` prevents duplicate scheduler jobs (app.py:772)
- **Scheduler Init**: Called at module level for Gunicorn compatibility (app.py:761)

## Testing & Debugging

### Test RSS Scraping
```bash
python3
>>> from app import fetch_rss
>>> items = fetch_rss('https://udn.com/rssfeed/news/2/0', '聯合報')
>>> print(len(items))
>>> print(items[0]['title'])
```

### Test Keyword Filtering
```bash
python3
>>> from app import keyword_match
>>> keyword_match('移工政策改革', ['移工', '外勞'], ['娛樂', '明星'])
True
```

### Manual API Test
```bash
# Trigger news update
curl -X POST http://localhost:5001/api/refresh

# View all data
curl http://localhost:5001/api/all | python3 -m json.tool | head -50

# View topics config
curl http://localhost:5001/api/admin/topics | python3 -m json.tool
```

### Check Scheduler Status
Monitor console output for:
- `[UPDATE] 開始更新新聞 - HH:MM:SS` (every 30min)
- `[SUMMARY] 開始 AI 摘要...` (08:00, 18:00)
- `[SEARCH] {topic}: 只有 N 則，使用 Google News 搜索補充...` (fallback triggered)

## Deployment Workflow

```bash
# 1. Test locally
source venv/bin/activate
python3 app.py

# 2. Commit changes
git add .
git commit -m "Update: description"

# 3. Push to GitHub
git push origin main
# Render auto-deploys from GitHub main branch

# 4. Monitor deployment
# Check Render dashboard for build logs
```

## Common Issues & Solutions

**News Count < 10 for Topic**:
- Check if keywords are too specific (app.py:499-516 triggers Google News fallback)
- Review negative_keywords - may be over-filtering
- Verify RSS sources are accessible

**Translation Failures**:
- Check Gemini API quota/rate limits
- Look for `[翻譯失敗]` prefix in international news titles
- Retry logic should auto-recover from transient errors

**Scheduler Not Running**:
- Verify `init_scheduler()` is called at module level (app.py:761)
- Check `use_reloader=False` in app.run() to prevent duplicate jobs
- For Gunicorn: use `--workers 1` (multiple workers = multiple schedulers)

**Topics Lost After Restart**:
- Only `topics_config.json` persists - verify file exists and is writable
- News data (`DATA_STORE`) is intentionally ephemeral - will repopulate on next update cycle
