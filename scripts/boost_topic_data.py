#!/usr/bin/env python3
"""
Boost Topic Data Script
用途：強制將特定專題的歸檔新聞數量填充到 30 則以上，以測試 Turbo 按鈕。
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# 載入環境變數
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
# 優先使用 Service Key，若無則使用 Anon Key
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ 錯誤：請先設定 SUPABASE_URL 和 SUPABASE_KEY")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_target_topic(topic_name_keyword="長照"):
    """搜尋名稱包含特定關鍵字的專題"""
    try:
        # 先取得所有專題
        result = supabase.table('user_topics').select('id, name, user_id').execute()
        topics = result.data
        
        matches = [t for t in topics if topic_name_keyword in t['name']]
        return matches
    except Exception as e:
        print(f"❌ 搜尋專題失敗: {e}")
        return []

def boost_topic_data(user_id, topic_id, target_count=35):
    """填充資料直到達到目標數量"""
    try:
        # 1. 檢查目前數量
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        result = supabase.table('topic_archive')\
            .select('*')\
            .eq('topic_id', topic_id)\
            .eq('user_id', user_id)\
            .gte('published_at', thirty_days_ago)\
            .execute()
        
        current_data = result.data
        current_count = len(current_data)
        
        print(f"📊 目前累積數量: {current_count}")
        
        if current_count >= target_count:
            print("✅ 數量已足夠，無需填充。")
            return
            
        needed = target_count - current_count
        print(f"⚡ 需要填充 {needed} 則資料...")
        
        # 2. 準備填充資料
        # 如果有現有資料，複製它們；如果沒有，建立假資料
        source_item = current_data[0] if current_data else {
            'title': '測試新聞：長照政策新發展',
            'summary': '這是一則用於測試系統功能的自動生成新聞，模擬長照議題的相關報導。',
            'url': 'https://example.com/test',
            'source': '測試來源'
        }
        
        new_items = []
        for i in range(needed):
            # 產生過去 1-29 天內的隨機時間
            days_ago = (i % 29) + 1
            fake_time = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            item = {
                'user_id': user_id,
                'topic_id': topic_id,
                'news_hash': str(uuid.uuid4()), # 隨機 hash 避免衝突
                'title': f"[測試數據 {i+1}] {source_item['title']}",
                'summary': source_item['summary'],
                'url': source_item['url'],
                'source': source_item['source'],
                'published_at': fake_time
            }
            new_items.append(item)
            
        # 3. 批次寫入
        if new_items:
            supabase.table('topic_archive').insert(new_items).execute()
            print(f"✅ 已成功寫入 {len(new_items)} 則測試資料！")
            print("🎉 現在該專題的 Turbo 按鈕應該已經亮起！")
            
    except Exception as e:
        print(f"❌ 填充資料失敗: {e}")

def main():
    print("🚀 Turbo Tester: Boosting '長照' Topic")
    
    # 1. 找專題
    matches = get_target_topic("長照")
    
    if not matches:
        print("❌ 找不到名稱包含「長照」的專題。")
        return
        
    print(f"🔍 找到 {len(matches)} 個相關專題：")
    for idx, t in enumerate(matches):
        print(f"{idx+1}. [{t['name']}] (User: {t['user_id'][:8]}...)")
    
    # 自動選擇第一個（或是讓使用者選，這裡為了自動化先選第一個）
    target = matches[0]
    print(f"\n🎯 選擇目標: {target['name']}")
    
    # 2. 執行填充
    boost_topic_data(target['user_id'], target['id'])

if __name__ == '__main__':
    main()
