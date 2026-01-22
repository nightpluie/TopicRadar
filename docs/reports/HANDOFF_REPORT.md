# TopicRadar 專題隔離功能開發 - 交接報告

**日期**: 2026-01-20
**任務**: 實作使用者專題隔離功能（移除共享專題，每個使用者獨立專題）

## 已完成的工作

### 1. 登入流程修改 ✅
- **檔案**: `login.html`
- **修改內容**:
  - 登入後導向改為前台 (`/`) 而非後台 (`/admin`)
  - 已登入使用者訪問登入頁時自動導向前台
  - 新增「記住帳號」功能，使用 localStorage 儲存 email

### 2. 後端 API 專題隔離 ✅
- **檔案**: `app.py`
- **修改內容**:
  - `/api/all` (lines 1234-1331): 認證模式下從 Supabase 讀取該使用者的專題
  - `/api/admin/topics` GET (lines 1375-1448): 返回使用者專屬專題列表
  - `/api/admin/topics` POST (lines 1450-1531): 建立專題時關聯 user_id
  - `/api/admin/topics/<tid>` PUT (lines 1533-1582): 更新前驗證擁有者
  - `/api/admin/topics/<tid>` DELETE (lines 1584-1615): 刪除前驗證擁有者
  - `/api/loading-status` (lines 1359-1373): 使用者專屬的載入狀態

### 3. 前端認證整合 ✅
- **檔案**: `script.js`
- **修改內容**:
  - `getAuthToken()` (line 235-237): 從 localStorage 讀取 auth_token
  - `loadAllData()` (lines 240-259): 帶入 Authorization header
  - `checkLoadingStatus()` (lines 384-410): 帶入 Authorization header
  - 未登入時自動導向 `/login` (line 255)

### 4. 新聞更新邏輯改造 ✅
- **檔案**: `app.py`
- **修改內容**:
  - `update_topic_news()` (lines 727-950): 認證模式下從 Supabase 讀取所有使用者專題
  - `update_domestic_news()` (lines 960-1064): 同上
  - `update_international_news()` (lines 1066-1203): 同上
  - `update_all_summaries()` (lines 1205-1231): 同上

**實作邏輯**:
```python
if AUTH_ENABLED:
    # 從 Supabase 讀取所有使用者的專題
    all_user_topics = auth.get_all_topics_admin()
    # 轉換為內部格式
    topics_to_update = {topic['id']: {...} for topic in all_user_topics}
else:
    # 使用本地 topics_config.json
    topics_to_update = TOPICS
```

### 5. 認證系統狀態 ✅
- **環境變數**: Supabase 已設定（SUPABASE_URL, SUPABASE_KEY）
- **AUTH_ENABLED**: True（app.py line 1643）
- **auth.py**: 完整的認證邏輯已實作
- **Supabase 資料表**: user_topics, invite_codes, user_roles

## 系統架構說明

### 資料流程（認證模式）

```
使用者登入 → localStorage 儲存 token
     ↓
前台訪問 /api/all 帶入 Bearer token
     ↓
後端驗證 token → 從 Supabase 讀取 user_topics
     ↓
返回該使用者的專題 + 新聞資料
```

### 新聞更新流程（認證模式）

```
定時排程觸發更新
     ↓
auth.get_all_topics_admin() → 讀取所有使用者專題
     ↓
抓取 RSS 新聞 → 針對每個專題過濾
     ↓
儲存到 DATA_STORE[tid] → 寫入 data_cache.json
     ↓
使用者訪問時從 DATA_STORE 讀取對應專題新聞
```

**重要**:
- 新聞資料是「共享快取」：所有使用者的專題新聞存在同一個 DATA_STORE
- 使用者隔離靠「專題 ID」實現：每個使用者的專題有獨立的 UUID
- 即使兩個使用者追蹤相同主題，也會建立不同專題（不同 ID）

## 測試狀態

