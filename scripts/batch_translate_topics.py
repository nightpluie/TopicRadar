#!/usr/bin/env python3
"""
批次更新腳本 - 為所有現有專題添加多語言關鍵字

此腳本會：
1. 讀取 Supabase 中所有專題
2. 對於只有中文關鍵字的專題，自動翻譯成英日韓三語
3. 更新資料庫
"""

import os
import sys
import time
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 匯入 auth 模組（需要先確保在正確目錄）
sys.path.insert(0, os.path.dirname(__file__))
import auth

# 引入翻譯函數（從 app.py）
import requests

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

def translate_with_gemini(text, target_lang='zh-TW', max_retries=3):
    """使用 Gemini Flash 翻譯文字到指定語言"""
    if not GEMINI_API_KEY:
        print(f"[ERROR] 無 Gemini API Key")
        return None

    # 語言名稱對應
    lang_names = {
        'zh-TW': '繁體中文',
        'en': 'English',
        'ja': '日本語',
        'ko': '한국어'
    }
    
    target_lang_name = lang_names.get(target_lang, '繁體中文')

    for attempt in range(max_retries):
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            headers = {"Content-Type": "application/json"}
            params = {"key": GEMINI_API_KEY}

            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"請將以下文字翻譯成{target_lang_name}，只輸出翻譯結果，不要有任何其他說明：\n\n{text}"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 200
                }
            }

            response = requests.post(url, headers=headers, params=params, json=payload, timeout=15)
            
            if response.status_code == 429:
                wait_time = (attempt + 1) * 2
                print(f"[WARN] API 速率限制，等待 {wait_time} 秒...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            data = response.json()
            translated = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
            return translated if translated else None

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)
                continue
            print(f"[ERROR] 翻譯失敗: {e}")
            return None
    
    return None


def auto_translate_keywords(chinese_keywords):
    """自動將中文關鍵字翻譯成英日韓三語"""
    if not isinstance(chinese_keywords, list) or not chinese_keywords:
        return {'zh': [], 'en': [], 'ja': [], 'ko': []}
    
    source_text = ', '.join(chinese_keywords)
    
    try:
        # 翻譯成英文
        en_keywords = []
        en_result = translate_with_gemini(source_text, target_lang='en')
        if en_result:
            en_keywords = [kw.strip() for kw in en_result.split(',') if kw.strip()]
        
        # 翻譯成日文
        ja_keywords = []
        ja_result = translate_with_gemini(source_text, target_lang='ja')
        if ja_result:
            ja_keywords = [kw.strip() for kw in ja_result.split(',') if kw.strip()]
        
        # 翻譯成韓文
        ko_keywords = []
        ko_result = translate_with_gemini(source_text, target_lang='ko')
        if ko_result:
            ko_keywords = [kw.strip() for kw in ko_result.split(',') if kw.strip()]
        
        print(f"  ✓ 翻譯完成: EN={len(en_keywords)}, JA={len(ja_keywords)}, KO={len(ko_keywords)}")
        
        return {
            'zh': chinese_keywords,
            'en': en_keywords,
            'ja': ja_keywords,
            'ko': ko_keywords
        }
    except Exception as e:
        print(f"  ✗ 翻譯失敗: {e}")
        return {
            'zh': chinese_keywords,
            'en': [],
            'ja': [],
            'ko': []
        }


def main():
    """主程式"""
    print("=" * 60)
    print("批次更新專題多語言關鍵字")
    print("=" * 60)
    print()
    
    # 檢查 API Key
    if not GEMINI_API_KEY:
        print("❌ 錯誤：未設定 GEMINI_API_KEY")
        print("請在 .env 檔案中設定 GEMINI_API_KEY")
        return
    
    # 檢查認證系統
    if not auth.AUTH_ENABLED:
        print("❌ 錯誤：認證系統未啟用")
        print("此腳本僅支援使用 Supabase 的系統")
        return
    
    # 獲取所有使用者
    try:
        from supabase import create_client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ 錯誤：未設定 Supabase 連線資訊")
            return
        
        supabase = create_client(supabase_url, supabase_key)
        
        # 獲取所有專題
        result = supabase.table('topics').select('*').execute()
        all_topics = result.data
        
        print(f"📊 找到 {len(all_topics)} 個專題\n")
        
        # 統計
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for topic in all_topics:
            topic_id = topic['id']
            topic_name = topic['name']
            keywords = topic.get('keywords', {})
            
            print(f"處理專題: {topic_name} (ID: {topic_id})")
            
            # 檢查關鍵字格式
            if isinstance(keywords, list):
                # 舊格式：純陣列
                print(f"  → 舊格式關鍵字，進行翻譯...")
                new_keywords = auto_translate_keywords(keywords)
            elif isinstance(keywords, dict):
                zh_keywords = keywords.get('zh', [])
                en_keywords = keywords.get('en', [])
                ja_keywords = keywords.get('ja', [])
                ko_keywords = keywords.get('ko', [])
                
                # 檢查是否缺少多語言關鍵字
                if not en_keywords and not ja_keywords and not ko_keywords:
                    print(f"  → 僅有中文關鍵字，進行翻譯...")
                    new_keywords = auto_translate_keywords(zh_keywords)
                else:
                    print(f"  ✓ 已有多語言關鍵字，跳過")
                    skipped_count += 1
                    print()
                    continue
            else:
                print(f"  ⚠ 無效的關鍵字格式，跳過")
                error_count += 1
                print()
                continue
            
            # 更新資料庫
            try:
                supabase.table('topics').update({
                    'keywords': new_keywords
                }).eq('id', topic_id).execute()
                
                print(f"  ✓ 已更新資料庫")
                updated_count += 1
                
                # 避免 API 速率限制
                time.sleep(1)
            except Exception as e:
                print(f"  ✗ 更新失敗: {e}")
                error_count += 1
            
            print()
        
        # 顯示總結
        print("=" * 60)
        print("處理完成！")
        print("=" * 60)
        print(f"✓ 已更新: {updated_count} 個專題")
        print(f"⊘ 已跳過: {skipped_count} 個專題（已有多語言關鍵字）")
        print(f"✗ 錯誤: {error_count} 個專題")
        print()
        
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
