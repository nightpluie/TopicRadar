#!/usr/bin/env python3
"""設定 Chen-Yu 管理員帳號"""

import os
from dotenv import load_dotenv
load_dotenv()

import auth

user_id = "e27efd8d-2b93-4159-8f66-485f98743fa0"

print("=== 設定管理員帳號 ===\n")

try:
    supabase = auth.get_supabase()

    # 1. 建立邀請碼
    print("1. 建立邀請碼 wakuwaku2026...")
    try:
        supabase.table('invite_codes').insert({'code': 'wakuwaku2026'}).execute()
        print("   ✅ 邀請碼已建立")
    except Exception as e:
        if 'duplicate' in str(e).lower():
            print("   ℹ️ 邀請碼已存在")
        else:
            print(f"   ⚠️ 建立邀請碼失敗: {e}")

    # 2. 設定為管理員
    print("\n2. 設定為管理員...")
    try:
        supabase.table('user_roles').upsert({
            'user_id': user_id,
            'role': 'admin'
        }).execute()
        print("   ✅ 已設定為管理員")
    except Exception as e:
        print(f"   ❌ 設定失敗: {e}")
        print("\n   請在 Supabase SQL Editor 手動執行：")
        print(f"   INSERT INTO user_roles (user_id, role) VALUES ('{user_id}', 'admin') ON CONFLICT (user_id) DO UPDATE SET role = 'admin';")

    # 3. 驗證
    print("\n3. 驗證設定...")
    try:
        result = supabase.table('user_roles').select('*').eq('user_id', user_id).execute()
        if result.data:
            print(f"   ✅ 角色: {result.data[0]['role']}")
        else:
            print("   ⚠️ 查無資料")
    except Exception as e:
        print(f"   ⚠️ 驗證失敗: {e}")

    print("\n" + "="*60)
    print("✅ 設定完成！")
    print("\n現在可以登入了：")
    print("   網址: http://localhost:5001/login")
    print("   Email: Chen-Yu@nightpluie.com")
    print("   Password: CY80664001")
    print("="*60)

except Exception as e:
    print(f"❌ 執行失敗: {e}")
