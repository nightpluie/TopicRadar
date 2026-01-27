-- 一次性修復所有外鍵約束問題
-- 確保刪除用戶時自動清理所有相關資料

BEGIN;

-- ============================================
-- 1. topic_cache 表
-- ============================================
ALTER TABLE topic_cache DROP CONSTRAINT IF EXISTS topic_cache_user_id_fkey;
ALTER TABLE topic_cache DROP CONSTRAINT IF EXISTS topic_cache_topic_id_fkey;

ALTER TABLE topic_cache
ADD CONSTRAINT topic_cache_user_id_fkey
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE topic_cache
ADD CONSTRAINT topic_cache_topic_id_fkey
FOREIGN KEY (topic_id) REFERENCES user_topics(id) ON DELETE CASCADE;

-- ============================================
-- 2. topic_archive 表
-- ============================================
ALTER TABLE topic_archive DROP CONSTRAINT IF EXISTS fk_archive_user;
ALTER TABLE topic_archive DROP CONSTRAINT IF EXISTS fk_archive_topic;

ALTER TABLE topic_archive
ADD CONSTRAINT fk_archive_user
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE topic_archive
ADD CONSTRAINT fk_archive_topic
FOREIGN KEY (topic_id) REFERENCES user_topics(id) ON DELETE CASCADE;

-- ============================================
-- 3. topic_angles 表
-- ============================================
ALTER TABLE topic_angles DROP CONSTRAINT IF EXISTS fk_angles_user;
ALTER TABLE topic_angles DROP CONSTRAINT IF EXISTS fk_topic;

ALTER TABLE topic_angles
ADD CONSTRAINT fk_angles_user
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE topic_angles
ADD CONSTRAINT fk_topic
FOREIGN KEY (topic_id) REFERENCES user_topics(id) ON DELETE CASCADE;

-- ============================================
-- 4. invite_codes 表
-- ============================================
ALTER TABLE invite_codes DROP CONSTRAINT IF EXISTS invite_codes_created_by_fkey;
ALTER TABLE invite_codes DROP CONSTRAINT IF EXISTS invite_codes_used_by_fkey;

ALTER TABLE invite_codes
ADD CONSTRAINT invite_codes_created_by_fkey
FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE SET NULL;

ALTER TABLE invite_codes
ADD CONSTRAINT invite_codes_used_by_fkey
FOREIGN KEY (used_by) REFERENCES auth.users(id) ON DELETE SET NULL;

COMMIT;

-- ============================================
-- 驗證所有外鍵設定
-- ============================================
SELECT
    tc.table_name,
    kcu.column_name,
    tc.constraint_name,
    rc.delete_rule,
    CASE
        WHEN rc.delete_rule IN ('CASCADE', 'SET NULL') THEN '✅'
        ELSE '❌'
    END as status
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON rc.unique_constraint_name = ccu.constraint_name
WHERE ccu.table_schema = 'auth'
    AND ccu.table_name = 'users'
    AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, kcu.column_name;

-- ============================================
-- 完成！現在可以安全刪除用戶了
-- ============================================
