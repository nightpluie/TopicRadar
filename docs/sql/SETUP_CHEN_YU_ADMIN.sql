1; J-- =======================================================
-- TopicRadar 管理員帳號設定
-- 在 Supabase Dashboard > SQL Editor 執行此腳本
-- =======================================================

-- 步驟 1: 新增邀請碼 wakuwaku2026
INSERT INTO invite_codes (code)
VALUES ('wakuwaku2026')
ON CONFLICT (code) DO NOTHING;

-- 檢查邀請碼是否建立成功
SELECT code, created_at, used_by
FROM invite_codes
WHERE code IN ('wakuwaku2026', 'WELCOME2026')
ORDER BY created_at DESC;

-- =======================================================
-- 步驟 2: 建立管理員帳號的兩種方法
-- =======================================================

-- 【方法 A】如果您已經在 Authentication > Users 建立帳號：
-- 1. 前往 Authentication > Users
-- 2. 找到 Chen-Yu@nightpluie.com
-- 3. 複製 UID
-- 4. 執行以下 SQL（記得替換 UID）

-- INSERT INTO user_roles (user_id, role)
-- VALUES ('貼上您複製的UID', 'admin')
-- ON CONFLICT (user_id) DO UPDATE SET role = 'admin';


-- 【方法 B】從登入頁面註冊後設定：
-- 1. 前往 http://localhost:5001/login
-- 2. 使用以下資訊註冊：
--    Email: Chen-Yu@nightpluie.com
--    Password: CY80664001
--    邀請碼: wakuwaku2026
-- 3. 註冊成功後，執行以下 SQL 查詢 UID：

SELECT
    id as user_id,
    email,
    created_at,
    email_confirmed_at
FROM auth.users
WHERE email = 'Chen-Yu@nightpluie.com';

-- 4. 複製查詢到的 user_id，然後執行：

-- INSERT INTO user_roles (user_id, role)
-- VALUES ('貼上查詢到的user_id', 'admin')
-- ON CONFLICT (user_id) DO UPDATE SET role = 'admin';


-- =======================================================
-- 驗證設定是否成功
-- =======================================================

-- 查看所有使用者及其角色
SELECT
    ur.user_id,
    au.email,
    ur.role,
    ur.created_at
FROM user_roles ur
LEFT JOIN auth.users au ON ur.user_id = au.id
ORDER BY ur.created_at DESC;

-- 查看所有可用邀請碼
SELECT
    code,
    used_by,
    used_at,
    expires_at,
    created_at
FROM invite_codes
ORDER BY created_at DESC;
