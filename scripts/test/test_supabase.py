#!/usr/bin/env python3
"""測試 Supabase 資料庫連接與表格狀態"""

import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

import auth

print('=== Supabase 連接測試 ===\n')

# 檢查環境變數
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

print(f'SUPABASE_URL: {supabase_url[:40]}...' if supabase_url else '❌ 未設定')
print(f'SUPABASE_KEY: {"✅ 已設定" if supabase_key else "❌ 未設定"}')
print()

try:
    supabase = auth.get_supabase()
    print('✅ Supabase 客戶端初始化成功\n')

    print('=== 資料庫表格檢查 ===\n')

    tables = [
        ('user_roles', '使用者角色表'),
        ('invite_codes', '邀請碼表'),
        ('user_topics', '使用者專題表')
    ]

    all_exist = True

    for table_name, description in tables:
        try:
            result = supabase.table(table_name).select('*').limit(1).execute()
            row_count = len(result.data)
            print(f'✅ {table_name} ({description})')
            print(f'   資料筆數: {row_count}')
        except Exception as e:
            all_exist = False
            error_msg = str(e)
            print(f'❌ {table_name} ({description})')
            if 'does not exist' in error_msg or 'relation' in error_msg:
                print(f'   → 表格不存在，需要執行資料庫遷移')
            else:
                print(f'   → 錯誤: {error_msg[:80]}')
        print()

    print('='*60)
    if all_exist:
        print('✅ 所有表格都已建立！可以開始使用認證功能')
        print('\n下一步：')
        print('1. python3 app.py  # 啟動伺服器')
        print('2. 訪問 http://localhost:5001/login 測試註冊登入')
    else:
        print('⚠️  資料庫表格尚未建立')
        print('\n下一步：')
        print('1. 前往 Supabase Dashboard (https://app.supabase.com)')
        print('2. 選擇專案 > SQL Editor > New Query')
        print('3. 複製並執行 docs/supabase_migration.sql')
        print('4. 重新執行此測試腳本確認')
    print('='*60)

except Exception as e:
    print(f'❌ Supabase 連接失敗: {e}')
