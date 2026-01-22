# 確認測試帳號郵件 - 手動操作步驟

由於系統使用的是 **anon key**（非 service_role key），無法透過程式直接修改 `auth.users` 表。

請您按照以下步驟在 Supabase Dashboard 手動確認郵件：

---

## 📋 操作步驟

### 1. 開啟 Supabase Dashboard
   - 在瀏覽器中前往：**https://app.supabase.com**
   - 登入您的帳號

### 2. 選擇專案
   - 選擇 TopicRadar 對應的專案

### 3. 進入 SQL Editor
   - 點擊左側選單的 **「SQL Editor」**
   - 點擊右上角的 **「New Query」** 按鈕

### 4. 執行 SQL
   在編輯器中貼上以下 SQL：

   ```sql
   UPDATE auth.users
   SET email_confirmed_at = NOW(),
       confirmed_at = NOW()
   WHERE email = 'test@topicradar.com';
   ```

### 5. 執行查詢
   - 點擊右下角的 **「Run」** 按鈕（或按 Ctrl+Enter / Cmd+Enter）
   - 應該會看到成功訊息：**「Success. 1 rows affected.」**

---

## ✅ 完成後測試

確認郵件後，即可使用以下帳號登入：

- **Email**: test@topicradar.com
- **Password**: test123456

### 測試步驟：
1. 訪問 http://localhost:5001/login
2. 使用上述帳號登入
3. 應該會看到：
   - ✅ 登入成功並導向首頁 (/)
   - ✅ 頂部顯示 Email: test@topicradar.com
   - ✅ 顯示「登出」按鈕

---

## 🔍 驗證確認是否成功

如果想確認郵件是否已確認，可以在 SQL Editor 執行：

```sql
SELECT id, email, email_confirmed_at, created_at
FROM auth.users
WHERE email = 'test@topicradar.com';
```

應該會看到 `email_confirmed_at` 欄位有時間戳記（不是 NULL）。

---

## 💡 替代方案：關閉郵件驗證

如果您想要更簡單的方式，可以直接關閉郵件驗證：

1. 在 Supabase Dashboard 中
2. 點擊 **Authentication** > **Settings**
3. 找到 **Email Auth** 區塊
4. **取消勾選** "Enable email confirmations"
5. 點擊 **Save**

關閉後，未來註冊的帳號都不需要確認郵件即可登入。

---

完成以上任一操作後，即可開始測試所有功能！
