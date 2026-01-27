-- 修復 invite_codes 表的外鍵約束
-- 讓刪除用戶時自動處理邀請碼關聯

-- ============================================
-- 1. 先移除舊的外鍵約束
-- ============================================

-- 刪除 created_by 的舊約束
ALTER TABLE invite_codes
DROP CONSTRAINT IF EXISTS invite_codes_created_by_fkey;

-- 刪除 used_by 的舊約束
ALTER TABLE invite_codes
DROP CONSTRAINT IF EXISTS invite_codes_used_by_fkey;

-- ============================================
-- 2. 加上新的外鍵約束（帶 ON DELETE SET NULL）
-- ============================================

-- created_by: 刪除用戶時設為 NULL（邀請碼仍可保留）
ALTER TABLE invite_codes
ADD CONSTRAINT invite_codes_created_by_fkey
FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE SET NULL;

-- used_by: 刪除用戶時設為 NULL（保留使用記錄但不綁定用戶）
ALTER TABLE invite_codes
ADD CONSTRAINT invite_codes_used_by_fkey
FOREIGN KEY (used_by) REFERENCES auth.users(id) ON DELETE SET NULL;

-- ============================================
-- 3. 驗證修復
-- ============================================

SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    rc.update_rule,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.table_name = 'invite_codes'
    AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY kcu.ordinal_position;

-- ============================================
-- 完成！現在可以安全刪除用戶了
-- ============================================
