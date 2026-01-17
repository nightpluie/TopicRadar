# TopicRadar 使用者認證系統實作計畫

為 TopicRadar 增加使用者登入功能，讓不同使用者可以自行管理個人追蹤的專題頁面。

## 技術方案決策

### 為什麼選擇 Supabase？

| 方案 | 優點 | 缺點 |
|------|------|------|
| **Supabase（推薦）** | 免費版夠用、內建 Auth、有 Python SDK | 外部依賴、免費版 7 天不活躍會暫停 |
| Render PostgreSQL | 與現有部署整合 | 需自己實作認證邏輯、免費版限制多 |

**Supabase 免費版限制**（對你的使用情境完全足夠）：
- ✅ **50,000 月活躍使用者 (MAU)** — 遠超過你的需求
- ✅ **500 MB 資料庫** — 存使用者和專題設定綽綽有餘
- ✅ **無限 API 請求**
- ⚠️ **7 天不活躍會暫停** — 只要有人使用就不會發生

---

## 資料庫設計

### 資料表結構

```sql
-- Supabase Auth 會自動處理 users 表，我們只需要建立專題相關的表

-- 使用者的專題設定
CREATE TABLE user_topics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(10) DEFAULT '📌',
    keywords JSONB NOT NULL,          -- 支援 {zh: [], en: [], ja: []} 格式
    negative_keywords JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS（行級安全策略）確保使用者只能存取自己的資料
ALTER TABLE user_topics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own topics"
    ON user_topics FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own topics"
    ON user_topics FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own topics"
    ON user_topics FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own topics"
    ON user_topics FOR DELETE
    USING (auth.uid() = user_id);
```

### 資料遷移策略

現有的 `topics_config.json` 中的專題將作為「範本專題」：
- 新使用者註冊時，可選擇訂閱預設範本
- 或直接複製範本到自己的帳號下

---

## 實作步驟

### Phase 1: Supabase 設置

#### 1.1 建立 Supabase 專案
1. 前往 [supabase.com](https://supabase.com) 註冊/登入
2. 建立新專案，區域選 **Northeast Asia (Tokyo)** 或 **Singapore**
3. 記錄以下資訊：
   - Project URL: `https://xxxxx.supabase.co`
   - anon/public key
   - service_role key（後端用）

#### 1.2 執行資料庫遷移
在 Supabase Dashboard > SQL Editor 執行上述 SQL

---

### Phase 2: 後端整合

#### 2.1 新增依賴

修改 [requirements.txt](file:///Users/nightpluie/Desktop/TopicRadar/requirements.txt)：

```diff
  flask
  gunicorn
  feedparser
  requests
  anthropic
  google-generativeai
+ supabase
```

#### 2.2 新增認證相關程式碼

##### [NEW] auth.py
建立新檔案處理 Supabase 認證邏輯：
- `signup(email, password)` - 註冊
- `login(email, password)` - 登入
- `logout()` - 登出
- `get_current_user()` - 從 session 取得當前使用者
- `require_auth` decorator - 保護需要登入的 API

##### [MODIFY] [app.py](file:///Users/nightpluie/Desktop/TopicRadar/app.py)
- 新增環境變數讀取 `SUPABASE_URL` 和 `SUPABASE_KEY`
- 新增路由：
  - `POST /api/auth/signup` - 註冊
  - `POST /api/auth/login` - 登入
  - `POST /api/auth/logout` - 登出
  - `GET /api/auth/me` - 取得當前使用者資訊
- 修改現有 API：
  - `GET /api/topics` - 改為讀取當前使用者的專題
  - `POST /api/topics/add` - 關聯到當前使用者
  - `PUT /api/topics/<tid>` - 驗證是否為擁有者
  - `DELETE /api/topics/<tid>` - 驗證是否為擁有者

---

### Phase 3: 前端整合

##### [NEW] login.html
登入/註冊頁面，包含：
- Email 輸入欄位
- 密碼輸入欄位  
- 登入/註冊切換按鈕
- 錯誤訊息顯示區

##### [MODIFY] [admin.html](file:///Users/nightpluie/Desktop/TopicRadar/admin.html)
- 新增導覽列顯示使用者狀態
- 新增登出按鈕
- 未登入時導向登入頁面

##### [MODIFY] [script.js](file:///Users/nightpluie/Desktop/TopicRadar/script.js)
- 新增登入狀態檢查
- API 請求加入認證 token

---

### Phase 4: 部署設定

##### [MODIFY] [render.yaml](file:///Users/nightpluie/Desktop/TopicRadar/render.yaml)

```yaml
services:
  - type: web
    name: topic-radar
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2
    envVars:
      - key: PERPLEXITY_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: TZ
        value: Asia/Taipei
      # 新增 Supabase 設定
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: FLASK_SECRET_KEY
        generateValue: true
```

---

## 驗證計畫

### 自動化測試

由於專案目前沒有測試框架，建議手動驗證為主。

### 手動驗證步驟

#### 測試 1: 使用者註冊
1. 開啟 `http://localhost:5001/login.html`
2. 輸入測試 email 和密碼
3. 點擊「註冊」按鈕
4. **預期結果**：顯示成功訊息，並自動導向 admin 頁面

#### 測試 2: 使用者登入/登出
1. 登出後重新登入
2. 驗證登入後可看到自己的專題列表
3. 點擊登出按鈕
4. **預期結果**：回到登入頁面，無法存取 admin

#### 測試 3: 專題隔離
1. 用帳號 A 建立專題「測試專題 A」
2. 登出，用帳號 B 登入
3. **預期結果**：帳號 B 看不到「測試專題 A」

#### 測試 4: CRUD 操作
1. 新增專題、編輯專題、刪除專題
2. 重新整理頁面
3. **預期結果**：資料持久化，刷新後仍存在

---

## 時程估計

| 階段 | 預估時間 |
|------|----------|
| Supabase 設置 + 資料庫建立 | 30 分鐘 |
| 後端認證整合 | 2-3 小時 |
| 前端登入頁面 | 1-2 小時 |
| 修改現有 API | 1-2 小時 |
| 測試與除錯 | 1 小時 |
| **總計** | **約 6-8 小時** |

---

## 使用者需決策事項

> [!IMPORTANT]
> 請確認以下問題：

1. **現有專題處理方式**：
   - A. 作為「範本」讓新使用者選擇訂閱
   - B. 遷移到你的管理員帳號下
   - C. 全部刪除，從零開始

2. **是否需要管理員功能**？
   - 例如：管理員可以看到所有人的專題、管理公共範本等

3. **是否要開放註冊**？
   - A. 任何人都可以註冊
   - B. 僅限邀請碼註冊
   - C. 僅允許特定 email domain

---

## 後續可擴展功能

- [ ] Google OAuth 登入（Supabase 內建支援）
- [ ] 專題分享（分享連結給其他使用者）
- [ ] 專題範本市集
- [ ] Email 通知（有新新聞時發信）
