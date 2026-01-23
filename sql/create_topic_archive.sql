-- TopicRadar: 專題新聞歸檔表
-- 用於角度發現功能，儲存過濾後的新聞（標題 + RSS 摘要）

CREATE TABLE IF NOT EXISTS topic_archive (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    topic_id UUID NOT NULL,
    news_hash TEXT NOT NULL,
    
    -- 基本資訊（來自 RSS）
    title TEXT NOT NULL,
    summary TEXT,              -- RSS 摘要（約 200 字）
    url TEXT NOT NULL,
    source TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- 元資料
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 約束：同一使用者、同一專題、同一新聞只能儲存一次
    CONSTRAINT unique_user_topic_news UNIQUE (user_id, topic_id, news_hash)
);

-- 索引：依專題和時間查詢（最常用）
CREATE INDEX IF NOT EXISTS idx_archive_topic_time 
ON topic_archive(topic_id, published_at DESC);

-- 索引：依使用者查詢
CREATE INDEX IF NOT EXISTS idx_archive_user 
ON topic_archive(user_id);

-- 索引：複合索引（累積數量查詢）
CREATE INDEX IF NOT EXISTS idx_archive_count 
ON topic_archive(user_id, topic_id, published_at);

-- 註解
COMMENT ON TABLE topic_archive IS '專題新聞歸檔，用於 AI 角度發現分析';
COMMENT ON COLUMN topic_archive.summary IS 'RSS 原有摘要，約 200 字';
COMMENT ON COLUMN topic_archive.news_hash IS '新聞標題的 MD5 hash，用於去重';
