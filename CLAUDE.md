# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 核心原則 (CRITICAL - READ FIRST)

### 1. 專案定位
**深度報導與專題追蹤工具**
- 目標：為調查記者提供議題進展追蹤與靈感
- **非即時新聞監控**，重視議題脈絡與趨勢分析
- 更新頻率適中（每小時），適合長期追蹤

### 2. 專業導向
**介面必須保持專業簡潔**
- ❌ **嚴禁使用顏文字**（emoji）於任何程式碼、介面、功能中
- ❌ 不使用裝飾性圖示或符號
- ✅ 專注於資訊密度與可讀性
- ✅ 使用文字標籤、純文字描述

**例外情況**：
- 文件中的說明性標記（如本文件的 ✅ ❌）僅限用於 Markdown 文件
- 程式碼、UI、資料庫中一律不使用顏文字

### 3. 版本管理
- 遵循語意化版本號 (Semantic Versioning): `主版本號.次版本號.修訂號`
- 當前版本：**v2.1.0**
- 每次更新前必須更新 `CHANGELOG.md`
- 版本號顯示於前端底部（index.html）

## Overview

TopicRadar (專題雷達) is an AI-powered news monitoring dashboard for investigative journalists. It tracks abstract topics by scraping RSS feeds, filtering with multilingual keywords (ZH/EN/JA/KO), translating international news, and generating AI summaries.

**Current Version**: v2.1  
**Live Site**: https://topicradar.bonnews.net (hosted on Render)

**Tech Stack**: Python Flask, APScheduler, Vanilla JS/HTML/CSS, Perplexity (summaries), Gemini (keywords + translation), Supabase (auth + user data), Render.com (hosting)

### v2.1 New Features (2026-01-22)

- 🌐 **Multilingual Keyword Management**: Automatic translation of keywords to EN/JA/KO, language indicators (EN/JP/KR badges)
- ⚡ **Performance Optimizations**: 
  - Auto-translation speed: 3x faster (3-6s → 1-2s, one API call instead of three)
  - Topic creation: 10-20x faster (15-40s → 1-2s, background threading for news/summary generation)
  - Loading status display for background tasks
- 🔧 **Batch Translation Script**: Retroactively add multilingual keywords to all existing topics

## Development Commands

```bash
# Setup & Run
cd ~/Desktop/TopicRadar
source venv/bin/activate
python3 app.py  # Runs on http://localhost:5001

# Install Dependencies
pip install -r requirements.txt

# Quick Start
./start_server.sh

# Setup Scripts (scripts/setup/)
python3 scripts/setup/setup_admin.py          # Create admin user
python3 scripts/setup/create_test_user.py     # Create test user
python3 scripts/setup/update_keywords.py      # Batch regenerate keywords for all topics
python3 scripts/setup/update_invite_code.py   # Update invite codes

# Batch Translation Script (NEW in v2.1)
python3 scripts/batch_translate_topics.py     # Add multilingual keywords to existing topics

# Test Scripts (scripts/test/)
python3 scripts/test/test_supabase.py         # Test Supabase connection
python3 scripts/test/verify_cache.py          # Verify cache file integrity
```

## Environment Variables (`.env`)

```ini
# AI APIs
PERPLEXITY_API_KEY=pplx-...   # Summaries (https://www.perplexity.ai/settings/api)
PERPLEXITY_MODEL=sonar
GEMINI_API_KEY=AIza...        # Keywords + Translation
ANTHROPIC_API_KEY=sk-...      # Legacy (used in update_keywords.py)

# Supabase (Authentication)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# Timezone
TZ=Asia/Taipei
```

See `.env.example` for template with Chinese comments.

## Core Architecture

### Data Flow

1. **RSS Scraping** → 8 Taiwan sources + 4 international sources (Guardian, BBC, NHK, Asahi)
2. **Keyword Filtering** → Multilingual: ZH for Taiwan, EN/JA for international
3. **Translation** → Gemini translates EN/JA headlines to Traditional Chinese
4. **AI Summary** → Perplexity generates 200-word "latest progress" summary

### Data Storage Model

**In-Memory State** (`DATA_STORE` dict in app.py):
- `topics`: Taiwan news per topic (max 10 recent items)
- `international`: International news per topic (max 10 recent items)
- `summaries`: AI-generated summaries with timestamps
- `last_update`: ISO timestamp of last news update
- `topic_owners`: User ownership mapping `{topic_id: user_id}`

