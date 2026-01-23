-- TopicRadar: 專題角度分析結果表
-- 用於儲存 AI 分析產生的調查角度與建議

CREATE TABLE IF NOT EXISTS topic_angles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    topic_id UUID NOT NULL,
    
    -- 分析狀態與結果
    status TEXT NOT NULL DEFAULT 'processing', -- processing, completed, failed
    angles_data JSONB,                         -- 儲存完整分析結果 (JSON)
    error_message TEXT,                        -- 失敗時的錯誤訊息
    
    -- 分析基礎數據
    analyzed_news_count INTEGER,               -- 本次分析使用的新聞數量
    data_range_start TIMESTAMP WITH TIME ZONE, -- 分析資料的開始時間
    data_range_end TIMESTAMP WITH TIME ZONE,   -- 分析資料的結束時間
    
    -- 時間戳記
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 約束：同一專題同一時間只能有一個進行中的分析任務 (防止重複點擊)
    -- 注意：這可能需要透過應用層邏輯或部分索引來實現，此處先不強制，由應用層控制
    CONSTRAINT fk_topic FOREIGN KEY (topic_id) REFERENCES user_topics(id) ON DELETE CASCADE
);

-- 索引：查詢特定專題的最新分析結果
CREATE INDEX IF NOT EXISTS idx_topic_angles_latest 
ON topic_angles(topic_id, created_at DESC);

-- 索引：查詢使用者所有分析
CREATE INDEX IF NOT EXISTS idx_topic_angles_user 
ON topic_angles(user_id);

-- 註解
COMMENT ON TABLE topic_angles IS '儲存 AI 針對專題新聞分析出的調查角度';
COMMENT ON COLUMN topic_angles.status IS '分析狀態：processing (分析中), completed (完成), failed (失敗)';
COMMENT ON COLUMN topic_angles.angles_data IS 'AI 分析回傳的 JSON 結構，包含多個角度與建議';
