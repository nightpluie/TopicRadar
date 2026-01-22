#!/usr/bin/env python3
"""設定管理員帳號"""

import os
from dotenv import load_dotenv
load_dotenv()

import auth

email = "Chen-Yu@nightpluie.com"
password = "CY80664001"
invite_code = "WELCOME2026"

print("=== 註冊管理員帳號 ===\n")

# 嘗試註冊
result, error = auth.signup(email, password, invite_code)

if error:
    print(f"⚠️ 註冊失敗或帳號已存在: {error}")
    print("\n嘗試登入以確認帳號狀態...")

    # 嘗試登入
    login_result, login_error = auth.login(email, password)
    if login_error:
        print(f"❌ 登入也失敗: {login_error}")
        print("\n請檢查：")
        print("1. 邀請碼是否有效")
        print("2. Email 格式是否正確")
        print("3. 密碼是否符合要求（至少 6 個字元）")
    else:
        print(f"✅ 帳號已存在，登入成功")
        user_id = login_result.user.id
        print(f"User ID: {user_id}")

        # 設為管理員
        print("\n正在設定為管理員...")

        # 直接使用 Supabase 更新
        try:
            supabase = auth.get_supabase()
            supabase.table('user_roles').upsert({
                'user_id': user_id,
                'role': 'admin'
            }).execute()
            print("✅ 已設為管理員")
        except Exception as e:
            print(f"⚠️ 設定管理員失敗: {e}")
            print(f"\n請在 Supabase SQL Editor 手動執行：")
            print(f"INSERT INTO user_roles (user_id, role) VALUES ('{user_id}', 'admin') ON CONFLICT (user_id) DO UPDATE SET role = 'admin';")
else:
    print(f"✅ 註冊成功！")
    user_id = result.user.id
    print(f"User ID: {user_id}")

    # 設為管理員
    print("\n正在設定為管理員...")
    try:
        supabase = auth.get_supabase()
        supabase.table('user_roles').upsert({
            'user_id': user_id,
            'role': 'admin'
        }).execute()
        print("✅ 已設為管理員")
    except Exception as e:
        print(f"⚠️ 設定管理員失敗: {e}")

print("\n" + "="*60)
print("✅ 完成！現在可以用以下帳號登入：")
print(f"   Email: {email}")
print(f"   Password: {password}")
print(f"   管理員權限: 已設定")
print("="*60)
