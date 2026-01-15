# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Topic Radar (專題雷達) is an AI-powered news monitoring dashboard for investigative journalists. It tracks abstract topics by scraping RSS feeds, filtering with multilingual keywords (ZH/EN/JA), translating international news, and generating AI summaries.

**Live Site**: https://topicradar.bonnnews.net (hosted on Render)

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
```

## Environment Variables (`.env`)

```ini
PERPLEXITY_API_KEY=pplx-...   # Summaries (https://www.perplexity.ai/settings/api)
PERPLEXITY_MODEL=sonar
GEMINI_API_KEY=AIza...        # Keywords + Translation
TZ=Asia/Taipei                # Timezone for scheduler
```

## Architecture

### Core Data Flow

1. **RSS Scraping** → 8 TW sources + 4 intl sources (Guardian, BBC, Asahi)
2. **Keyword Filtering** → Multilingual: ZH for Taiwan, EN/JA for international
3. **Translation** → Gemini translates EN/JA headlines to Traditional Chinese
4. **AI Summary** → Perplexity generates 100-word latest progress summary

### Key Files

| File | Purpose |
|------|---------|
| `app.py` | Flask backend, API endpoints, AI integration, scheduler |
| `topics_config.json` | Topic database (persisted) |
| `index.html` | Frontend dashboard |
| `admin.html` | Admin interface (CRUD topics) |
| `script.js` | Frontend logic |
| `style.css` | Styling |

### Scheduler Configuration

```python
# News: every 30 minutes
scheduler.add_job(update_topic_news, 'interval', minutes=30)

# AI Summaries: daily at 08:00 and 18:00 (Taipei time)
scheduler.add_job(update_all_summaries, 'cron', hour=8, minute=0)
scheduler.add_job(update_all_summaries, 'cron', hour=18, minute=0)
```

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/all` | All topics + news + summaries |
| POST | `/api/refresh` | Trigger news update |
| POST | `/api/refresh-summary` | Trigger AI summary |
| GET | `/api/admin/topics` | Get topics config |
| POST | `/api/admin/topics` | Create topic (AI keywords) |
| PUT | `/api/admin/topics/<tid>` | Update keywords |
| DELETE | `/api/admin/topics/<tid>` | Delete topic |

## Deployment (Render.com)

**URL**: https://topicradar.onrender.com

**Custom Domain**: topicradar.bonnnews.net

**Files**:
- `requirements.txt` - Dependencies
- `render.yaml` - Render config
- `.gitignore` - Excludes .env, venv, __pycache__

**Start Command**:
```bash
cp /etc/secrets/.env .env && gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2
```

**Environment**: Set via Render Secret File (`.env`)

## AI Integration

### Gemini (Keywords + Translation)
- Model: `gemini-2.0-flash`
- Generates 10-15 keywords in ZH/EN/JA for each topic
- Translates international headlines to Traditional Chinese
- Rate limit handling: 0.5s delay between requests, 3 retries

### Perplexity (Summaries)
- Model: `sonar`
- Generates 100-word "latest progress" summary
- Runs at 08:00 and 18:00 daily
- Removes markdown symbols from output

## Important Notes

- **No Database**: State in-memory (`DATA_STORE`), only `topics_config.json` persists
- **Deduplication**: MD5 hash of title prevents duplicates
- **Port**: 5001 (avoid conflicts)
- **Free Tier**: Render sleeps after 15min idle, ~30s cold start

## Common Workflows

### Test RSS
```bash
python3
>>> from app import fetch_rss
>>> items = fetch_rss('https://udn.com/rssfeed/news/2/0', '聯合報')
>>> print(len(items))
```

### Manual API Test
```bash
curl -X POST http://localhost:5001/api/refresh
curl http://localhost:5001/api/all | python3 -m json.tool | head -50
```

### Deploy Updates
```bash
git add . && git commit -m "Update" && git push origin main
# Render auto-deploys from GitHub
```
