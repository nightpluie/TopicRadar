# 專題雷達 - Topic Radar
# Python 後端：RSS 抓取 + 關鍵字過濾 + AI 摘要 (Perplexity) + AI 關鍵字 (Claude)

import os
import re
import json
import time
import hashlib
import feedparser
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# 台北時區
TAIPEI_TZ = ZoneInfo('Asia/Taipei')

# 載入環境變數
load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ============ 設定 ============

# API Keys
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')
PERPLEXITY_MODEL = os.getenv('PERPLEXITY_MODEL', 'sonar')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# 專題設定儲存檔案
TOPICS_FILE = 'topics_config.json'

# 台灣媒體 RSS 來源
RSS_SOURCES_TW = {
    '聯合報': 'https://udn.com/rssfeed/news/2/0',
    '聯合報財經': 'https://udn.com/rssfeed/news/2/6645',
    '自由時報': 'https://news.ltn.com.tw/rss/all.xml',
    '自由財經': 'https://news.ltn.com.tw/rss/business.xml',
    'ETtoday': 'https://feeds.feedburner.com/ettoday/realtime',
    'ETtoday財經': 'https://feeds.feedburner.com/ettoday/finance',
    '報導者': 'https://www.twreporter.org/a/rss2.xml',
    'Google News TW': 'https://news.google.com/rss?hl=zh-TW&gl=TW&ceid=TW:zh-Hant',
    '公視新聞': 'https://news.pts.org.tw/xml/newsfeed.xml',
    '鏡週刊': 'https://www.mirrormedia.mg/rss/news.xml',
}

# 國際媒體 RSS 來源（英文/日文）
RSS_SOURCES_INTL = {
    'BBC News': 'https://feeds.bbci.co.uk/news/rss.xml',
    'The Guardian': 'https://www.theguardian.com/world/rss',
    'NHK (日文)': 'https://www3.nhk.or.jp/rss/news/cat0.xml',
    '朝日新聞 (日文)': 'http://rss.asahi.com/rss/asahi/newsheadlines.rdf',
}

# Google News 國際版來源
GOOGLE_NEWS_INTL_REGIONS = {
    '日本': {'code': 'JP', 'lang': 'ja'},
    '美國': {'code': 'US', 'lang': 'en'},
    '法國': {'code': 'FR', 'lang': 'fr'},
}

# 預設專題設定
DEFAULT_TOPICS = {
    'migrant_workers': {
        'name': '服務業移工',
        'keywords': ['移工', '外勞', '勞動部', '缺工', '外籍勞工', '移民署', '服務業', '餐飲業', '仲介'],
    },
    'labor_pension': {
        'name': '勞保年金改革',
        'keywords': ['勞保', '年金', '退休金', '勞動基金', '精算', '破產', '勞保局', '勞退', '老年給付'],
    },
    'housing_tax': {
        'name': '囤房稅2.0',
        'keywords': ['囤房稅', '房屋稅', '持有稅', '房價', '空屋', '多屋', '稅率', '非自住'],
    },
}

# 資料儲存
DATA_STORE = {
    'topics': {},           # 每個專題的台灣新聞列表
    'international': {},    # 每個專題的國際新聞列表（翻譯後）
    'summaries': {},        # 每個專題的 AI 摘要
    'last_update': None,
}

# 載入進度狀態
LOADING_STATUS = {
    'is_loading': False,
    'current': 0,
    'total': 0,
    'current_topic': '',
    'phase': ''  # 'news' 或 'summary'
}

TOPICS = {}

# 資料快取檔案路徑
DATA_CACHE_FILE = 'data_cache.json'

# ============ 資料快取管理 ============

