#!/usr/bin/env python3
# 批次更新專題關鍵字（生成四語關鍵字：中英日韓）

import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
TOPICS_FILE = 'topics_config.json'

def generate_keywords_with_ai(topic_name):
    """使用 Claude 生成議題相關關鍵字（中英日韓四語）"""
    if not ANTHROPIC_API_KEY:
        print(f"[WARN] 無 Anthropic API Key")
        return None

    try:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 800,
            "messages": [
                {
                    "role": "user",
                    "content": f"""你是一位專業的新聞資料庫管理員。請針對「{topic_name}」這個新聞議題，列出搜尋關鍵字。

要求：
1. 繁體中文關鍵字：10-15 個（核心詞彙、相關單位、同義詞）
2. 英文關鍵字：8-10 個（對應的英文詞彙，用於搜尋國際新聞）
3. 日文關鍵字：8-10 個（對應的日文詞彙，用於搜尋日本新聞）
4. 韓文關鍵字：8-10 個（對應的韓文詞彙，用於搜尋韓國新聞）

格式（請嚴格遵守）：
ZH: 關鍵字1, 關鍵字2, 關鍵字3
EN: keyword1, keyword2, keyword3
JA: キーワード1, キーワード2, キーワード3
KO: 키워드1, 키워드2, 키워드3

直接輸出，不要有其他開場白或解釋。"""
                }
            ]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        content = data.get('content', [{}])[0].get('text', '')

        # 解析四語關鍵字
        keywords = {'zh': [], 'en': [], 'ja': [], 'ko': []}
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('ZH:'):
                keywords['zh'] = [kw.strip() for kw in line[3:].split(',') if kw.strip()]
            elif line.startswith('EN:'):
                keywords['en'] = [kw.strip() for kw in line[3:].split(',') if kw.strip()]
            elif line.startswith('JA:'):
                keywords['ja'] = [kw.strip() for kw in line[3:].split(',') if kw.strip()]
            elif line.startswith('KO:'):
                keywords['ko'] = [kw.strip() for kw in line[3:].split(',') if kw.strip()]

        # 確保至少有基本關鍵字
        if not keywords['zh']:
            keywords['zh'] = [topic_name]

        print(f"[AI] 為「{topic_name}」生成了關鍵字: ZH={len(keywords['zh'])}, EN={len(keywords['en'])}, JA={len(keywords['ja'])}, KO={len(keywords['ko'])}")
        return keywords

    except Exception as e:
        print(f"[ERROR] Claude 關鍵字生成失敗: {e}")
        return None

if __name__ == '__main__':
    # 讀取現有專題
    with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
        topics = json.load(f)

    print(f"[INFO] 找到 {len(topics)} 個專題，開始更新關鍵字...")

    # 更新每個專題的關鍵字
    updated_count = 0
    for topic_id, topic_data in topics.items():
        topic_name = topic_data.get('name', '')
        current_keywords = topic_data.get('keywords', [])

        # 如果已經是字典格式（新格式），跳過
        if isinstance(current_keywords, dict):
            print(f"[SKIP] {topic_name} 已經是新格式")
            continue

        print(f"\n[UPDATE] 正在更新「{topic_name}」...")
        new_keywords = generate_keywords_with_ai(topic_name)

        if new_keywords:
            topics[topic_id]['keywords'] = new_keywords
            updated_count += 1
            print(f"[SUCCESS] 已更新「{topic_name}」")
            time.sleep(2)  # 避免 API rate limit
        else:
            print(f"[FAIL] 無法更新「{topic_name}」")

    # 儲存更新後的專題
    with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)

    print(f"\n[COMPLETE] 完成！成功更新 {updated_count} 個專題的關鍵字")
