# 專題雷達 - Topic Radar
# Python 後端：RSS 抓取 + 關鍵字過濾 + AI 摘要 (Perplexity) + AI 關鍵字 (Claude)

import os
import re
import json
import time
import hashlib
import feedparser
import requests
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

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
    'The Japan Times': 'https://www.japantimes.co.jp/feed',
    'NHK (日文)': 'https://www3.nhk.or.jp/rss/news/cat0.xml',
    '朝日新聞 (日文)': 'http://rss.asahi.com/rss/asahi/newsheadlines.rdf',
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

TOPICS = {}

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

        current_time = datetime.now().strftime('%Y/%m/%d')
        
        payload = {
            "model": PERPLEXITY_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位資深專題記者，正在為已經熟悉議題背景的同事更新最新進展。請用「進度報告」的格式撰寫，假設讀者已了解議題背景，不需要重複說明基本概念或歷史脈絡。直接切入最新動態和變化。"
                },
                {
                    "role": "user",
                    "content": f"議題：{topic_name}\n日期：{current_time}\n\n請用進度報告格式，重點說明：\n1. 本週或近期有什麼新動態？（政策發布、協商進展、重要事件、爭議）\n2. 目前推進到什麼階段？有什麼關鍵進展或轉折？\n3. 接下來值得關注的焦點是什麼？\n\n格式要求：\n- 200 字以內，繁體中文\n- 用「進度更新」語氣，不是「議題介紹」\n- 不要使用引用標記（[1][2] 等）\n- 語氣專業、客觀、精簡"
                }
            ],
            "max_tokens": 500,
            "temperature": 0.2
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        
        data = response.json()
        summary = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # 移除可能的引用標記 [1], [2] 等
        summary = re.sub(r'\[\d+\]', '', summary)
        
        # 移除 markdown 格式符號（#、**、*、###等）
        summary = re.sub(r'^#{1,6}\s*', '', summary, flags=re.MULTILINE)  # 移除標題符號
        summary = re.sub(r'\*\*([^*]+)\*\*', r'\1', summary)  # 移除粗體 **text**
        summary = re.sub(r'\*([^*]+)\*', r'\1', summary)  # 移除斜體 *text*
        summary = re.sub(r'^[-*]\s+', '', summary, flags=re.MULTILINE)  # 移除列表符號
        
        return summary.strip() if summary else "（無法生成摘要）"
    
    except Exception as e:
        print(f"[ERROR] Perplexity 摘要失敗: {e}")
        return f"（摘要生成失敗）"

# ============ RSS 抓取 ============

def fetch_rss(url, source_name, timeout=15):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        items = []
        for entry in feed.entries[:30]:
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            else:
                published = datetime.now()
            
            items.append({
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'source': source_name,
                'published': published,
                'summary': entry.get('summary', '')[:200]
            })
        return items
    except Exception as e:
        print(f"[ERROR] 抓取 {source_name} 失敗: {e}")
        return []

def keyword_match(text, keywords):
    """關鍵字比對"""
    if not text or not keywords:
        return False
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False

def update_topic_news():
    print(f"\n[UPDATE] 開始更新新聞 - {datetime.now().strftime('%H:%M:%S')}")

    # 1. 抓取台灣新聞
    all_news_tw = []
    for name, url in RSS_SOURCES_TW.items():
        all_news_tw.extend(fetch_rss(url, name))

    # 2. 抓取國際新聞
    all_news_intl = []
    for name, url in RSS_SOURCES_INTL.items():
        all_news_intl.extend(fetch_rss(url, name))

    # 3. 過濾台灣新聞和國際新聞
    for tid, cfg in TOPICS.items():
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

        # 過濾台灣新聞（使用中文關鍵字）
        if not keywords_zh:
            DATA_STORE['topics'][tid] = []
        else:
            filtered_tw = []
            seen_tw = set()
            for item in all_news_tw:
                content = f"{item['title']} {item['summary']}"
                if keyword_match(content, keywords_zh):
                    h = hashlib.md5(item['title'].encode()).hexdigest()
                    if h not in seen_tw:
                        seen_tw.add(h)
                        filtered_tw.append(item)

            filtered_tw.sort(key=lambda x: x['published'], reverse=True)
            DATA_STORE['topics'][tid] = filtered_tw[:20]

        # 過濾國際新聞（使用英日文關鍵字）
        intl_keywords = keywords_en + keywords_ja
        if not intl_keywords:
            DATA_STORE['international'][tid] = []
        else:
            filtered_intl = []
            seen_intl = set()
            for item in all_news_intl:
                content = f"{item['title']} {item['summary']}"
                if keyword_match(content, intl_keywords):
                    h = hashlib.md5(item['title'].encode()).hexdigest()
                    if h not in seen_intl:
                        seen_intl.add(h)
                        # 翻譯標題（加入延遲避免 API 速率限制）
                        original_title = item['title']
                        translated_title = translate_with_gemini(original_title)
                        item['title_original'] = original_title
                        item['title'] = translated_title
                        filtered_intl.append(item)
                        time.sleep(0.5)  # 每次翻譯後等待 0.5 秒

            filtered_intl.sort(key=lambda x: x['published'], reverse=True)
            DATA_STORE['international'][tid] = filtered_intl[:10]

    DATA_STORE['last_update'] = datetime.now().isoformat()
    print("[UPDATE] 完成")
    # 摘要更新改用排程（每天 8:00 和 18:00），不在新聞更新時觸發

def update_all_summaries():
    print(f"\n[SUMMARY] 開始 AI 摘要...")
    for tid in TOPICS.keys():
        summary = generate_topic_summary(tid)
        DATA_STORE['summaries'][tid] = {
            'text': summary,
            'updated_at': datetime.now().isoformat()
        }
        time.sleep(1)
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
        for n in news[:10]:
            dt = n['published']
            now = datetime.now()
            if dt.date() == now.date():
                time_str = dt.strftime('%H:%M')
            else:
                time_str = dt.strftime('%m/%d')

            fmt_news.append({
                'title': n['title'],
                'link': n['link'],
                'source': n['source'],
                'time': time_str
            })

        # 格式化國際新聞
        fmt_intl_news = []
        for n in intl_news[:5]:
            dt = n['published']
            now = datetime.now()
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
            'international': fmt_intl_news
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
            'icon': cfg.get('icon', ''),
            'summary': summary_data.get('text', ''),
            'summary_updated': summary_data.get('updated_at'),
            'news_count': news_count
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
    
    tid = generate_topic_id(name)
    TOPICS[tid] = {'name': name, 'keywords': keywords}
    save_topics_config()
    
    # 立即更新該專題新聞
    update_topic_news()
    
    return jsonify({'status': 'ok'})

@app.route('/api/admin/topics/<tid>', methods=['PUT'])
def update_topic(tid):
    if tid not in TOPICS:
        return jsonify({'error': 'Not found'}), 404
    data = request.json
    if 'keywords' in data:
        TOPICS[tid]['keywords'] = data['keywords']
    save_topics_config()
    update_topic_news()
    return jsonify({'status': 'ok'})

@app.route('/api/admin/topics/<tid>', methods=['DELETE'])
def delete_topic(tid):
    if tid in TOPICS:
        del TOPICS[tid]
        save_topics_config()
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
init_scheduler()

if __name__ == '__main__':
    print("[INIT] 初始化資料...")
    update_topic_news()
    
    if PERPLEXITY_API_KEY:
        # 啟動時自動生成摘要
        print("[INIT] 生成 AI 摘要...")
        update_all_summaries() 
        
    app.run(port=5001, debug=True, use_reloader=False)

