-- =====================================================
-- TopicRadar 快速設定 - 一鍵完成所有設定
-- 請在 Supabase Dashboard > SQL Editor 執行此腳本
-- =====================================================

-- 步驟 1: 建立邀請碼
INSERT INTO invite_codes (code)
VALUES ('wakuwaku2026')
ON CONFLICT (code) DO NOTHING;

-- 步驟 2: 建立管理員帳號
-- 注意：這會建立一個未驗證的帳號，需要在 Authentication > Users 手動確認

-- 步驟 3: 查看現有帳號（如果有的話）
SELECT
    id,
    email,
    email_confirmed_at,
    created_at
FROM auth.users
WHERE email = 'Chen-Yu@nightpluie.com';

-- =====================================================
-- 如果上方查詢沒有結果，請使用以下兩種方法之一：
-- =====================================================

-- 【方法 A - 推薦】在 Supabase Dashboard 建立帳號：
-- 1. 前往 Authentication > Users
-- 2. 點擊 "Add user" > "Create new user"
-- 3. Email: Chen-Yu@nightpluie.com
-- 4. Password: CY80664001
-- 5. ✅ 勾選 "Auto Confirm User"
-- 6. 點擊 "Create user"
-- 7. 複製生成的 UID
-- 8. 執行下方 SQL（記得替換 UID）:

/*
INSERT INTO user_roles (user_id, role)
VALUES ('貼上您複製的UID', 'admin')
ON CONFLICT (user_id) DO UPDATE SET role = 'admin';
*/

-- 【方法 B】從網站註冊後設定：
-- 1. 確保上方的邀請碼已建立
-- 2. 前往 http://localhost:5001/login
-- 3. 註冊帳號：
--    Email: Chen-Yu@nightpluie.com
--    Password: CY80664001
--    邀請碼: wakuwaku2026
-- 4. 註冊成功後，執行以下 SQL:

-- 查詢剛註冊的帳號 UID
SELECT id, email FROM auth.users WHERE email = 'Chen-Yu@nightpluie.com';

-- 設定為管理員（替換下方的 UID）
/*
INSERT INTO user_roles (user_id, role)
VALUES ('貼上查詢到的UID', 'admin')
ON CONFLICT (user_id) DO UPDATE SET role = 'admin';
*/

-- =====================================================
-- 驗證設定
-- =====================================================

-- 檢查邀請碼
SELECT code, used_by, used_at FROM invite_codes WHERE code = 'wakuwaku2026';

-- 檢查管理員帳號
SELECT
    ur.user_id,
    au.email,
    ur.role
FROM user_roles ur
LEFT JOIN auth.users au ON ur.user_id = au.id
WHERE au.email = 'Chen-Yu@nightpluie.com';

-- =====================================================
-- 完成！
-- =====================================================
-- 設定完成後：
-- 1. 前往 http://localhost:5001/login
-- 2. 使用 Chen-Yu@nightpluie.com / CY80664001 登入
-- 3. 應該會看到管理員專區
-- =====================================================
