-- =====================================================
-- 邀請碼系統升級：支援多次使用
-- 執行環境：Supabase Dashboard > SQL Editor
-- =====================================================

-- 步驟 1: 新增欄位到 invite_codes 表
-- max_uses: 最大使用次數 (NULL = 無限使用)
-- use_count: 已使用次數 (預設 0)
ALTER TABLE invite_codes
ADD COLUMN IF NOT EXISTS max_uses INTEGER DEFAULT 3,
ADD COLUMN IF NOT EXISTS use_count INTEGER DEFAULT 0;

-- 步驟 2: 建立使用記錄表（追蹤誰用了這個邀請碼）
CREATE TABLE IF NOT EXISTS invite_code_uses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    invite_code_id UUID NOT NULL REFERENCES invite_codes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    used_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(invite_code_id, user_id)  -- 同一個使用者不能重複使用同一個邀請碼
);

-- 啟用 RLS
ALTER TABLE invite_code_uses ENABLE ROW LEVEL SECURITY;

-- 管理員可以查看所有使用記錄
CREATE POLICY "Admins can view all invite code uses"
    ON invite_code_uses FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_roles
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- 步驟 3: 更新現有邀請碼
-- 將舊的邀請碼設定為已用完（used_by 不為 NULL 的）
UPDATE invite_codes
SET use_count = max_uses
WHERE used_by IS NOT NULL;

-- 將未使用的邀請碼設定為可用 3 次
UPDATE invite_codes
SET max_uses = 3, use_count = 0
WHERE used_by IS NULL;

-- 步驟 4: 建立/更新邀請碼
-- wakuwaku2026: 可用 3 次
INSERT INTO invite_codes (code, max_uses, use_count)
VALUES ('wakuwaku2026', 3, 0)
ON CONFLICT (code)
DO UPDATE SET max_uses = 3, use_count = 0, used_by = NULL, used_at = NULL;

-- peanut2026: 可用 3 次
INSERT INTO invite_codes (code, max_uses, use_count)
VALUES ('peanut2026', 3, 0)
ON CONFLICT (code)
DO UPDATE SET max_uses = 3, use_count = 0, used_by = NULL, used_at = NULL;

-- test2026: 可用 3 次（測試用）
INSERT INTO invite_codes (code, max_uses, use_count)
VALUES ('test2026', 3, 0)
ON CONFLICT (code)
DO UPDATE SET max_uses = 3, use_count = 0, used_by = NULL, used_at = NULL;

-- 步驟 5: 驗證設定
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
WHERE code IN ('wakuwaku2026', 'peanut2026', 'test2026')
ORDER BY created_at DESC;

-- =====================================================
-- 完成！
-- =====================================================
-- 已建立 3 個邀請碼：
--   1. wakuwaku2026 (可用 3 次)
--   2. peanut2026 (可用 3 次)
--   3. test2026 (可用 3 次，測試用)