**Persisted Files**:
- `topics_config.json`: Topic configurations (name, keywords {zh, en, ja}, negative_keywords, icon)
- `data_cache.json`: Cached news data for fast serving (ephemeral on Render free tier)

**Supabase Database**:
- `auth.users`: User accounts (managed by Supabase Auth)
- `user_roles`: User role assignments (admin/user)
- `invite_codes`: Registration invite codes
- User-specific topic configs (being migrated)

**Important**: Server restart clears in-memory `DATA_STORE`. Only `topics_config.json` and Supabase data persist.

### Key Files & Line References

| File | Lines | Purpose |
|------|-------|---------|
| `app.py:760-772` | Init | Loads topics, starts scheduler, first update |
| `app.py:442-566` | `update_topic_news()` | RSS fetch, filter, translate, deduplicate |
| `app.py:252-315` | `generate_topic_summary()` | Perplexity API integration |
| `app.py:116-193` | `generate_keywords_with_ai()` | Gemini keyword generation |
| `app.py:196-248` | `translate_with_gemini()` | Gemini translation with retry logic |
| `app.py:415-440` | `keyword_match()` | Filtering logic with negative keyword support |
| `app.py:599-646` | `fetch_google_news_by_keywords()` | Google News fallback search |
| `auth.py` | All | Supabase authentication decorators (`@require_auth`, `@require_admin`) |
| `topics_config.json` | All | Persisted topic database |
| `data_cache.json` | All | Cached news data (auto-generated) |
| `index.html` | All | Frontend dashboard |
| `admin.html` | All | Admin interface (CRUD topics) |
| `login.html` | All | Login/signup page |

### Scheduler Configuration

```python
# News updates: every 30 minutes
scheduler.add_job(update_topic_news, 'interval', minutes=30)

# AI Summaries: daily at 08:00 and 18:00 (Taipei time)
scheduler.add_job(update_all_summaries, 'cron', hour=8, minute=0)
scheduler.add_job(update_all_summaries, 'cron', hour=18, minute=0)
```

All times use `TAIPEI_TZ = ZoneInfo('Asia/Taipei')` for consistency (app.py:19).

### RSS Sources

**Taiwan** (8 sources in `RSS_SOURCES_TW`, app.py:40-51):
- UDN (聯合報, 聯合報財經)
- LTN (自由時報, 自由財經)
- ETtoday (即時, 財經)
- 報導者, Google News TW, 公視新聞, 鏡週刊

**International** (4 sources in `RSS_SOURCES_INTL`, app.py:54-59):
- BBC News, The Guardian (English)
- NHK, 朝日新聞 (Japanese)

**Google News Fallback**: If filtered news < 10 items, `fetch_google_news_by_keywords()` supplements with keyword search results (app.py:599-646).

### API Endpoints

| Method | Endpoint | Purpose | Auth Required | Notes |
|--------|----------|---------|---------------|-------|
| GET | `/api/all` | All topics + news + summaries | No | Main data endpoint for dashboard |
| POST | `/api/refresh` | Trigger news update | No | Calls `update_topic_news()` |
| POST | `/api/refresh-summary` | Trigger AI summary | No | Calls `update_all_summaries()` |
| GET | `/api/admin/topics` | Get topics config | Yes | Includes news_count, summary |
| POST | `/api/admin/topics` | Create topic | Yes | Auto-generates keywords with Gemini |
| PUT | `/api/admin/topics/<tid>` | Update keywords | Yes | Updates both keywords and negative_keywords |
| DELETE | `/api/admin/topics/<tid>` | Delete topic | Yes | Removes from config |
| POST | `/api/auth/login` | User login | No | Returns JWT token |
| POST | `/api/auth/signup` | User registration | No | Requires invite code |
| GET | `/api/auth/me` | Current user info | Yes | Returns user profile |

### Authentication System (auth.py)

**Decorators**:
- `@require_auth`: Requires valid JWT token, adds `g.user`, `g.user_id`, `g.is_admin`
- `@require_admin`: Requires admin role (stacks on `@require_auth`)

**Functions**:
- `get_supabase()`: Returns singleton Supabase client
- `get_user_from_token(token)`: Validates JWT and returns user object
- `get_user_role(user_id)`: Fetches user role from `user_roles` table
- `is_admin(user_id)`: Checks if user is admin

