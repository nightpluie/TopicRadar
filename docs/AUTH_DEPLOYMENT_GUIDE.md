# TopicRadar 認證系統部署與測試指南

## ✅ 已完成實作項目

### 後端 (100%)
- ✅ auth.py 認證模組 (332 行)
  - 使用者註冊/登入/登出
  - Token 驗證
  - 邀請碼管理
  - 使用者角色管理
  - 專題 CRUD 操作
- ✅ app.py API 路由整合
  - 認證 API (註冊、登入、登出、使用者資訊)
  - 專題管理 API 加上認證保護
  - 管理員 API (邀請碼、使用者管理)
- ✅ requirements.txt 更新 (包含 supabase 套件)

### 前端 (100%)
- ✅ login.html 登入頁面 (469 行)
  - 登入/註冊表單切換
  - 邀請碼驗證
  - Token 儲存
  - 自動導向
- ✅ admin.html 認證整合
  - 登入狀態檢查
  - 登出按鈕
  - API 請求加入 Authorization header
  - 管理員專區 (邀請碼管理、使用者管理)

### 資料庫設計 (100%)
- ✅ docs/supabase_migration.sql
  - user_topics 資料表
  - invite_codes 資料表
  - user_roles 資料表
  - RLS 安全策略

---

## 📋 部署步驟

### 步驟 1: Supabase 資料庫設置

#### 1.1 執行資料庫遷移

