-- 修復 topic_cache 表的外鍵約束
-- 讓刪除用戶時自動刪除快取資料

-- ============================================
-- 1. 移除舊的外鍵約束
-- ============================================

ALTER TABLE topic_cache
DROP CONSTRAINT IF EXISTS topic_cache_user_id_fkey;

ALTER TABLE topic_cache
DROP CONSTRAINT IF EXISTS topic_cache_topic_id_fkey;

-- ============================================
-- 2. 加上新的外鍵約束（帶 ON DELETE CASCADE）
-- ============================================

-- user_id: 刪除用戶時自動刪除該用戶的所有快取
ALTER TABLE topic_cache
ADD CONSTRAINT topic_cache_user_id_fkey
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- topic_id: 刪除專題時自動刪除該專題的快取
ALTER TABLE topic_cache
ADD CONSTRAINT topic_cache_topic_id_fkey
FOREIGN KEY (topic_id) REFERENCES user_topics(id) ON DELETE CASCADE;

-- ============================================
-- 3. 驗證修復
-- ============================================

SELECT
    tc.constraint_name,
    kcu.column_name,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.table_name = 'topic_cache'
    AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY kcu.ordinal_position;

-- ============================================
-- 完成！現在可以刪除用戶了
-- ============================================
