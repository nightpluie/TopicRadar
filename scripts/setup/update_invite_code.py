#!/usr/bin/env python3
"""更新邀請碼"""

import os
from dotenv import load_dotenv
load_dotenv()

import auth

print("=== 新增邀請碼 ===\n")

try:
    supabase = auth.get_supabase()

    # 新增邀請碼 wakuwaku2026
    result = supabase.table('invite_codes').insert({
        'code': 'wakuwaku2026',
        'expires_at': None  # 永不過期
    }).execute()

    print("✅ 邀請碼已新增: wakuwaku2026")
    print("   此邀請碼永不過期")

except Exception as e:
    error_msg = str(e)
    if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
        print("⚠️ 邀請碼 wakuwaku2026 已存在")
    else:
        print(f"❌ 新增失敗: {e}")

print("\n=== 所有可用邀請碼 ===\n")

try:
    result = supabase.table('invite_codes').select('*').is_('used_by', 'null').execute()

    if result.data:
        for code in result.data:
            print(f"📧 {code['code']}")
            if code.get('expires_at'):
                print(f"   到期: {code['expires_at']}")
            else:
                print(f"   永不過期")
            print()
    else:
        print("目前沒有可用的邀請碼")

except Exception as e:
    print(f"查詢失敗: {e}")