**Usage Pattern**:
```python
@app.route('/api/protected')
@require_auth
def protected_route():
    user = g.user  # Current user object
    user_id = g.user_id  # User ID string
    is_admin = g.is_admin  # Boolean
    return jsonify({'user': user_id})
```

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

**Format Compatibility** (v2.1):
- Old format: `keywords: []` (plain array)
- Current format: `keywords: {zh: [], en: [], ja: [], ko: []}` (multilang dict with Korean)
- Auto-translation: When creating topics without AI, system auto-translates ZH → EN/JA/KO
- Code handles both formats with `normalize_keywords()` function

## AI Integration

### Gemini (Keywords + Translation)
- **Model**: `gemini-2.0-flash`
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`
- **Keyword Generation**: 10-15 ZH keywords, 8-10 EN/JA/KO keywords per topic (supports 4 languages)
- **Translation**: Multi-target support (zh-TW, en, ja, ko) with single prompt
- **Auto-Translation** (v2.1): One API call for all 3 languages (EN/JA/KO) instead of 3 separate calls
- **Rate Limiting**: 0.5s delay between translations, 3 retries with exponential backoff for 429 errors

### Perplexity (Summaries)
- **Model**: `sonar` (configurable via `PERPLEXITY_MODEL`)
- **Endpoint**: `https://api.perplexity.ai/chat/completions`
- **Prompt Style**: "Progress report" for colleagues familiar with the topic (NOT introductory explainers)
- **System Prompt**: "你是一位資深專題記者，正在為已經熟悉議題背景的同事更新最新進展" (app.py:252-315)
- **Schedule**: 08:00 and 18:00 daily (Taipei time)
- **Post-processing**: Removes markdown symbols ([1], [2], **, *, #) from output (app.py:302-309)

## Deployment (Render.com)

**URL**: https://topicradar.onrender.com
**Custom Domain**: https://topicradar.bonnews.net

**Files**:
- `requirements.txt`: Python dependencies
- `render.yaml`: Render configuration (1 worker, 2 threads)
- `.gitignore`: Excludes .env, venv, __pycache__

**Start Command**:
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2
```

**Environment**: Set API keys via Render dashboard (Secret Files or Environment Variables). `TZ=Asia/Taipei` is defined in `render.yaml`.

**Cold Start**: Render free tier sleeps after 15min idle, ~30s cold start. Scheduler resumes automatically.

**Deployment Workflow**:
```bash
# 1. Test locally
source venv/bin/activate
python3 app.py

# 2. Commit and push
git add .
git commit -m "feat: description"
git push origin main

# 3. Render auto-deploys from GitHub main branch
# 4. Monitor deployment in Render dashboard
```

## Important Implementation Details

- **No Persistent News Storage**: All news data is in-memory (`DATA_STORE`). Only `topics_config.json` persists locally. Supabase stores user data only.
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

### Test Authentication
```bash
# Test Supabase connection
python3 scripts/test/test_supabase.py

# Verify cache file
python3 scripts/test/verify_cache.py
```

### Manual API Test
```bash
# Trigger news update
curl -X POST http://localhost:5001/api/refresh

# View all data
curl http://localhost:5001/api/all | python3 -m json.tool | head -50

# View topics config (requires auth)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:5001/api/admin/topics | python3 -m json.tool
```

### Check Scheduler Status
Monitor console output for:
- `[UPDATE] 開始更新新聞 - HH:MM:SS` (every 30min)
- `[SUMMARY] 開始 AI 摘要...` (08:00, 18:00)
- `[SEARCH] {topic}: 只有 N 則，使用 Google News 搜索補充...` (fallback triggered)

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

**Authentication Errors**:
- Verify `SUPABASE_URL` and `SUPABASE_KEY` in .env
- Check JWT token is passed as `Authorization: Bearer <token>` header
- Use scripts/setup/setup_admin.py to create admin user

**Cache File Issues**:
- Run `python3 scripts/test/verify_cache.py` to check integrity
- Delete `data_cache.json` to force regeneration
- Check Render disk space (free tier has limits)

## Documentation

Detailed documentation in `docs/`:
- `ARCHITECTURE.md`: System architecture diagram and component explanation
- `AUTH_DEPLOYMENT_GUIDE.md`: Authentication system deployment guide
- `USER_AUTH_PLAN.md`: Authentication implementation plan
- `guides/`: Step-by-step setup guides
- `reports/`: Implementation reports and analysis
- `sql/`: Database schema and migrations
