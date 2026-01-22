# 設定管理員帳號指南

由於 Supabase 預設需要 Email 驗證，請依照以下步驟在 Supabase Dashboard 直接建立管理員帳號。

## 方法 1: 在 Supabase Dashboard 建立帳號（推薦）

### 步驟 1: 建立使用者

1. 前往 [Supabase Dashboard](https://app.supabase.com)
2. 選擇您的專案
3. 點擊左側選單 **Authentication** > **Users**
4. 點擊右上角 **Add user** > **Create new user**
5. 填寫資料：
   - **Email**: `Chen-Yu@nightpluie.com`
   - **Password**: `CY80664001`
   - ✅ 勾選 **Auto Confirm User** (自動確認，跳過 Email 驗證)
6. 點擊 **Create user**

### 步驟 2: 複製 User ID

1. 在 Users 列表中找到剛建立的帳號
2. 點擊該帳號進入詳細資訊
3. 複製 **UID**（UUID 格式，例如：`abc123-def456-...`）

### 步驟 3: 設定為管理員

1. 點擊左側選單 **SQL Editor**
2. 點擊 **New Query**
3. 執行以下 SQL（記得替換 User ID）：

```sql
-- 設定為管理員
INSERT INTO user_roles (user_id, role)
VALUES ('貼上您複製的UID', 'admin')
ON CONFLICT (user_id) DO UPDATE SET role = 'admin';
```

4. 點擊 **Run**

### 步驟 4: 標記邀請碼為已使用（可選）

```sql
-- 將 WELCOME2026 標記為已使用
UPDATE invite_codes
SET used_by = '貼上您複製的UID',
    used_at = NOW()
WHERE code = 'WELCOME2026';
```

---

## 方法 2: 關閉 Email 驗證（更簡單）

如果您希望直接從前端註冊，可以關閉 Email 驗證：

### 步驟 1: 關閉 Email 確認

1. 前往 Supabase Dashboard
2. 點擊 **Authentication** > **Settings**
3. 在 **Email Auth** 區塊中
4. **取消勾選** "Enable email confirmations"
5. 點擊 **Save**

### 步驟 2: 前往網站註冊

1. 訪問 `http://localhost:5001/login`
2. 切換到「註冊」分頁
3. 填寫資料：
   - Email: `Chen-Yu@nightpluie.com`
   - 密碼: `CY80664001`
   - 邀請碼: `WELCOME2026`
4. 點擊註冊

### 步驟 3: 設定為管理員

註冊成功後，仍需在 Supabase SQL Editor 執行：

```sql
-- 先找出您的 User ID
SELECT id, email FROM auth.users WHERE email = 'Chen-Yu@nightpluie.com';

-- 設定為管理員（替換 User ID）
INSERT INTO user_roles (user_id, role)
VALUES ('貼上查詢到的UID', 'admin')
ON CONFLICT (user_id) DO UPDATE SET role = 'admin';
```

---

## 驗證是否成功

設定完成後：

1. 前往 `http://localhost:5001/login`
2. 使用 `Chen-Yu@nightpluie.com` / `CY80664001` 登入
3. 應該會看到：
   - ✅ 右上角顯示 "👤 Chen-Yu@nightpluie.com (管理員)"
   - ✅ 頁面下方出現 "⚙️ 管理員專區"
   - ✅ 可以看到原本的 6 個專題

---

## 故障排除

### 問題 1: 登入時顯示 "Email not confirmed"

**解決方法：**
- 使用方法 1 在 Dashboard 建立帳號時勾選 "Auto Confirm User"
- 或使用方法 2 關閉 Email 驗證

### 問題 2: 登入成功但看不到管理員專區

**解決方法：**
- 確認在 SQL Editor 執行了設定管理員的 SQL
- 登出後重新登入
- 檢查 SQL：
  ```sql
  SELECT * FROM user_roles WHERE user_id = (
    SELECT id FROM auth.users WHERE email = 'Chen-Yu@nightpluie.com'
  );
  ```
  應該返回 `role: 'admin'`

### 問題 3: RLS policy 錯誤

**解決方法：**
- 在 Supabase Dashboard 直接操作，不要透過前端 API
- 確認 `docs/supabase_migration.sql` 的 RLS policies 都已正確執行