def save_data_cache():
    """儲存資料到快取檔案（會覆蓋舊檔）"""
    try:
        # 準備要序列化的資料（處理 datetime 物件）
        cache_data = {
            'topics': {},
            'international': {},
            'summaries': DATA_STORE['summaries'],
            'last_update': DATA_STORE['last_update']
        }

        # 處理新聞資料（將 datetime 轉成字串）
        for tid, news_list in DATA_STORE['topics'].items():
            cache_data['topics'][tid] = []
            for news in news_list:
                news_copy = news.copy()
                if 'published' in news_copy and isinstance(news_copy['published'], datetime):
                    news_copy['published'] = news_copy['published'].isoformat()
                cache_data['topics'][tid].append(news_copy)

        for tid, news_list in DATA_STORE['international'].items():
            cache_data['international'][tid] = []
            for news in news_list:
                news_copy = news.copy()
                if 'published' in news_copy and isinstance(news_copy['published'], datetime):
                    news_copy['published'] = news_copy['published'].isoformat()
                cache_data['international'][tid].append(news_copy)

        # 寫入檔案（覆蓋）
        with open(DATA_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        print(f"[CACHE] 資料已儲存到 {DATA_CACHE_FILE}")

    except Exception as e:
        print(f"[CACHE] 儲存失敗: {e}")

def load_data_cache():
    """從快取檔案載入資料"""
    global DATA_STORE

    if not os.path.exists(DATA_CACHE_FILE):
        print(f"[CACHE] 快取檔案不存在，將使用空資料")
        return

    try:
        with open(DATA_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        # 載入摘要和最後更新時間
        DATA_STORE['summaries'] = cache_data.get('summaries', {})
        DATA_STORE['last_update'] = cache_data.get('last_update')

        # 載入新聞資料（將字串轉回 datetime）
        DATA_STORE['topics'] = {}
        for tid, news_list in cache_data.get('topics', {}).items():
            DATA_STORE['topics'][tid] = []
            for news in news_list:
                news_copy = news.copy()
                if 'published' in news_copy and isinstance(news_copy['published'], str):
                    news_copy['published'] = datetime.fromisoformat(news_copy['published'])
                DATA_STORE['topics'][tid].append(news_copy)

        DATA_STORE['international'] = {}
        for tid, news_list in cache_data.get('international', {}).items():
            DATA_STORE['international'][tid] = []
            for news in news_list:
                news_copy = news.copy()
                if 'published' in news_copy and isinstance(news_copy['published'], str):
                    news_copy['published'] = datetime.fromisoformat(news_copy['published'])
                DATA_STORE['international'][tid].append(news_copy)

        print(f"[CACHE] 從快取載入了 {len(DATA_STORE['topics'])} 個專題的資料")

    except Exception as e:
        print(f"[CACHE] 載入快取失敗: {e}")

# ============ 專題設定管理 ============

def load_topics_config():
    """從檔案載入專題設定"""
    global TOPICS
    try:
        if os.path.exists(TOPICS_FILE):
            with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
                TOPICS = json.load(f)
        else:
            TOPICS = DEFAULT_TOPICS.copy()
            save_topics_config()
    except Exception as e:
        print(f"[ERROR] 載入專題設定失敗: {e}")
        TOPICS = DEFAULT_TOPICS.copy()

def save_topics_config():
    """儲存專題設定到檔案"""
    try:
        with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(TOPICS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] 儲存專題設定失敗: {e}")

def generate_topic_id(name):
    """根據名稱生成唯一 ID"""
    timestamp = int(time.time() * 1000) % 100000
    prefix = re.sub(r'[^\w]', '', name)[:10]
    return f"{prefix}_{timestamp}"

# ============ AI 關鍵字生成 (Gemini) ============

def generate_keywords_with_ai(topic_name):
    """使用 Gemini Flash 生成議題相關關鍵字（中英日三語）"""
    if not GEMINI_API_KEY:
        print("[WARN] 無 Gemini API Key，使用預設關鍵字")
        return {
            'zh': [topic_name],
            'en': [],
            'ja': []
        }

    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {
            "Content-Type": "application/json"
        }
        params = {
            "key": GEMINI_API_KEY
        }

        prompt = f"""你是一位專業的新聞資料庫管理員。請針對「{topic_name}」這個新聞議題，列出搜尋關鍵字。

要求：
1. 繁體中文關鍵字：10-15 個（核心詞彙、相關單位、同義詞）
2. 英文關鍵字：8-10 個（對應的英文詞彙，用於搜尋國際新聞）
3. 日文關鍵字：8-10 個（對應的日文詞彙，用於搜尋日本新聞）

格式（請嚴格遵守）：
ZH: 關鍵字1, 關鍵字2, 關鍵字3
EN: keyword1, keyword2, keyword3
JA: キーワード1, キーワード2, キーワード3

直接輸出，不要有其他開場白或解釋。"""

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 800
            }
        }

        response = requests.post(url, headers=headers, params=params, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        content = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')

        # 解析三語關鍵字
        keywords = {'zh': [], 'en': [], 'ja': []}
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('ZH:'):
                keywords['zh'] = [kw.strip() for kw in line[3:].split(',') if kw.strip()]
            elif line.startswith('EN:'):
                keywords['en'] = [kw.strip() for kw in line[3:].split(',') if kw.strip()]
            elif line.startswith('JA:'):
                keywords['ja'] = [kw.strip() for kw in line[3:].split(',') if kw.strip()]

        # 確保至少有基本關鍵字
        if not keywords['zh']:
            keywords['zh'] = [topic_name]

        print(f"[AI] Gemini 為「{topic_name}」生成了關鍵字: ZH={len(keywords['zh'])}, EN={len(keywords['en'])}, JA={len(keywords['ja'])}")
        return keywords

    except Exception as e:
        print(f"[ERROR] Gemini 關鍵字生成失敗: {e}")
        return {
            'zh': [topic_name],
            'en': [],
            'ja': []
        }

# ============ Gemini Flash 翻譯 ============

def translate_with_gemini(text, source_lang='auto', max_retries=3):
    """使用 Gemini Flash 翻譯標題到繁體中文"""
    if not GEMINI_API_KEY:
        return f"[未翻譯] {text}"

    for attempt in range(max_retries):
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            headers = {
                "Content-Type": "application/json"
            }

            params = {
                "key": GEMINI_API_KEY
            }

            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"請將以下新聞標題翻譯成繁體中文，只輸出翻譯結果，不要有任何其他說明：\n\n{text}"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 200
                }
            }

            response = requests.post(url, headers=headers, params=params, json=payload, timeout=15)
            
            # 如果是 429 Too Many Requests，等待後重試
            if response.status_code == 429:
                wait_time = (attempt + 1) * 2  # 2, 4, 6 秒
                print(f"[WARN] Gemini API 速率限制，等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()

            data = response.json()
            translated = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()

            return translated if translated else f"[翻譯失敗] {text}"

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)
                continue
            print(f"[ERROR] Gemini 翻譯失敗: {e}")
            return f"[翻譯失敗] {text}"
    
    return f"[翻譯失敗] {text}"

