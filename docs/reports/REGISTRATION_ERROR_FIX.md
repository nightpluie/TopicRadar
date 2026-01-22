# 註冊錯誤處理改進報告

**修改時間**: 2026-01-21 13:51
**狀態**: ✅ 已完成並重啟伺服器

---

## 🔍 問題分析

### 使用者回報的問題

1. **第一次註冊顯示「網路失敗」**
   - 實際上註冊成功了（信箱收到確認信）
   - 但使用者以為失敗，可能會重複嘗試

2. **第二次嘗試顯示速率限制錯誤**
   - `"For security purposes, you can only request this after 49 seconds"`
   - 這是 Supabase 的 60 秒速率限制保護

3. **登入顯示「Email not confirmed」**
   - 新註冊的帳號無法登入
   - 錯誤訊息是英文，不夠清楚

### 根本原因

**註冊流程**（`app.py:1928-1947`）:
1. 呼叫 `auth.signup()` → **成功**（帳號已建立）
2. 嘗試自動登入 `auth.login()` → **失敗**（因為 Email 未確認）
3. 返回 `200` + 錯誤訊息 `"註冊成功但登入失敗，請手動登入"`

**前端問題**（`login.html:438-461` 修改前）:
- 當 `response.ok` 為 true 時，直接假設有 `data.access_token`
- 沒有檢查 `data.error` 的情況
- 導致 JavaScript 錯誤，進入 catch 區塊顯示「網路失敗」

---

## ✅ 修改內容

### 1. 前端錯誤處理改進 (`login.html:438-477`)

**修改前**:
```javascript
if (response.ok) {
    // 直接假設有 access_token
    localStorage.setItem('auth_token', data.access_token);
    // ...
} else {
    showMessage(data.error || '操作失敗', 'error');
}
```

**修改後**:
```javascript
if (response.ok) {
    // ✅ 檢查是否真的成功（有 access_token）
    if (data.access_token && data.user) {
        // 儲存 token，導向前台
        localStorage.setItem('auth_token', data.access_token);
        // ...
    } else if (data.error) {
        // ✅ 200 回應但有錯誤訊息（例如「註冊成功但登入失敗」）
        showMessage(data.error, 'error');
    } else {
        showMessage('操作失敗，請稍後再試', 'error');
    }
} else {
    // ✅ 特別處理 Supabase 速率限制錯誤
    let errorMsg = data.error || '操作失敗';

    if (errorMsg.includes('security purposes') || errorMsg.includes('seconds')) {
        errorMsg = '請求過於頻繁，請稍後再試（需等待約 60 秒）';
    }

    showMessage(errorMsg, 'error');
}
```

**改進點**:
- ✅ 檢查 `data.access_token` 和 `data.user` 是否存在
- ✅ 處理 200 回應但有錯誤的情況
- ✅ 將 Supabase 的英文錯誤訊息轉換為中文

### 2. 後端登入錯誤訊息改進 (`auth.py:212-225`)

**修改前**:
```python
except Exception as e:
    error_msg = str(e)
    if 'invalid' in error_msg.lower():
        return None, "Email 或密碼錯誤"
    return None, f"登入失敗: {error_msg}"
```

**修改後**:
```python
except Exception as e:
    error_msg = str(e)
    print(f"[AUTH] 登入失敗: {error_msg}")

    # 檢查各種錯誤類型
    error_lower = error_msg.lower()

    # ✅ 偵測 Email 未確認的錯誤
    if 'email not confirmed' in error_lower or 'not confirmed' in error_lower:
        return None, "Email 尚未確認，請先點擊確認信中的連結"

    if 'invalid' in error_lower or 'credentials' in error_lower:
        return None, "Email 或密碼錯誤"

    return None, f"登入失敗: {error_msg}"
```

**改進點**:
- ✅ 偵測「Email not confirmed」錯誤
- ✅ 返回清楚的中文錯誤訊息
- ✅ 增加 console log 方便除錯

---

## 🧪 測試場景

### 場景 1: 第一次註冊（Email 未確認）

**操作**:
1. 前往 http://localhost:5001/login
2. 切換到「註冊」標籤
3. 輸入新的 Email + 密碼 + 邀請碼（例如 `wakuwaku2026`）
4. 點擊「註冊」

**預期結果**:
- ✅ 顯示：`"註冊成功但登入失敗，請手動登入"`
- ✅ 使用者知道註冊成功，但需要確認 Email
- ✅ 信箱收到 Supabase 的確認信

**改進前的錯誤**:
- ❌ 顯示：`"網路錯誤，請稍後再試"`
- ❌ 使用者以為註冊失敗

### 場景 2: 60 秒內重複註冊

**操作**:
1. 在上一次註冊後 60 秒內
2. 再次點擊「註冊」（使用相同或不同 Email）

**預期結果**:
- ✅ 顯示：`"請求過於頻繁，請稍後再試（需等待約 60 秒）"`
- ✅ 使用者知道需要等待