1. 前往 [Supabase Dashboard](https://app.supabase.com)
2. 選擇您的專案 (已連線到 `uukpoxhbfanxwqgaitac.supabase.co`)
3. 點擊左側選單的 **SQL Editor**
4. 點擊 **New Query**
5. 複製 `docs/supabase_migration.sql` 的完整內容並貼上
6. 點擊 **Run** 執行

#### 1.2 建立第一個管理員帳號

**方法一：使用 SQL 手動建立 (推薦)**

```sql
-- 1. 先在 Supabase Auth 註冊一個測試帳號
-- 前往 Authentication > Users > Invite User
-- 或直接使用登入頁面註冊 (需要邀請碼，見下方)

-- 2. 建立初始邀請碼 (如果還沒有的話)
INSERT INTO invite_codes (code, created_by, expires_at)
VALUES ('ADMIN2026', NULL, NOW() + INTERVAL '30 days');

-- 3. 使用邀請碼註冊後，取得 user_id
-- 前往 Authentication > Users，複製您帳號的 UID

-- 4. 設定為管理員
INSERT INTO user_roles (user_id, role)
VALUES ('您的_USER_ID_在這裡', 'admin')
ON CONFLICT (user_id) DO UPDATE SET role = 'admin';
```

**方法二：使用前端流程**

1. 先在 SQL Editor 建立初始邀請碼：
   ```sql
   INSERT INTO invite_codes (code, expires_at)
   VALUES ('WELCOME2026', NOW() + INTERVAL '30 days');
   ```

2. 前往 `http://localhost:5001/login`
3. 使用邀請碼 `WELCOME2026` 註冊第一個帳號
4. 在 Supabase Dashboard 取得該使用者的 UID
5. 執行 SQL 設定為管理員 (見上方)

---

### 步驟 2: 本地測試

#### 2.1 啟動伺服器

```bash
cd ~/Desktop/TopicRadar
source venv/bin/activate
python3 app.py
```

伺服器將在 `http://localhost:5001` 啟動

#### 2.2 測試認證系統狀態

```bash
curl http://localhost:5001/api/auth/status | python3 -m json.tool
```

預期輸出：
```json
{
  "enabled": true,
  "supabase_configured": true
}
```

---

## 🧪 測試清單

### 測試 1: 使用者註冊

1. 開啟 `http://localhost:5001/login`
2. 切換到「註冊」分頁
3. 輸入測試 Email (例如：test@example.com)
4. 輸入密碼 (至少 6 個字元)
5. 輸入邀請碼 (例如：`WELCOME2026`)
6. 點擊「註冊」

**預期結果：**
- ✅ 顯示「註冊成功！」訊息
- ✅ 1 秒後自動導向 `/admin` 頁面
- ✅ 在 admin 頁面右上角顯示使用者 Email

### 測試 2: 使用者登入/登出

1. 在 admin 頁面點擊「登出」按鈕
2. 導回登入頁面
3. 輸入剛才註冊的 Email 和密碼
4. 點擊「登入」

**預期結果：**
- ✅ 登入成功，導向 admin 頁面
- ✅ 可以看到自己的專題列表
- ✅ 登出後無法直接訪問 `/admin` (會自動導向登入頁)

### 測試 3: 專題隔離

1. 用帳號 A 登入，建立專題「測試專題 A」
2. 登出
3. 用帳號 B 登入

**預期結果：**
- ✅ 帳號 B 看不到「測試專題 A」
- ✅ 每個使用者只能看到自己建立的專題

**注意：** 目前系統仍使用 `topics_config.json`，所有使用者共享專題。若要實現真正的專題隔離，需要將專題資料遷移到 Supabase `user_topics` 資料表。

### 測試 4: 管理員功能

#### 4.1 邀請碼管理

1. 用管理員帳號登入
2. 在 admin 頁面應該看到「⚙️ 管理員專區」
3. 點擊「生成新邀請碼」按鈕
4. 查看邀請碼列表

**預期結果：**
- ✅ 成功生成新邀請碼
- ✅ 邀請碼顯示為「未使用」狀態
- ✅ 可以刪除未使用的邀請碼

#### 4.2 使用者管理

1. 在管理員專區查看「使用者管理」區塊
2. 應該看到所有註冊使用者的列表
3. 嘗試將一般使用者提升為管理員

**預期結果：**
- ✅ 顯示所有使用者及其角色
- ✅ 可以切換使用者角色（一般使用者 ↔ 管理員）
- ✅ 顯示每個使用者的專題數和註冊日期

### 測試 5: API 認證保護

```bash
# 未登入時訪問專題 API (應該被拒絕)
curl -X GET http://localhost:5001/api/admin/topics

# 使用 token 訪問 (應該成功)
TOKEN="your_token_here"  # 從 localStorage 取得
curl -X GET http://localhost:5001/api/admin/topics \
  -H "Authorization: Bearer $TOKEN"
```

**預期結果：**
- ✅ 未提供 token 時返回 401 Unauthorized
- ✅ 提供有效 token 時返回專題列表
- ✅ Token 失效時返回 401

---

## 🚀 部署到 Render

### 步驟 1: 更新環境變數

在 Render Dashboard 設定以下環境變數：

```
SUPABASE_URL=https://uukpoxhbfanxwqgaitac.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 步驟 2: 推送程式碼

```bash
git add .
git commit -m "feat: 新增使用者認證系統

- 整合 Supabase 認證
- 新增登入/註冊頁面
- 專題管理 API 加上認證保護
- 管理員功能 (邀請碼管理、使用者管理)

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"

git push origin main
```

### 步驟 3: 驗證部署

1. 等待 Render 自動部署完成 (約 2-3 分鐘)
2. 前往 `https://topicradar.bonnews.net/login`
3. 測試登入/註冊功能

---

## 🔧 故障排除

### 問題 1: 無法連接到 Supabase

**症狀：**
- `/api/auth/status` 返回 `enabled: false`
- 登入時顯示「認證系統未啟用」

**解決方法：**
1. 檢查 `.env` 檔案是否包含 `SUPABASE_URL` 和 `SUPABASE_KEY`
2. 確認環境變數值正確無誤
3. 重啟伺服器

### 問題 2: 註冊時提示「邀請碼無效」

**症狀：**
- 輸入邀請碼後仍無法註冊

**解決方法：**
1. 在 Supabase Dashboard 檢查 `invite_codes` 資料表
2. 確認邀請碼未被使用且未過期
3. 手動建立新邀請碼 (見上方 SQL)

### 問題 3: 登入後無法看到管理員專區

**症狀：**
- 已登入但看不到「管理員專區」

**解決方法：**
1. 檢查 `user_roles` 資料表，確認該使用者的 role 為 `admin`
2. 清除瀏覽器 localStorage 並重新登入
3. 執行 SQL：
   ```sql
   UPDATE user_roles SET role = 'admin' WHERE user_id = '您的_USER_ID';
   ```

### 問題 4: Token 驗證失敗

**症狀：**
- 頁面不斷重新導向到登入頁
- Console 顯示 401 錯誤

**解決方法：**
1. 清除瀏覽器 localStorage：
   ```javascript
   localStorage.clear();
   ```
2. 重新登入取得新 token
3. 檢查 Supabase 專案是否暫停 (免費版 7 天不活躍會暫停)

---

## 📊 系統架構說明

### 認證流程

```
使用者 → login.html → POST /api/auth/login → Supabase Auth
                                              ↓
                                         驗證成功
                                              ↓
                        localStorage.setItem('auth_token', token)
                                              ↓
                                      導向 /admin
                                              ↓
                             checkAuth() 驗證 token
                                              ↓
                                    GET /api/auth/me
                                              ↓
                                      載入專題資料
```

### 資料隔離（未來實作）

目前系統使用 `topics_config.json` 儲存專題，所有使用者共享。若要實現真正的專題隔離，需要：

1. 修改 `get_topics()` 從 Supabase 讀取 `user_topics`
2. 修改 `add_topic()` 關聯到當前使用者
3. 修改 `update_topic()` 驗證擁有者
4. 修改 `delete_topic()` 驗證擁有者

這需要額外的後端修改，建議作為 Phase 2 實作。

---

## ✨ 功能總結

### 已實作功能

✅ 使用者註冊（需邀請碼）
✅ 使用者登入/登出
✅ Token 認證
✅ 專題管理 API 認證保護
✅ 管理員邀請碼管理
✅ 管理員使用者管理
✅ 角色權限控制 (admin / user)

### 未來擴展功能

- [ ] Google OAuth 登入
- [ ] Email 驗證
- [ ] 密碼重設
- [ ] 專題資料遷移到 Supabase (真正的使用者隔離)
- [ ] 專題分享功能
- [ ] Email 通知

---

## 📝 相關檔案

- `auth.py` - 認證模組核心邏輯
- `app.py` - API 路由整合
- `login.html` - 登入/註冊頁面
- `admin.html` - 後台管理介面
- `docs/supabase_migration.sql` - 資料庫遷移腳本
- `docs/USER_AUTH_PLAN.md` - 原始設計文件

---

**實作完成日期：** 2026-01-20
**完成度：** 95% (核心功能已完成，待測試驗證)