# ============ Perplexity AI 摘要 ============

def generate_topic_summary(topic_id):
    """使用 Perplexity AI 生成專題摘要"""
    if not PERPLEXITY_API_KEY:
        return "（尚未設定 Perplexity API Key）"
    
    topic_config = TOPICS.get(topic_id)
    if not topic_config:
        return "（未知專題）"
    
    topic_name = topic_config['name']
    
    try:
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 取得目前最新的幾則新聞標題作為參考（輔助）
        if topic_id in DATA_STORE['topics']:
            recent_titles = [f"- {n['title']} ({n['published'].strftime('%Y/%m/%d') if isinstance(n['published'], datetime) else ''})" 
                           for n in DATA_STORE['topics'][topic_id][:5]]
            context = "\n".join(recent_titles)
        else:
            context = "（暫無相關 RSS 新聞）"

        current_time = datetime.now(TAIPEI_TZ).strftime('%Y/%m/%d')
        
        payload = {
            "model": PERPLEXITY_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位資深專題記者，正在為已經熟悉議題背景的同事更新最新進展。假設讀者已了解議題背景，不需要重複說明基本概念或歷史脈絡。直接切入最新動態和變化。"
                },
                {
                    "role": "user",
                    "content": f"議題：{topic_name}\n日期：{current_time}\n\n請用純文字格式（不要markdown）輸出最新進展摘要：\n\n內容要求：\n1. 本週或近期有什麼新動態？（政策發布、協商進展、重要事件、爭議）\n2. 目前推進到什麼階段？有什麼關鍵進展或轉折？\n3. 總共120字以內，繁體中文\n4. 如果有2-3個重點，每個重點自成一句，用句號結尾即可\n\n格式規則（非常重要）：\n- 第一個字直接開始寫內容，不要有任何空行、空格或前綴\n- 不要任何標題（如「最新動態」「進度報告」等）\n- 不要引用標記 [1][2]\n- 不要markdown符號（#、**、*、-）\n- 不要在結尾標註字數\n- 不要空行分段，所有內容連續書寫\n- 每個重點用句號結尾，然後直接接下一個重點\n\n範例格式（注意沒有空行）：\n勞保年金改革草案已於2026年1月正式啟動，預計最低投保薪資調升至29,500元。法案審議預計在2026年3月完成初審，但藍綠對於年齡級距仍存在分歧。接下來需關注立法院審議進度及各方協商結果。"
                }
            ],
            "max_tokens": 400,
            "temperature": 0.2
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        # 移除可能的引用標記 [1], [2] 等
        content = re.sub(r'\[\d+\]', '', content)

        # 移除 markdown 格式符號（#、**、*、###等）
        content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)  # 移除標題符號
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # 移除粗體 **text**
        content = re.sub(r'\*([^*]+)\*', r'\1', content)  # 移除斜體 *text*
        content = re.sub(r'^[-*]\s+', '', content, flags=re.MULTILINE)  # 移除列表符號

        # 移除開頭可能出現的標題（如「進度報告：」「最新動態：」等）
        content = re.sub(r'^[^：]*進度報告[：:]\s*', '', content)
        content = re.sub(r'^[^：]*最新動態[：:]\s*', '', content)
        content = re.sub(r'^[^：]*摘要[：:]\s*', '', content)

        # 移除結尾的字數標記（如「（200字）」「(200字)」等）
        content = re.sub(r'[（(]\s*\d+\s*字\s*[）)]$', '', content)

        # 第一次清理：移除首尾空白
        content = content.strip()

        # 第二次清理：移除開頭的所有空白字符（包括空格、tab、換行）
        while content and content[0] in (' ', '\t', '\n', '\r'):
            content = content[1:]

        # 第三次清理：使用 regex 移除開頭所有空白
        content = re.sub(r'^[\s\n\r]+', '', content)

        # 移除結尾的所有連續空行
        content = re.sub(r'[\s\n\r]+$', '', content)

        # 最後一次 strip 確保乾淨
        content = content.strip()

        return content if content else "（無法生成摘要）"
    
    except Exception as e:
        print(f"[ERROR] Perplexity 摘要失敗: {e}")
        return "（摘要生成失敗）"

# ============ RSS 抓取 ============

