#!/usr/bin/env python3
"""
建立測試使用者腳本
直接在 Supabase 建立已確認的測試帳號
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def create_test_user():
    """建立測試使用者"""

    # 使用 service role key 來繞過 RLS
    service_key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY

    supabase: Client = create_client(SUPABASE_URL, service_key)

    test_email = "test@topicradar.com"
    test_password = "test123456"

    print(f"[INFO] 正在建立測試使用者: {test_email}")

    try:
        # 註冊使用者
        response = supabase.auth.sign_up({
            "email": test_email,
            "password": test_password,
            "options": {
                "data": {
                    "email_confirm": True  # 自動確認
                }
            }
        })

        if response.user:
            user_id = response.user.id
            print(f"[SUCCESS] 使用者建立成功！")
            print(f"[INFO] User ID: {user_id}")
            print(f"[INFO] Email: {test_email}")

            # 設定為一般使用者角色
            try:
                supabase.table('user_roles').insert({
                    'user_id': user_id,
                    'role': 'user'
                }).execute()
                print(f"[SUCCESS] 使用者角色設定完成")
            except Exception as e:
                print(f"[WARN] 角色設定失敗（可能已存在）: {e}")

            # 標記邀請碼為已使用
            try:
                supabase.table('invite_codes').update({
                    'used_by': user_id,
                    'used_at': 'now()'
                }).eq('code', 'wakuwaku2026').execute()
                print(f"[SUCCESS] 邀請碼標記完成")
            except Exception as e:
                print(f"[WARN] 邀請碼標記失敗: {e}")

            print(f"\n✅ 測試帳號建立完成！")
            print(f"Email: {test_email}")
            print(f"Password: {test_password}")

        else:
            print(f"[ERROR] 使用者建立失敗")

    except Exception as e:
        print(f"[ERROR] 發生錯誤: {e}")
        print(f"\n請手動在 Supabase Dashboard 建立使用者：")
        print(f"1. 前往 Authentication > Users")
        print(f"2. 點擊 'Add user' > 'Create new user'")
        print(f"3. Email: {test_email}")
        print(f"4. Password: {test_password}")
        print(f"5. ✅ 勾選 'Auto Confirm User'")

if __name__ == '__main__':
    create_test_user()