**改進前的錯誤**:
- ❌ 顯示：`"For security purposes, you can only request this after 49 seconds"`
- ❌ 英文錯誤訊息，不夠清楚

### 場景 3: Email 未確認就嘗試登入

**操作**:
1. 使用剛註冊的帳號嘗試登入
2. 但還沒有點擊確認信中的連結

**預期結果**:
- ✅ 顯示：`"Email 尚未確認，請先點擊確認信中的連結"`
- ✅ 使用者知道需要去信箱確認

**改進前的錯誤**:
- ❌ 顯示：`"登入失敗: Email not confirmed"`
- ❌ 英文錯誤訊息

### 場景 4: Email 已確認後登入

**操作**:
1. 點擊確認信中的連結
2. 回到登入頁面
3. 輸入 Email + 密碼，點擊「登入」

**預期結果**:
- ✅ 顯示：`"登入成功！"`
- ✅ 自動導向前台 `/`
- ✅ 可以正常使用所有功能

---

## 📊 檔案變更摘要

| 檔案 | 修改行數 | 變更說明 |
|------|---------|----------|
| `login.html` | 438-477 | 改進錯誤處理邏輯，檢查 access_token 是否存在 |
| `auth.py` | 212-225 | 偵測 Email 未確認錯誤，返回中文訊息 |

---

## 🎯 使用者體驗改進

### 改進前的使用者流程

1. 註冊 → ❌ 顯示「網路失敗」
2. 以為失敗，再次註冊 → ❌ 顯示英文速率限制訊息
3. 等待 60 秒，再次註冊 → ❌ 顯示「此 Email 已被註冊」
4. 困惑，嘗試登入 → ❌ 顯示英文「Email not confirmed」
5. 不知道要去信箱確認

### 改進後的使用者流程

1. 註冊 → ✅ 顯示「註冊成功但登入失敗，請手動登入」
2. 知道註冊成功，嘗試登入 → ✅ 顯示「Email 尚未確認，請先點擊確認信中的連結」
3. 去信箱點擊確認連結
4. 再次登入 → ✅ 登入成功！

---

## 🚀 部署

### 本地環境

- ✅ 已重啟伺服器（PID: 982, 8107）
- ✅ 可立即測試：http://localhost:5001/login

### 生產環境（Render）

1. 將程式碼推送到 GitHub:
```bash
git add login.html auth.py REGISTRATION_ERROR_FIX.md
git commit -m "Fix: improve registration error handling for email confirmation

- Check for access_token before treating response as success
- Handle 200 responses with error messages
- Translate Supabase rate limit errors to Chinese
- Detect 'Email not confirmed' and show clear Chinese message

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"

git push origin main
```

2. Render 將自動部署
3. 部署完成後使用 `peanut2026` 邀請碼測試

---

## 📝 注意事項

### Supabase Email 確認設定

**預設行為**:
- Supabase 預設要求 Email 確認才能登入
- 註冊後會發送確認信到使用者信箱
- 使用者必須點擊連結才能啟用帳號

**如何關閉 Email 確認（不建議）**:

如果您想要關閉這個功能（測試用），可以在 Supabase Dashboard 修改：

1. 前往 Supabase Dashboard
2. 選擇您的專案
3. 點擊 **Authentication** > **Settings**
4. 找到 **Email Auth**
5. 關閉 **Enable email confirmations**

**建議**:
- 生產環境應該保持 Email 確認功能（安全性）
- 本地測試時可以手動在 Dashboard 確認使用者

### 手動確認使用者 Email

如果測試帳號需要快速啟用：

1. 前往 Supabase Dashboard > Authentication > Users
2. 找到該使用者
3. 點擊使用者進入詳細頁面
4. 點擊 **Confirm email** 按鈕

---

## ✨ 未來可能的改進

### 1. 自動重新發送確認信

在登入頁面增加「重新發送確認信」按鈕：

```javascript
async function resendConfirmationEmail() {
    const email = document.getElementById('email').value;
    const response = await fetch('/api/auth/resend-confirmation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    });
    // ...
}
```

### 2. 註冊成功後顯示確認提示

```javascript
if (data.error && data.error.includes('註冊成功')) {
    showMessage(
        '註冊成功！我們已發送確認信到您的信箱，請點擊信中的連結以啟用帳號。',
        'success'
    );
}
```

### 3. 倒數計時器

當遇到速率限制時，顯示倒數計時器：

```javascript
let remainingSeconds = 60;
const interval = setInterval(() => {
    remainingSeconds--;
    if (remainingSeconds <= 0) {
        clearInterval(interval);
        // 啟用註冊按鈕
    } else {
        showMessage(`請等待 ${remainingSeconds} 秒後再試`, 'info');
    }
}, 1000);
```

---

**修改完成時間**: 2026-01-21 13:51
**測試狀態**: ⏳ 待測試
**伺服器狀態**: ✅ 已重啟，運行中