### 伺服器狀態
- **執行中**: Yes (http://127.0.0.1:5001)
- **認證系統**: Enabled
- **背景任務**: Running (task ID: b440f61)

### 已測試項目
- ✅ 伺服器成功啟動
- ✅ 認證系統啟用確認 (`/api/auth/status` 返回 enabled: true)
- ⏳ 背景新聞更新進行中

### 待測試項目
1. 使用者登入並建立專題
2. 驗證專題只顯示給建立者
3. 測試新聞更新是否正確抓取使用者專題的新聞
4. 測試不同使用者建立相同名稱專題時的隔離性
5. 測試專題 CRUD 操作的擁有者驗證

## 已知問題和注意事項

### 1. 快取資料與使用者隔離
- **data_cache.json** 儲存所有使用者的新聞資料
- 專題 ID 是 UUID (Supabase 自動生成)，確保唯一性
- 舊的 topics_config.json 仍存在但在認證模式下不再使用

### 2. 登出功能缺失
- **index.html** 目前沒有登出按鈕
- 建議：在頂部狀態列加入「使用者資訊 + 登出」按鈕

### 3. 背景更新輸出
- 背景新聞更新線程似乎沒有輸出日誌
- 可能需要調查 stdout flush 問題或線程阻塞

### 4. 前台未要求登入
- **index.html** 目前只在 `/api/all` 返回 401 時才導向登入
- 建議：頁面載入時主動檢查登入狀態

## 建議後續工作

### 高優先級
1. **新增登出功能**
   - 修改 index.html 加入登出按鈕
   - 清除 localStorage 的 auth_token
   - 導向登入頁

2. **測試完整流程**
   - 建立第二個測試帳號
   - 驗證專題隔離是否正常運作
   - 測試新聞更新是否包含所有使用者專題

3. **前台登入檢查**
   - index.html 載入時檢查 token 有效性
   - 無效或不存在時直接導向登入頁

### 中優先級
4. **優化快取機制**
   - 考慮是否需要分開儲存每個使用者的新聞快取
   - 目前設計下，刪除專題時 data_cache.json 中的資料不會自動清理

5. **錯誤處理增強**
   - Supabase 連線失敗時的降級機制
   - 更友善的前端錯誤訊息

6. **效能優化**
   - 大量使用者時，auth.get_all_topics_admin() 可能成為瓶頸
   - 考慮加入快取層

### 低優先級
7. **使用者體驗**
   - 顯示當前登入使用者名稱
   - 專題列表顯示建立時間
   - 支援專題分享（可選功能）

8. **文件更新**
   - 更新 CLAUDE.md 說明認證架構
   - 建立使用者操作手冊

## 程式碼檔案清單

### 已修改檔案
- `app.py` - 新增認證邏輯、專題隔離、新聞更新改造
- `login.html` - 登入導向修改、記住帳號功能
- `script.js` - Authorization header 整合

### 未修改但相關的檔案
- `auth.py` - 認證核心邏輯（已由其他 AI 完成）
- `index.html` - 前台頁面（待加入登出功能）
- `admin.html` - 後台管理頁面（已支援使用者專題管理）

### 設定檔案
- `.env` - Supabase 認證資訊
- `topics_config.json` - 舊版專題設定（認證模式下不使用）
- `data_cache.json` - 新聞快取（包含所有使用者專題）

## 技術細節

### Supabase 資料表結構

**user_topics**
```sql
id UUID PRIMARY KEY
user_id UUID REFERENCES auth.users(id)
name VARCHAR(100)
keywords JSONB  -- {zh: [...], en: [...], ja: [...]}
negative_keywords JSONB
icon VARCHAR(10)
order INTEGER
created_at TIMESTAMPTZ
```

**invite_codes**
```sql
id UUID PRIMARY KEY
code VARCHAR(20) UNIQUE
created_by UUID
used_by UUID
used_at TIMESTAMPTZ
expires_at TIMESTAMPTZ
```

**user_roles**
```sql
id UUID PRIMARY KEY
user_id UUID REFERENCES auth.users(id)
role VARCHAR(20)  -- 'admin' or 'user'
created_at TIMESTAMPTZ
```

### 環境變數需求
```ini
# Supabase（必須）
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGc...

# AI API Keys
PERPLEXITY_API_KEY=pplx-...
GEMINI_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-...  # 可選，用於 update_keywords.py

# Server
TZ=Asia/Taipei
```

## 交接建議

1. **先測試基本功能**：登入 → 建立專題 → 檢查新聞更新
2. **檢查背景更新**：確認新聞定時更新是否正常運作
3. **加入登出功能**：讓使用者可以切換帳號測試隔離性
4. **壓力測試**：建立多個使用者和專題，確認效能

## 聯絡資訊

如有問題或需要進一步說明，請參考：
- 程式碼註解
- auth.py 的函數文件字串
- Supabase Dashboard 的 RLS 政策設定

---

**報告產生時間**: 2026-01-20 22:06
**伺服器狀態**: Running on http://127.0.0.1:5001
**認證系統**: Enabled
**背景任務**: b440f61 (監控中)
