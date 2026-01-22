-- TopicRadar 使用者認證系統 - Supabase 資料庫遷移
-- 在 Supabase Dashboard > SQL Editor 中執行此腳本

-- ============================================
-- 1. 使用者專題表
-- ============================================
CREATE TABLE IF NOT EXISTS user_topics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(10) DEFAULT '📌',
    keywords JSONB NOT NULL,          -- 支援 {zh: [], en: [], ja: []} 格式
    negative_keywords JSONB DEFAULT '[]',
    "order" INTEGER DEFAULT 999,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS（行級安全策略）
ALTER TABLE user_topics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own topics"
    ON user_topics FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own topics"
    ON user_topics FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own topics"
    ON user_topics FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own topics"
    ON user_topics FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- 2. 邀請碼表
-- ============================================
CREATE TABLE IF NOT EXISTS invite_codes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    created_by UUID REFERENCES auth.users(id),
    used_by UUID REFERENCES auth.users(id),
    used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE invite_codes ENABLE ROW LEVEL SECURITY;

-- 管理員可以管理邀請碼
CREATE POLICY "Admins can manage invite codes"
    ON invite_codes FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM user_roles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- 任何人可以查看邀請碼是否有效（但不暴露敏感資訊）
CREATE POLICY "Anyone can check invite code validity"
    ON invite_codes FOR SELECT
    USING (true);

-- ============================================
-- 3. 使用者角色表
-- ============================================
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'user',  -- 'admin' or 'user'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

-- 使用者可以查看自己的角色
CREATE POLICY "Users can view their own role"
    ON user_roles FOR SELECT
    USING (auth.uid() = user_id);

-- 管理員可以管理所有角色
CREATE POLICY "Admins can manage roles"
    ON user_roles FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM user_roles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- ============================================
-- 4. 管理員查看所有專題的策略
-- ============================================
CREATE POLICY "Admins can view all topics"
    ON user_topics FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_roles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- ============================================
-- 5. 建立第一個管理員帳號（重要！）
-- ============================================
-- 首先在 Supabase Auth 中註冊一個帳號
-- 然後在這裡手動設定為管理員
-- 取得 user_id 的方法：
--   1. 前往 Authentication > Users
--   2. 找到你的帳號，複製 UID

-- 執行以下 SQL（取消註解並替換 YOUR_USER_ID）:
-- INSERT INTO user_roles (user_id, role) VALUES ('YOUR_USER_ID', 'admin');

-- ============================================
-- 6. 建立初始邀請碼（給管理員使用）
-- ============================================
-- 首次設置時，可以手動建立一個邀請碼供測試
-- INSERT INTO invite_codes (code, created_by) VALUES ('WELCOME2025', NULL);

-- ============================================
-- 完成！
-- ============================================
-- 接下來：
-- 1. 在 Supabase Dashboard 取得 Project URL 和 anon key
-- 2. 設定到 .env 檔案中
-- 3. 重啟伺服器
-- 4. 前往 /login 測試登入功能
