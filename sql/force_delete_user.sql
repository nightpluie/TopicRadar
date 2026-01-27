-- 強制刪除用戶（找出並解決所有阻礙）
-- 請替換 'USER_EMAIL_HERE' 為要刪除的用戶 email

-- ============================================
-- 步驟 1: 找出要刪除的用戶 ID
-- ============================================
SELECT
    id,
    email,
    created_at,
    last_sign_in_at,
    CASE
        WHEN last_sign_in_at IS NULL THEN '從未登入'
        WHEN last_sign_in_at < NOW() - INTERVAL '30 days' THEN '超過 30 天未登入'
        WHEN last_sign_in_at < NOW() - INTERVAL '7 days' THEN '超過 7 天未登入'
        ELSE '最近有登入'
    END as activity_status
FROM auth.users
WHERE email = 'USER_EMAIL_HERE';  -- 替換成要刪除的 email

-- ============================================
-- 步驟 2: 查看這個用戶有哪些資料
-- ============================================
-- 專題數量
SELECT 'user_topics' as table_name, COUNT(*) as count
FROM user_topics
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'USER_EMAIL_HERE')
UNION ALL
-- 歸檔新聞數量
SELECT 'topic_archive' as table_name, COUNT(*) as count
FROM topic_archive
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'USER_EMAIL_HERE')
UNION ALL
-- 分析記錄數量
SELECT 'topic_angles' as table_name, COUNT(*) as count
FROM topic_angles
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'USER_EMAIL_HERE');

-- ============================================
-- 步驟 3: 手動刪除所有相關資料（如果自動 CASCADE 失敗）
-- ============================================
-- 先刪除分析記錄
DELETE FROM topic_angles
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'USER_EMAIL_HERE');

-- 再刪除歸檔新聞
DELETE FROM topic_archive
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'USER_EMAIL_HERE');

-- 再刪除專題（這會觸發 CASCADE 刪除相關資料）
DELETE FROM user_topics
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'USER_EMAIL_HERE');

-- 最後刪除用戶（這會觸發 CASCADE 刪除 user_roles）
DELETE FROM auth.users
WHERE email = 'USER_EMAIL_HERE';

-- ============================================
-- 步驟 4: 驗證刪除成功
-- ============================================
SELECT
    'auth.users' as table_name,
    COUNT(*) as remaining_count
FROM auth.users
WHERE email = 'USER_EMAIL_HERE'
UNION ALL
SELECT
    'user_topics' as table_name,
    COUNT(*) as remaining_count
FROM user_topics
WHERE user_id NOT IN (SELECT id FROM auth.users)
UNION ALL
SELECT
    'topic_archive' as table_name,
    COUNT(*) as remaining_count
FROM topic_archive
WHERE user_id NOT IN (SELECT id FROM auth.users);

-- ============================================
-- 完成！如果所有 remaining_count 都是 0，代表刪除成功
-- ============================================
