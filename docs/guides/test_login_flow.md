# 登入流程測試指南

## 測試帳號狀態

目前系統中的帳號：

1. **管理員帳號** (可能未建立或需要重設)
   - Email: Chen-Yu@nightpluie.com
   - Password: CY80664001
   - 狀態: ❌ 登入失敗

2. **測試帳號** (已註冊但未確認)
   - Email: test@topicradar.com
   - Password: test123456
   - 狀態: ⚠️ 需要在 Supabase Dashboard 確認郵件

## 快速測試步驟

### 方式 1: 在 Supabase Dashboard 確認測試帳號

1. 前往 [Supabase Dashboard](https://app.supabase.com)
2. 選擇您的專案
3. 點擊 **SQL Editor**
4. 執行 `confirm_test_user.sql` 中的 SQL 語句
5. 完成後使用以下帳號登入測試：
   ```
   Email: test@topicradar.com
   Password: test123456
   ```

### 方式 2: 關閉郵件驗證後重新註冊

1. 前往 Supabase Dashboard
2. Authentication > Settings
3. 取消勾選 "Enable email confirmations"
4. Save
5. 訪問 http://localhost:5001/login
6. 使用新的 Email 註冊（例如 user2@test.com）

## 測試登出功能

1. 登入成功後，檢查頂部狀態列：
   - ✅ 應該顯示使用者 Email
   - ✅ 應該顯示「登出」按鈕

2. 點擊「登出」按鈕：
   - ✅ 應該清除 localStorage 中的 auth_token
   - ✅ 應該重定向到 /login

3. 重新訪問首頁：
   - ✅ 應該自動導向 /login（因為未登入）

## 測試專題隔離

需要兩個帳號進行測試：

### 帳號 A 操作
1. 登入帳號 A
2. 前往後台建立專題（例如：「測試專題 A」）
3. 回到首頁確認可以看到該專題

### 帳號 B 操作
1. 登出帳號 A
2. 登入帳號 B
3. 前往首頁
4. ✅ 應該**看不到**帳號 A 建立的專題
5. 建立專題（例如：「測試專題 B」）
6. ✅ 只能看到自己的專題

### 驗證隔離性
1. 登出帳號 B，重新登入帳號 A
2. ✅ 只能看到「測試專題 A」
3. ✅ 看不到「測試專題 B」

## 自動化測試腳本

如果您想透過 API 測試，可以執行：

```bash
# 1. 登入取得 token
TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@topicradar.com","password":"test123456"}' \
  | jq -r '.access_token')

# 2. 查看專題列表
curl -s http://localhost:5001/api/all \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.topics'

# 3. 建立專題
curl -s -X POST http://localhost:5001/api/admin/topics \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試專題",
    "keywords": {"zh": ["測試", "驗證"]},
    "icon": "🧪"
  }' | jq '.'
```

## 已實作的功能 ✅

1. ✅ 登出按鈕（index.html）
2. ✅ 使用者資訊顯示（頂部狀態列）
3. ✅ 登出時清除 token
4. ✅ 登出後重定向到登入頁
5. ✅ 未登入時自動導向登入頁
6. ✅ 專題隔離（後端 API）
7. ✅ 新聞更新支援多使用者

## 下一步

請使用者手動執行以下操作之一：

1. **在 Supabase Dashboard 確認 test@topicradar.com 的郵件**
2. **或關閉郵件驗證功能**
3. **或直接在 Dashboard 建立新的測試帳號並勾選 Auto Confirm**

完成後即可進行完整的功能測試。
