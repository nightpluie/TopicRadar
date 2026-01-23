# Code Review Report

Scope: `app.py`, `admin.html`  
Focus: Turbo button logic, database interactions, security, performance, code style.

## Findings (highest severity first)

### Critical
- **`supabase` is never initialized, so DB calls will raise `NameError` at runtime.**  
  This breaks archiving and all Turbo analysis endpoints in authenticated mode.  
  References: `app.py:970`, `app.py:3075`, `app.py:3140`, `app.py:3188`, `app.py:3213`, `app.py:3252`, `app.py:3298`

- **Missing import for `timedelta` crashes Turbo/analysis endpoints.**  
  `timedelta` is used but never imported, causing immediate `NameError`.  
  References: `app.py:3073`, `app.py:3138`, `app.py:3186`, `app.py:3257`

- **Turbo analysis worker references `news_data` without defining it.**  
  `_run_angle_analysis_task` assigns `news_response` but then checks/uses `news_data`, so analysis always fails.  
  References: `app.py:3188`, `app.py:3197`, `app.py:3210`, `app.py:3217`

### High
- **Turbo “ready” gating is client‑only and trivially bypassed.**  
  The button always calls `turboAnalyze`, and the backend doesn’t enforce a minimum archive count. Users can trigger analysis without the intended data threshold.  
  References: `admin.html:1056`, `admin.html:1709`, `app.py:3239`

- **TLS verification is disabled for RSS/Google News requests.**  
  `verify=False` enables MITM/data‑tampering risks.  
  References: `app.py:711`, `app.py:807`, `app.py:863`

### Medium
- **Turbo status fetch ignores `API_BASE`, leading to mixed‑origin behavior.**  
  If `API_BASE` is set (reverse proxy, subpath), archive‑count calls go to the wrong origin.  
  References: `admin.html:1670`

- **Turbo status fetch doesn’t check `response.ok`.**  
  On 401/500, it still parses JSON and computes `NaN%` water levels, causing misleading UI states.  
  References: `admin.html:1670`

- **Turbo status update can race topic rendering.**  
  `setTimeout(updateTurboButtons, 1000)` may fire before `loadTopics()` finishes, leaving buttons stale until the 2‑hour interval.  
  References: `admin.html:1438`, `admin.html:1837`

- **Potential XSS via `innerHTML` with user‑controlled or AI content.**  
  Topic names/keywords and AI analysis output are injected without sanitization.  
  References: `admin.html:1030`, `admin.html:1719`, `admin.html:1788`

### Low
- **`LOADING_STATUS` is overwritten immediately in `update_domestic_news`.**  
  The first assignment (`phase: 'domestic'`) is replaced by `phase: 'news'`, obscuring intent.  
  References: `app.py:1744`, `app.py:1751`

## Open Questions / Assumptions
- I assumed `supabase` should be initialized via `auth.get_supabase()` or similar; no such initialization exists in `app.py`.
- Is the legacy `/api/topics/<topic_id>/discover-angles` endpoint still intended to be used alongside the newer Turbo endpoints?
