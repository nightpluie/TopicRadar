#!/usr/bin/env python3
"""
Turbo 按鈕功能驗證腳本
用途：檢查 topic_archive 表中的新聞累積數量，驗證 Turbo 按鈕顯示邏輯
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# 載入環境變數
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ 錯誤：請先設定 SUPABASE_URL 和 SUPABASE_SERVICE_KEY")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_all_users():
    """取得所有使用者"""
    try:
        result = supabase.table('topics').select('user_id').execute()
        user_ids = list(set([row['user_id'] for row in result.data if row.get('user_id')]))
        return user_ids
    except Exception as e:
        print(f"❌ 取得使用者失敗: {e}")
        return []

def check_topic_archive_count(user_id, topic_id):
    """檢查特定專題的新聞累積數量"""
    try:
        # 計算 30 天前的日期
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        # 查詢資料庫
        result = supabase.table('topic_archive')\
            .select('id', count='exact')\
            .eq('topic_id', topic_id)\
            .eq('user_id', user_id)\
            .gte('published_at', thirty_days_ago)\
            .execute()
        
        count = result.count if result.count else 0
        is_ready = count >= 30
        
        return {
            'count': count,
            'ready': is_ready,
            'threshold': 30
        }
    except Exception as e:
        print(f"❌ 查詢失敗 (topic_id={topic_id}): {e}")
        return None

def get_user_topics(user_id):
    """取得使用者的所有專題"""
    try:
        result = supabase.table('topics')\
            .select('id, name')\
            .eq('user_id', user_id)\
            .execute()
        return result.data
    except Exception as e:
        print(f"❌ 取得專題失敗: {e}")
        return []

def main():
    print("=" * 60)
    print("🔍 Turbo 按鈕功能驗證")
    print("=" * 60)
    print()
    
    # 取得所有使用者
    user_ids = get_all_users()
    
    if not user_ids:
        print("⚠️  找不到任何使用者")
        return
    
    print(f"📊 找到 {len(user_ids)} 位使用者\n")
    
    # 檢查每位使用者的專題
    for user_id in user_ids:
        print(f"\n👤 使用者 ID: {user_id}")
        print("-" * 60)
        
        topics = get_user_topics(user_id)
        
        if not topics:
            print("   ⚠️  沒有專題")
            continue
        
        for topic in topics:
            topic_id = topic['id']
            topic_name = topic['name']
            
            # 檢查累積數量
            stats = check_topic_archive_count(user_id, topic_id)
            
            if stats:
                count = stats['count']
                ready = stats['ready']
                
                # 顯示狀態
                status_icon = "🟢" if ready else "⚪"
                status_text = "就緒" if ready else "累積中"
                
                print(f"   {status_icon} {topic_name}")
                print(f"      累積: {count} 則 / 門檻: 30 則")
                print(f"      狀態: {status_text}")
                
                if ready:
                    print(f"      ⚡ Turbo 按鈕應該顯示為「綠色發光」")
                else:
                    print(f"      ⏳ Turbo 按鈕應該顯示為「灰色半透明」")
                print()
    
    print("=" * 60)
    print("✅ 驗證完成")
    print("=" * 60)
    print()
    print("💡 驗證步驟：")
    print("1. 對照上面的數據與 Admin 頁面的按鈕狀態")
    print("2. 將滑鼠移到 ⚡ 按鈕上，檢查 Tooltip 是否顯示正確數量")
    print("3. 確認 ≥30 則的專題按鈕是綠色且可點擊")
    print("4. 確認 <30 則的專題按鈕是灰色且不可點擊")

if __name__ == '__main__':
    main()
