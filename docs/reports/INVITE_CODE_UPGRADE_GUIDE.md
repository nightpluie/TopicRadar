# 邀請碼系統升級指南

**升級時間**: 2026-01-21
**功能**: 從「一碼一用」升級到「一碼多用」

---

## 🎯 升級目標

- **舊系統**: 一個邀請碼只能用一次（used_by 不為 NULL 就不能再用）
- **新系統**: 一個邀請碼可以用 N 次（max_uses = 3，use_count < max_uses 就可以用）

---

## 📋 執行步驟

### 步驟 1: 執行資料庫遷移

1. 前往 [Supabase Dashboard](https://app.supabase.com)
2. 選擇您的專案
3. 點擊左側選單 **SQL Editor**
4. 點擊 **New Query**
5. 複製並執行 `migrate_invite_codes.sql` 的內容

**SQL 會做什麼**:
- ✅ 新增 `max_uses` 欄位（預設 3）
- ✅ 新增 `use_count` 欄位（預設 0）
- ✅ 建立 `invite_code_uses` 表（追蹤使用記錄）
- ✅ 更新現有邀請碼的狀態
- ✅ 建立/更新 `wakuwaku2026` 和 `peanut2026` 邀請碼

### 步驟 2: 驗證資料庫更新

執行以下查詢檢查邀請碼狀態：

```sql
SELECT
    code,
    max_uses,
    use_count,
    CASE
        WHEN max_uses IS NULL THEN '無限使用'
        WHEN use_count >= max_uses THEN '已用完'
        ELSE CONCAT('剩餘 ', max_uses - use_count, ' 次')
    END as status,
    created_at
FROM invite_codes
ORDER BY created_at DESC;
```

**預期結果**:
| code | max_uses | use_count | status |
|------|----------|-----------|--------|
| test2026 | 3 | 0 | 剩餘 3 次 |
| peanut2026 | 3 | 0 | 剩餘 3 次 |
| wakuwaku2026 | 3 | 0 | 剩餘 3 次 |

### 步驟 3: 重啟伺服器

```bash
# 停止目前的伺服器（如果有在運行）
# 在終端機按 Ctrl+C 或執行：
pkill -f "python3 app.py"

# 重新啟動
cd ~/Desktop/TopicRadar
source venv/bin/activate
python3 app.py
```

### 步驟 4: 測試邀請碼功能

使用以下測試腳本：

```bash
# 第一次使用 wakuwaku2026 註冊
curl -X POST http://localhost:5001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test1@example.com","password":"test123456","invite_code":"wakuwaku2026"}'

# 第二次使用 wakuwaku2026 註冊（應該成功）
curl -X POST http://localhost:5001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test2@example.com","password":"test123456","invite_code":"wakuwaku2026"}'

# 第三次使用 wakuwaku2026 註冊（應該成功）
curl -X POST http://localhost:5001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test3@example.com","password":"test123456","invite_code":"wakuwaku2026"}'

# 第四次使用 wakuwaku2026 註冊（應該失敗：已達上限）
curl -X POST http://localhost:5001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test4@example.com","password":"test123456","invite_code":"wakuwaku2026"}'
```

---

## 📊 新資料庫結構

### invite_codes 表（更新）

| 欄位 | 類型 | 說明 | 新增/修改 |
|------|------|------|-----------|
| id | UUID | 主鍵 | 原有 |
| code | VARCHAR(20) | 邀請碼 | 原有 |
| created_by | UUID | 建立者 | 原有 |
| used_by | UUID | 使用者（舊欄位，保留相容性） | 原有 |
| used_at | TIMESTAMPTZ | 使用時間（舊欄位） | 原有 |
| expires_at | TIMESTAMPTZ | 過期時間 | 原有 |
| **max_uses** | **INTEGER** | **最大使用次數（NULL=無限）** | **✨ 新增** |
| **use_count** | **INTEGER** | **已使用次數** | **✨ 新增** |
| created_at | TIMESTAMPTZ | 建立時間 | 原有 |

### invite_code_uses 表（新建）

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| invite_code_id | UUID | 邀請碼 ID（FK） |
| user_id | UUID | 使用者 ID（FK） |
| used_at | TIMESTAMPTZ | 使用時間 |

**UNIQUE 限制**: (invite_code_id, user_id) - 同一使用者不能重複使用同一邀請碼

---

## 🔧 程式碼變更

### auth.py 修改（行 115-170）

#### 1. 邀請碼驗證邏輯

**舊邏輯**:
```python
if invite.get('used_by') is not None:
    return None, "邀請碼已被使用"
```

**新邏輯**:
```python
max_uses = invite.get('max_uses')
use_count = invite.get('use_count', 0)

if max_uses is not None and use_count >= max_uses:
    return None, f"邀請碼已達使用上限 ({use_count}/{max_uses})"
```

#### 2. 註冊成功後的處理

**舊邏輯**:
```python
supabase.table('invite_codes').update({
    'used_by': result.user.id,
    'used_at': datetime.now(timezone.utc).isoformat()
}).eq('code', invite_code).execute()
```

**新邏輯**:
```python
# 更新使用次數
new_use_count = use_count + 1
supabase.table('invite_codes').update({
    'use_count': new_use_count
}).eq('id', invite_id).execute()

# 記錄使用詳情
supabase.table('invite_code_uses').insert({
    'invite_code_id': invite_id,
    'user_id': result.user.id
}).execute()
```

---

## ✅ 驗證清單

執行完畢後，請確認：

- [ ] 資料庫已新增 `max_uses` 和 `use_count` 欄位
- [ ] 資料庫已建立 `invite_code_uses` 表
- [ ] `wakuwaku2026` 和 `peanut2026` 邀請碼已建立/更新
- [ ] 伺服器已重啟（載入新的 auth.py）
- [ ] 第一次註冊成功（use_count = 1）
- [ ] 第二次註冊成功（use_count = 2）
- [ ] 第三次註冊成功（use_count = 3）
- [ ] 第四次註冊失敗（顯示「已達使用上限」）

---

## 🎯 新邀請碼列表

| 邀請碼 | 最大使用次數 | 已使用次數 | 用途 | 狀態 |
|--------|-------------|-----------|------|------|
| wakuwaku2026 | 3 | 0 | 正式使用 | ✅ 可用 |
| peanut2026 | 3 | 0 | 正式使用 | ✅ 可用 |
| test2026 | 3 | 0 | 測試部署 | ✅ 可用 |

---

## 💡 未來擴展

### 建立無限使用的邀請碼

```sql
INSERT INTO invite_codes (code, max_uses, use_count)
VALUES ('UNLIMITED2026', NULL, 0);
```

### 建立單次使用的邀請碼

```sql
INSERT INTO invite_codes (code, max_uses, use_count)
VALUES ('ONCE2026', 1, 0);
```

### 建立 10 次使用的邀請碼

```sql
INSERT INTO invite_codes (code, max_uses, use_count)
VALUES ('TEAM2026', 10, 0);
```

---

**升級完成！** 🎉
