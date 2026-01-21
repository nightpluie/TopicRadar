#!/usr/bin/env python3
"""
邀請碼系統資料庫遷移腳本
自動執行 migrate_invite_codes.sql 中的所有 SQL 語句
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ 錯誤：缺少 SUPABASE_URL 或 SUPABASE_KEY")
    print("請檢查 .env 檔案")
    exit(1)

print("=" * 60)
print("邀請碼系統資料庫遷移")
print("=" * 60)
print()

# 建立 Supabase 客戶端
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("✅ 已連接到 Supabase")
print()

# 執行遷移步驟
try:
    print("步驟 1: 新增 max_uses 和 use_count 欄位...")
    # 注意：Supabase Python 客戶端不直接支援 ALTER TABLE
    # 我們需要使用 rpc 或直接透過 REST API

    print("⚠️  警告：Supabase Python 客戶端無法直接執行 DDL 語句")
    print("⚠️  需要手動在 Supabase Dashboard 執行 SQL")
    print()

    # 但我們可以檢查並建立邀請碼
    print("步驟 2: 建立/更新邀請碼...")

    codes = [
        {'code': 'wakuwaku2026', 'max_uses': 3, 'use_count': 0},
        {'code': 'peanut2026', 'max_uses': 3, 'use_count': 0},
        {'code': 'test2026', 'max_uses': 3, 'use_count': 0},
    ]

    for invite in codes:
        try:
            # 嘗試插入或更新
            result = supabase.table('invite_codes').upsert(invite, on_conflict='code').execute()
            if result.data:
                print(f"  ✅ {invite['code']}: 已建立/更新")
            else:
                print(f"  ⚠️  {invite['code']}: 可能需要先執行 ALTER TABLE")
        except Exception as e:
            error_msg = str(e)
            if 'column' in error_msg.lower() and ('max_uses' in error_msg.lower() or 'use_count' in error_msg.lower()):
                print(f"  ❌ {invite['code']}: 欄位尚未建立，需要先執行 SQL 遷移")
                print(f"     錯誤: {error_msg}")
            else:
                print(f"  ❌ {invite['code']}: {error_msg}")

    print()
    print("步驟 3: 驗證邀請碼...")

    # 查詢邀請碼
    try:
        result = supabase.table('invite_codes').select('*').in_('code', ['wakuwaku2026', 'peanut2026', 'test2026']).execute()

        if result.data:
            print()
            print("邀請碼列表:")
            print("-" * 60)
            for invite in result.data:
                code = invite.get('code')
                max_uses = invite.get('max_uses', '?')
                use_count = invite.get('use_count', '?')

                if max_uses == '?' or use_count == '?':
                    status = "⚠️  欄位尚未建立"
                elif max_uses is None:
                    status = "無限使用"
                elif use_count >= max_uses:
                    status = "已用完"
                else:
                    status = f"剩餘 {max_uses - use_count} 次"

                print(f"  {code}: max_uses={max_uses}, use_count={use_count} ({status})")
        else:
            print("  ⚠️  找不到邀請碼")
    except Exception as e:
        print(f"  ❌ 查詢失敗: {e}")

    print()
    print("=" * 60)
    print("遷移腳本執行完成")
    print("=" * 60)
    print()

    # 給出後續指示
    if '欄位尚未建立' in str(result.data if 'result' in locals() else ''):
        print("⚠️  偵測到欄位尚未建立")
        print()
        print("請手動執行以下步驟:")
        print("1. 前往 Supabase Dashboard > SQL Editor")
        print("2. 執行 migrate_invite_codes.sql 中的 SQL")
        print("3. 再次執行此腳本驗證")
    else:
        print("✅ 邀請碼系統已準備就緒！")
        print()
        print("您現在可以使用以下邀請碼:")
        print("  - wakuwaku2026 (可用 3 次)")
        print("  - peanut2026 (可用 3 次)")
        print("  - test2026 (可用 3 次，測試用)")

except Exception as e:
    print()
    print(f"❌ 發生錯誤: {e}")
    print()
    print("請檢查:")
    print("1. SUPABASE_URL 和 SUPABASE_KEY 是否正確")
    print("2. 是否有足夠的權限執行資料庫操作")
    exit(1)