def fetch_rss(url, source_name, timeout=15, max_items=50):
    """抓取 RSS，增加最大抓取數量以確保能找到足夠的相關新聞"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        items = []
        # 增加抓取數量從 30 到 max_items，確保有足夠新聞可過濾
        for entry in feed.entries[:max_items]:
            # 獲取標題，跳過空標題
            title = entry.get('title', '').strip()
            if not title:
                continue

            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                # RSS 時間通常是 UTC，轉換為台北時間
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                published = published.astimezone(TAIPEI_TZ)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                published = published.astimezone(TAIPEI_TZ)
            else:
                # 使用台北時間的當前時間
                published = datetime.now(TAIPEI_TZ)

            items.append({
                'title': title,
                'link': entry.get('link', ''),
                'source': source_name,
                'published': published,
                'summary': entry.get('summary', '')[:200]
            })
        return items
    except Exception as e:
        print(f"[ERROR] 抓取 {source_name} 失敗: {e}")
        return []

def fetch_google_news_by_keywords(keywords, max_items=50):
    """使用 Google News 搜索特定關鍵字的新聞，並提取原始媒體來源"""
    if not keywords:
        return []

    # 使用第一個關鍵字作為搜索詞
    search_term = keywords[0] if isinstance(keywords, list) else keywords
    # Google News 搜索 RSS
    url = f"https://news.google.com/rss/search?q={search_term}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        items = []
        for entry in feed.entries[:max_items]:
            # 獲取標題，跳過空標題
            title = entry.get('title', '').strip()
            if not title:
                continue

            # 提取原始媒體來源（Google News RSS 特有）
            source_name = 'Google News'
            if hasattr(entry, 'source') and entry.source:
                source_name = entry.source.get('title', 'Google News')

            # 處理時間
            published = None
            is_date_only = False

            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                published = published.astimezone(TAIPEI_TZ)

                # 檢查是否是整點時間（可能只是日期的占位符）
                # 例如 08:00:00 可能只代表當天，不是真實時間
                if published.minute == 0 and published.second == 0:
                    is_date_only = True
            else:
                published = datetime.now(TAIPEI_TZ)

            items.append({
                'title': title,
                'link': entry.get('link', ''),
                'source': source_name,  # 使用原始媒體名稱
                'published': published,
                'summary': entry.get('summary', '')[:200],
                'is_date_only': is_date_only  # 標記僅有日期
            })
        return items
    except Exception as e:
        print(f"[ERROR] Google News 搜索失敗: {e}")
        return []

def fetch_google_news_intl(keywords, region_code, lang, max_items=30):
    """使用 Google News 國際版搜索特定國家的新聞"""
    if not keywords:
        return []

    # 使用第一個關鍵字作為搜索詞
    search_term = keywords[0] if isinstance(keywords, list) else keywords
    # Google News 國際版 RSS（根據國家代碼和語言）
    url = f"https://news.google.com/rss/search?q={search_term}&hl={lang}&gl={region_code}&ceid={region_code}:{lang}"

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        items = []
        for entry in feed.entries[:max_items]:
            title = entry.get('title', '').strip()
            if not title:
                continue

            # 提取原始媒體來源
            source_name = f'Google News ({region_code})'
            if hasattr(entry, 'source') and entry.source:
                source_name = entry.source.get('title', source_name)

            # 處理時間
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                published = published.astimezone(TAIPEI_TZ)
            else:
                published = datetime.now(TAIPEI_TZ)

            items.append({
                'title': title,
                'link': entry.get('link', ''),
                'source': source_name,
                'published': published,
                'summary': entry.get('summary', '')[:200]
            })
        return items
    except Exception as e:
        print(f"[ERROR] Google News {region_code} 搜索失敗: {e}")
        return []

def keyword_match(text, keywords, negative_keywords=None):
    """
    關鍵字比對，支援負面關鍵字過濾

    Args:
        text: 要檢查的文字
        keywords: 正面關鍵字列表（匹配任一即可）
        negative_keywords: 負面關鍵字列表（包含任一則排除）
    """
    if not text or not keywords:
        return False

    text_lower = text.lower()

    # 先檢查負面關鍵字，如果包含則直接排除
    if negative_keywords:
        for neg_kw in negative_keywords:
            if neg_kw.lower() in text_lower:
                return False

    # 再檢查正面關鍵字
    for kw in keywords:
        if kw.lower() in text_lower:
            return True

    return False

def update_single_topic_news(topic_id):
    """只更新單一專題的新聞（用於新增專題時）"""
    if topic_id not in TOPICS:
        return

    cfg = TOPICS[topic_id]
    print(f"\n[UPDATE] 更新單一專題新聞: {cfg['name']}")

    # 1. 抓取台灣新聞
    all_news_tw = []
    for name, url in RSS_SOURCES_TW.items():
        all_news_tw.extend(fetch_rss(url, name, max_items=50))

    # 2. 抓取國際新聞
    all_news_intl = []
    for name, url in RSS_SOURCES_INTL.items():
        all_news_intl.extend(fetch_rss(url, name, max_items=50))

    # 3. 抓取該專題的 Google News 國際版
    keywords = cfg.get('keywords', {})
    if isinstance(keywords, dict):
        keywords_en = keywords.get('en', [])
        keywords_ja = keywords.get('ja', [])

        if keywords_ja:
            all_news_intl.extend(fetch_google_news_intl(keywords_ja, 'JP', 'ja', max_items=20))
        if keywords_en:
            all_news_intl.extend(fetch_google_news_intl(keywords_en, 'US', 'en', max_items=20))
            all_news_intl.extend(fetch_google_news_intl(keywords_en, 'FR', 'fr', max_items=20))

    # 4. 過濾該專題的新聞
    keywords_zh = keywords.get('zh', []) if isinstance(keywords, dict) else keywords
    keywords_en = keywords.get('en', []) if isinstance(keywords, dict) else []
    keywords_ja = keywords.get('ja', []) if isinstance(keywords, dict) else []
    negative_keywords = cfg.get('negative_keywords', [])

    # 過濾台灣新聞
    filtered_tw = [n for n in all_news_tw if keyword_match(n['title'], keywords_zh, negative_keywords)]
    print(f"[SEARCH] {cfg['name']}: 找到 {len(filtered_tw)} 則台灣新聞")

    # Google News 補充（如需要）
    if len(filtered_tw) < 10:
        print(f"[SEARCH] {cfg['name']}: 只有 {len(filtered_tw)} 則，使用 Google News 搜索補充...")
        google_news = fetch_google_news_by_keywords(keywords_zh, max_items=20)
        for n in google_news:
            if keyword_match(n['title'], keywords_zh, negative_keywords):
                filtered_tw.append(n)
        print(f"[SEARCH] {cfg['name']}: 補充後共 {len(filtered_tw)} 則新聞")

    # 更新該專題的台灣新聞
    existing = DATA_STORE['topics'].get(topic_id, [])
    existing_hashes = {n['hash'] for n in existing}

    new_items = []
    for n in filtered_tw[:10]:
        n_hash = hashlib.md5(n['title'].encode()).hexdigest()
        n['hash'] = n_hash
        if n_hash not in existing_hashes:
            new_items.append(n)

    all_items = new_items + existing
    DATA_STORE['topics'][topic_id] = all_items[:10]

    if new_items:
        print(f"[UPDATE] {cfg['name']}: 新增 {len(new_items)} 則新聞，當前 {len(DATA_STORE['topics'][topic_id])} 則")

    # 過濾國際新聞
    intl_keywords = keywords_en + keywords_ja
    filtered_intl = [n for n in all_news_intl if keyword_match(n['title'], intl_keywords, negative_keywords)]

    # 翻譯國際新聞
    for n in filtered_intl:
        if 'title_original' not in n:
            n['title_original'] = n['title']
            translated = translate_with_gemini(n['title'])
            n['title'] = translated if translated else n['title']
            time.sleep(0.5)

    # Google News 國際補充
    if len(filtered_intl) < 5:
        for region_name, region_info in GOOGLE_NEWS_INTL_REGIONS.items():
            if len(filtered_intl) >= 5:
                break
            search_keywords = keywords_ja if region_info['lang'] == 'ja' else keywords_en
            google_intl = fetch_google_news_intl(search_keywords, region_info['code'], region_info['lang'], max_items=20)
            for n in google_intl:
                if keyword_match(n['title'], search_keywords, negative_keywords):
                    n['title_original'] = n['title']
                    translated = translate_with_gemini(n['title'])
                    n['title'] = translated if translated else n['title']
                    filtered_intl.append(n)
                    time.sleep(0.5)

    # 更新該專題的國際新聞
    existing_intl = DATA_STORE['international'].get(topic_id, [])
    existing_intl_hashes = {n['hash'] for n in existing_intl}

    new_intl_items = []
    for n in filtered_intl[:10]:
        n_hash = hashlib.md5(n.get('title_original', n['title']).encode()).hexdigest()
        n['hash'] = n_hash
        if n_hash not in existing_intl_hashes:
            new_intl_items.append(n)

    all_intl_items = new_intl_items + existing_intl
    DATA_STORE['international'][topic_id] = all_intl_items[:10]

    if new_intl_items:
        print(f"[UPDATE] {cfg['name']} (國際): 新增 {len(new_intl_items)} 則新聞，當前 {len(DATA_STORE['international'][topic_id])} 則")

    DATA_STORE['last_update'] = datetime.now(TAIPEI_TZ).isoformat()

    # 儲存到快取檔案
    save_data_cache()

    print(f"[UPDATE] {cfg['name']} 更新完成")

def update_topic_news():
    global LOADING_STATUS
    total_topics = len(TOPICS)
    LOADING_STATUS = {
        'is_loading': True,
        'current': 0,
        'total': total_topics,
        'current_topic': '',
        'phase': 'news'
    }
    print(f"\n[UPDATE] 開始更新新聞 - {datetime.now(TAIPEI_TZ).strftime('%H:%M:%S')}")

    # 1. 抓取台灣新聞（增加抓取數量）
    all_news_tw = []
    for name, url in RSS_SOURCES_TW.items():
        all_news_tw.extend(fetch_rss(url, name, max_items=50))

    # 2. 抓取國際新聞（增加抓取數量）
    all_news_intl = []
    for name, url in RSS_SOURCES_INTL.items():
        all_news_intl.extend(fetch_rss(url, name, max_items=50))

    # 2.5 抓取 Google News 國際版新聞（日本、美國、法國）
    # 為每個專題的國際關鍵字抓取對應國家的新聞
    google_news_intl = []
    for tid, cfg in TOPICS.items():
        keywords = cfg.get('keywords', {})
        if isinstance(keywords, dict):
            keywords_en = keywords.get('en', [])
            keywords_ja = keywords.get('ja', [])

            # 日本 Google News（使用日文關鍵字）
            if keywords_ja:
                google_news_intl.extend(fetch_google_news_intl(keywords_ja, 'JP', 'ja', max_items=20))

            # 美國 Google News（使用英文關鍵字）
            if keywords_en:
                google_news_intl.extend(fetch_google_news_intl(keywords_en, 'US', 'en', max_items=20))

            # 法國 Google News（使用英文關鍵字）
            if keywords_en:
                google_news_intl.extend(fetch_google_news_intl(keywords_en, 'FR', 'fr', max_items=20))

    all_news_intl.extend(google_news_intl)

    # 3. 過濾台灣新聞和國際新聞
    topic_index = 0
    for tid, cfg in TOPICS.items():
        topic_index += 1
        LOADING_STATUS['current'] = topic_index
        LOADING_STATUS['current_topic'] = cfg['name']
        keywords = cfg.get('keywords', {})

        # 處理舊格式（純列表）vs 新格式（字典）
        if isinstance(keywords, list):
            keywords_zh = keywords
            keywords_en = []
            keywords_ja = []
        else:
            keywords_zh = keywords.get('zh', [])
            keywords_en = keywords.get('en', [])
            keywords_ja = keywords.get('ja', [])

        # 獲取負面關鍵字
        negative_keywords = cfg.get('negative_keywords', [])

        # 過濾台灣新聞（使用中文關鍵字）- 確保至少10則
        if not keywords_zh:
            DATA_STORE['topics'][tid] = []
        else:
            # 取得現有新聞列表
            existing_news = DATA_STORE['topics'].get(tid, [])
            existing_hashes = {hashlib.md5(item['title'].encode()).hexdigest(): item
                             for item in existing_news}

            # 過濾新新聞
            filtered_tw = []
            seen_tw = set(existing_hashes.keys())
            new_items = []

            for item in all_news_tw:
                content = f"{item['title']} {item['summary']}"
                if keyword_match(content, keywords_zh, negative_keywords):
                    h = hashlib.md5(item['title'].encode()).hexdigest()
                    if h not in seen_tw:
                        seen_tw.add(h)
                        new_items.append(item)

            # 合併：新新聞 + 現有新聞，按時間排序
            all_items = new_items + existing_news
            all_items.sort(key=lambda x: x['published'], reverse=True)

            # 如果新聞數量少於 10 則，使用 Google News 搜索補充
            if len(all_items) < 10:
                print(f"[SEARCH] {cfg['name']}: 只有 {len(all_items)} 則，使用 Google News 搜索補充...")
                google_news = fetch_google_news_by_keywords(keywords_zh, max_items=100)

                # 過濾並去重
                existing_hashes_all = {hashlib.md5(item['title'].encode()).hexdigest() for item in all_items}
                for item in google_news:
                    if len(all_items) >= 10:
                        break
                    content = f"{item['title']} {item['summary']}"
                    if keyword_match(content, keywords_zh, negative_keywords):
                        h = hashlib.md5(item['title'].encode()).hexdigest()
                        if h not in existing_hashes_all:
                            existing_hashes_all.add(h)
                            all_items.append(item)

                all_items.sort(key=lambda x: x['published'], reverse=True)
                print(f"[SEARCH] {cfg['name']}: 補充後共 {len(all_items)} 則新聞")

            # 保持最新的 10 則（一則一則替換）
            DATA_STORE['topics'][tid] = all_items[:10]

            if new_items:
                print(f"[UPDATE] {cfg['name']}: 新增 {len(new_items)} 則新聞，當前 {len(DATA_STORE['topics'][tid])} 則")

        # 過濾國際新聞（使用英日文關鍵字）- 確保至少10則
        intl_keywords = keywords_en + keywords_ja
        if not intl_keywords:
            DATA_STORE['international'][tid] = []
        else:
            # 取得現有國際新聞
            existing_intl = DATA_STORE['international'].get(tid, [])
            existing_intl_hashes = {hashlib.md5(item.get('title_original', item['title']).encode()).hexdigest(): item
                                   for item in existing_intl}

            # 過濾新的國際新聞
            filtered_intl = []
            seen_intl = set(existing_intl_hashes.keys())
            new_intl_items = []

            for item in all_news_intl:
                content = f"{item['title']} {item['summary']}"
                if keyword_match(content, intl_keywords, negative_keywords):
                    h = hashlib.md5(item['title'].encode()).hexdigest()
                    if h not in seen_intl:
                        seen_intl.add(h)
                        # 翻譯標題（加入延遲避免 API 速率限制）
                        original_title = item['title']
                        translated_title = translate_with_gemini(original_title)
                        item['title_original'] = original_title
                        item['title'] = translated_title
                        new_intl_items.append(item)
                        time.sleep(0.5)  # 每次翻譯後等待 0.5 秒

            # 合併：新新聞 + 現有新聞，按時間排序
            all_intl_items = new_intl_items + existing_intl
            all_intl_items.sort(key=lambda x: x['published'], reverse=True)

            # 如果新聞數量少於 5 則，使用 Google News 國際版補充
            if len(all_intl_items) < 5:
                print(f"[SEARCH] {cfg['name']} (國際): 只有 {len(all_intl_items)} 則，使用 Google News 國際版補充...")

                # 依序從日本、美國、法國 Google News 補充
                for region_name, region_info in GOOGLE_NEWS_INTL_REGIONS.items():
                    if len(all_intl_items) >= 5:
                        break

                    # 根據語言選擇關鍵字
                    search_keywords = keywords_ja if region_info['lang'] == 'ja' else keywords_en
                    if not search_keywords:
                        continue

                    google_intl = fetch_google_news_intl(
                        search_keywords,
                        region_info['code'],
                        region_info['lang'],
                        max_items=20
                    )

                    # 過濾並翻譯
                    existing_hashes_all = {hashlib.md5(item.get('title_original', item['title']).encode()).hexdigest()
                                         for item in all_intl_items}
                    for item in google_intl:
                        if len(all_intl_items) >= 5:
                            break
                        content = f"{item['title']} {item['summary']}"
                        if keyword_match(content, intl_keywords, negative_keywords):
                            h = hashlib.md5(item['title'].encode()).hexdigest()
                            if h not in existing_hashes_all:
                                existing_hashes_all.add(h)
                                # 翻譯標題
                                original_title = item['title']
                                translated_title = translate_with_gemini(original_title)
                                item['title_original'] = original_title
                                item['title'] = translated_title
                                all_intl_items.append(item)
                                time.sleep(0.5)

                all_intl_items.sort(key=lambda x: x['published'], reverse=True)
                print(f"[SEARCH] {cfg['name']} (國際): 補充後共 {len(all_intl_items)} 則新聞")

            # 保持最新的 10 則（一則一則替換）
            DATA_STORE['international'][tid] = all_intl_items[:10]

            if new_intl_items:
                print(f"[UPDATE] {cfg['name']} (國際): 新增 {len(new_intl_items)} 則新聞，當前 {len(DATA_STORE['international'][tid])} 則")

    DATA_STORE['last_update'] = datetime.now(TAIPEI_TZ).isoformat()
    LOADING_STATUS['is_loading'] = False
    LOADING_STATUS['current'] = total_topics

    # 儲存到快取檔案
    save_data_cache()

    print("[UPDATE] 完成")
    # 摘要更新改用排程（每天 8:00 和 18:00），不在新聞更新時觸發

def update_all_summaries():
    print(f"\n[SUMMARY] 開始 AI 摘要...")
    for tid in TOPICS.keys():
        summary_text = generate_topic_summary(tid)
        DATA_STORE['summaries'][tid] = {
            'text': summary_text,
            'updated_at': datetime.now(TAIPEI_TZ).isoformat()
        }
        time.sleep(1)

    # 儲存到快取檔案
    save_data_cache()

    print("[SUMMARY] 完成")

# ============ API ============

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/admin')
def admin():
    return app.send_static_file('admin.html')

@app.route('/api/all')
def get_all():
    result = {'topics': {}, 'last_update': DATA_STORE['last_update']}
    for tid, cfg in TOPICS.items():
        news = DATA_STORE['topics'].get(tid, [])
        intl_news = DATA_STORE['international'].get(tid, [])
        summary = DATA_STORE['summaries'].get(tid, {})

        # 格式化台灣新聞
        fmt_news = []
        now = datetime.now(TAIPEI_TZ)
        for n in news[:10]:
            dt = n['published']
            # 確保 dt 有時區資訊
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TAIPEI_TZ)

            # 根據日期決定顯示格式
            is_date_only = n.get('is_date_only', False)

            if is_date_only:
                # Google News 等只有日期的新聞，只顯示日期
                time_str = dt.strftime('%m/%d')
            elif dt.date() == now.date():
                # 今天的新聞顯示時間
                time_str = dt.strftime('%H:%M')
            else:
                # 其他日期顯示月/日
                time_str = dt.strftime('%m/%d')

            fmt_news.append({
                'title': n['title'],
                'link': n['link'],
                'source': n['source'],
                'time': time_str
            })

        # 格式化國際新聞（最多10則）
        fmt_intl_news = []
        for n in intl_news[:10]:
            dt = n['published']
            # 確保 dt 有時區資訊
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TAIPEI_TZ)

            # 根據日期決定顯示格式
            if dt.date() == now.date():
                time_str = dt.strftime('%H:%M')
            else:
                time_str = dt.strftime('%m/%d')

            fmt_intl_news.append({
                'title': n['title'],
                'title_original': n.get('title_original', ''),
                'link': n['link'],
                'source': n['source'],
                'time': time_str
            })

        # 處理關鍵字顯示（只顯示中文關鍵字）
        keywords = cfg.get('keywords', [])
        if isinstance(keywords, dict):
            display_keywords = keywords.get('zh', [])
        else:
            display_keywords = keywords

        result['topics'][tid] = {
            'id': tid,
            'name': cfg['name'],
            'icon': cfg.get('icon', '📌'),
            'keywords': display_keywords,
            'summary': summary.get('text', ''),
            'summary_updated': summary.get('updated_at'),
            'news': fmt_news,
            'international': fmt_intl_news,
            'order': cfg.get('order', 999)
        }
    return jsonify(result)

@app.route('/api/refresh', methods=['POST'])
def refresh():
    update_topic_news()
    return jsonify({'status': 'ok'})

@app.route('/api/refresh-summary', methods=['POST'])
def refresh_summary():
    update_all_summaries()
    return jsonify({'status': 'ok'})

@app.route('/api/loading-status')
def loading_status():
    """回傳載入進度狀態"""
    return jsonify(LOADING_STATUS)

@app.route('/api/admin/topics', methods=['GET'])
def get_topics():
    # 回傳專題設定及摘要資訊
    result = {}
    for tid, cfg in TOPICS.items():
        # 處理關鍵字格式（新格式 dict vs 舊格式 list）
        keywords = cfg.get('keywords', [])
        if isinstance(keywords, dict):
            display_keywords = keywords.get('zh', [])
        else:
            display_keywords = keywords
        
        # 取得摘要
        summary_data = DATA_STORE['summaries'].get(tid, {})
        
        # 取得新聞數量
        news_count = len(DATA_STORE['topics'].get(tid, []))
        
        result[tid] = {
            'name': cfg['name'],
            'keywords': display_keywords,
            'negative_keywords': cfg.get('negative_keywords', []),
            'icon': cfg.get('icon', ''),
            'summary': summary_data.get('text', ''),
            'summary_updated': summary_data.get('updated_at'),
            'news_count': news_count,
            'order': cfg.get('order', 999)
        }
    return jsonify({'topics': result, 'last_update': DATA_STORE['last_update']})

@app.route('/api/admin/topics', methods=['POST'])
def add_topic():
    data = request.json
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Empty name'}), 400

    # AI 生成關鍵字
    keywords = generate_keywords_with_ai(name)

    # 計算新專題的 order（放在最後）
    max_order = max([t.get('order', 0) for t in TOPICS.values()], default=-1)
    new_order = max_order + 1

    tid = generate_topic_id(name)
    TOPICS[tid] = {'name': name, 'keywords': keywords, 'order': new_order}
    save_topics_config()

    # 只更新新專題的新聞（不更新其他專題）
    update_single_topic_news(tid)

    # 只為新專題生成摘要
    if PERPLEXITY_API_KEY:
        print(f"[INIT] 為新專題「{name}」生成 AI 摘要...")
        summary_text = generate_topic_summary(tid)
        DATA_STORE['summaries'][tid] = {
            'text': summary_text,
            'updated_at': datetime.now(TAIPEI_TZ).isoformat()
        }

    return jsonify({'status': 'ok'})

@app.route('/api/admin/topics/<tid>', methods=['PUT'])
def update_topic(tid):
    if tid not in TOPICS:
        return jsonify({'error': 'Not found'}), 404
    data = request.json
    if 'keywords' in data:
        TOPICS[tid]['keywords'] = data['keywords']
    if 'negative_keywords' in data:
        TOPICS[tid]['negative_keywords'] = data['negative_keywords']
    save_topics_config()
    update_topic_news()
    return jsonify({'status': 'ok'})

@app.route('/api/admin/topics/<tid>', methods=['DELETE'])
def delete_topic(tid):
    if tid in TOPICS:
        del TOPICS[tid]
        save_topics_config()
    return jsonify({'status': 'ok'})

@app.route('/api/admin/topics/reorder', methods=['PUT'])
def reorder_topics():
    """更新專題排序"""
    data = request.json
    order_list = data.get('order', [])

    print(f"[REORDER] 收到排序請求: {order_list}")

    # 更新每個專題的 order 欄位
    for item in order_list:
        tid = item.get('id')
        order = item.get('order')
        if tid in TOPICS:
            TOPICS[tid]['order'] = order
            print(f"[REORDER] 更新 {TOPICS[tid]['name']} 的順序為 {order}")

    save_topics_config()
    print("[REORDER] 順序已儲存到 topics_config.json")
    return jsonify({'status': 'ok'})

# ============ Main ============

def init_scheduler():
    scheduler = BackgroundScheduler(timezone='Asia/Taipei')
    # 30分鐘更新一次新聞
    scheduler.add_job(update_topic_news, 'interval', minutes=30)
    # AI 摘要：每天 8:00 和 18:00 執行
    scheduler.add_job(update_all_summaries, 'cron', hour=8, minute=0)
    scheduler.add_job(update_all_summaries, 'cron', hour=18, minute=0)
    scheduler.start()
    print("[SCHEDULER] 排程已啟動 - 新聞每30分鐘, 摘要每天08:00/18:00")

import urllib3
urllib3.disable_warnings()

# ============ 模組載入時初始化（Gunicorn 需要）============
load_topics_config()
load_data_cache()  # 先從快取載入資料（快速啟動）
init_scheduler()

if __name__ == '__main__':
    import threading
    import sys

    # 在背景線程執行初始化資料
    def background_init():
        print("[INIT] 背景更新資料...", flush=True)
        sys.stdout.flush()
        update_topic_news()
        if PERPLEXITY_API_KEY:
            print("[INIT] 生成 AI 摘要...", flush=True)
            sys.stdout.flush()
            update_all_summaries()
        print("[INIT] 背景更新完成", flush=True)
        sys.stdout.flush()

    # 啟動背景線程
    init_thread = threading.Thread(target=background_init, daemon=True)
    init_thread.start()

    print("[SERVER] 伺服器啟動中... (已載入快取資料，新資料將在背景更新)")
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

