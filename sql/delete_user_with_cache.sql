-- 刪除用戶及其所有相關資料（包含 topic_cache）
-- 因為 topic_cache 的資料類型不匹配，無法建立 CASCADE，需要手動刪除

-- ============================================
-- 方案 A: 刪除單一用戶
-- ============================================
-- 請替換 'USER_EMAIL_HERE' 為要刪除的用戶 email

-- 1. 先刪除 topic_cache（因為外鍵無法 CASCADE）
DELETE FROM topic_cache
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'USER_EMAIL_HERE');

-- 2. 再刪除用戶（會自動 CASCADE 刪除其他表）
DELETE FROM auth.users
WHERE email = 'USER_EMAIL_HERE';

-- ============================================
-- 方案 B: 批量刪除不活躍用戶
-- ============================================

-- 先查看哪些用戶可以刪除
SELECT
    u.id,
    u.email,
    u.last_sign_in_at,
    COUNT(DISTINCT ut.id) as topics_count,
    COUNT(DISTINCT tc.id) as cache_count,
    CASE
        WHEN u.last_sign_in_at IS NULL THEN '從未登入'
        WHEN u.last_sign_in_at < NOW() - INTERVAL '30 days' THEN '超過30天未登入'
        ELSE '最近有登入'
    END as status
FROM auth.users u
LEFT JOIN user_topics ut ON u.id = ut.user_id
LEFT JOIN topic_cache tc ON u.id = tc.user_id
GROUP BY u.id, u.email, u.last_sign_in_at
ORDER BY u.last_sign_in_at ASC NULLS FIRST;

-- 執行批量刪除（小心使用！）
-- 刪除從未登入的用戶
DO $$
DECLARE
    user_record RECORD;
BEGIN
    FOR user_record IN
        SELECT id FROM auth.users
        WHERE last_sign_in_at IS NULL  -- 從未登入
    LOOP
        -- 先刪除 topic_cache
        DELETE FROM topic_cache WHERE user_id = user_record.id;
        -- 再刪除用戶（自動 CASCADE）
        DELETE FROM auth.users WHERE id = user_record.id;
        RAISE NOTICE 'Deleted user: %', user_record.id;
    END LOOP;
END $$;

-- ============================================
-- 驗證刪除結果
-- ============================================
SELECT
    'Remaining users' as info,
    COUNT(*) as count
FROM auth.users;
