-- TopicRadar: 修復級聯刪除 - 確保刪除用戶時自動清理所有相關資料
-- 執行此腳本前請先備份資料庫！
-- 在 Supabase Dashboard > SQL Editor 中執行

-- ============================================
-- 1. 為 topic_archive 加上外鍵約束
-- ============================================

-- 先刪除可能存在的孤兒資料（user_id 不存在的記錄）
DELETE FROM topic_archive
WHERE user_id NOT IN (SELECT id FROM auth.users);

-- 先刪除 topic_id 對應的專題已被刪除的記錄
DELETE FROM topic_archive
WHERE topic_id NOT IN (SELECT id FROM user_topics);

-- 加上外鍵約束（刪除用戶時自動刪除）
ALTER TABLE topic_archive
ADD CONSTRAINT fk_archive_user
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- 加上外鍵約束（刪除專題時自動刪除）
ALTER TABLE topic_archive
ADD CONSTRAINT fk_archive_topic
FOREIGN KEY (topic_id) REFERENCES user_topics(id) ON DELETE CASCADE;

-- ============================================
-- 2. 為 topic_angles 加上用戶外鍵約束（如果還沒有）
-- ============================================

-- 先檢查是否已有約束，如果沒有則加上
DO $$
BEGIN
    -- 刪除孤兒資料
    DELETE FROM topic_angles
    WHERE user_id NOT IN (SELECT id FROM auth.users);

    -- 加上用戶外鍵約束
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_angles_user'
    ) THEN
        ALTER TABLE topic_angles
        ADD CONSTRAINT fk_angles_user
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;

    -- 確保專題外鍵約束存在（可能已經有了）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_topic'
    ) THEN
        ALTER TABLE topic_angles
        ADD CONSTRAINT fk_topic
        FOREIGN KEY (topic_id) REFERENCES user_topics(id) ON DELETE CASCADE;
    END IF;
END $$;

-- ============================================
-- 3. 建立檢視 - 方便查看用戶資料統計
-- ============================================

CREATE OR REPLACE VIEW user_data_stats AS
SELECT
    u.id as user_id,
    u.email,
    ur.role,
    COUNT(DISTINCT ut.id) as topics_count,
    COUNT(DISTINCT ta.id) as archived_news_count,
    COUNT(DISTINCT tang.id) as analysis_count,
    MAX(ta.archived_at) as last_archived_at,
    MAX(tang.created_at) as last_analysis_at
FROM auth.users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN user_topics ut ON u.id = ut.user_id
LEFT JOIN topic_archive ta ON u.id = ta.user_id
LEFT JOIN topic_angles tang ON u.id = tang.user_id
GROUP BY u.id, u.email, ur.role
ORDER BY archived_news_count DESC;

-- ============================================
-- 4. 驗證結果
-- ============================================

-- 查看所有用戶的資料統計
SELECT * FROM user_data_stats;

-- 檢查是否還有孤兒資料
SELECT
    'topic_archive' as table_name,
    COUNT(*) as orphan_count
FROM topic_archive
WHERE user_id NOT IN (SELECT id FROM auth.users)
UNION ALL
SELECT
    'topic_angles' as table_name,
    COUNT(*) as orphan_count
FROM topic_angles
WHERE user_id NOT IN (SELECT id FROM auth.users);

-- ============================================
-- 完成！
-- ============================================
-- 現在可以安全地刪除用戶了，所有相關資料會自動清理：
-- DELETE FROM auth.users WHERE id = '要刪除的用戶ID';
