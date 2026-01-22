-- 確認測試使用者的郵件
-- 在 Supabase Dashboard > SQL Editor 執行此腳本

-- 步驟 1: 查詢測試使用者
SELECT id, email, email_confirmed_at, created_at
FROM auth.users
WHERE email = 'test@topicradar.com';

-- 步驟 2: 手動確認郵件（複製上面查詢到的 user_id 替換下面的 'USER_ID'）
-- UPDATE auth.users
-- SET email_confirmed_at = NOW(),
--     confirmed_at = NOW()
-- WHERE email = 'test@topicradar.com';

-- 步驟 3: 設定使用者角色（複製 user_id 替換 'USER_ID'）
-- INSERT INTO user_roles (user_id, role)
-- VALUES ('USER_ID', 'user')
-- ON CONFLICT (user_id) DO UPDATE SET role = 'user';

-- 步驟 4: 標記邀請碼已使用（複製 user_id 替換 'USER_ID'）
-- UPDATE invite_codes
-- SET used_by = 'USER_ID',
--     used_at = NOW()
-- WHERE code = 'wakuwaku2026';

-- 完成後，可以使用以下帳號登入：
-- Email: test@topicradar.com
-- Password: test123456
