#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# 建立 Supabase 客戶端
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    # 查詢測試使用者
    result = supabase.table('auth.users').select('id, email, email_confirmed_at').eq('email', 'test@topicradar.com').execute()
    
    if result.data:
        print(f"找到使用者: {result.data}")
    else:
        print("未找到使用者，嘗試從 auth schema 查詢...")
        
        # 使用 PostgREST 查詢（anon key 可能沒權限）
        import requests
        
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
        
        # 查詢使用者
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/auth.users?email=eq.test@topicradar.com',
            headers=headers
        )
        
        print(f"API 回應: {response.status_code}")
        print(f"內容: {response.text}")
        
except Exception as e:
    print(f"錯誤: {e}")
    print("\n由於 RLS 政策限制，無法透過 API 直接修改 auth.users 表。")
    print("請在 Supabase Dashboard 手動執行 SQL。")
