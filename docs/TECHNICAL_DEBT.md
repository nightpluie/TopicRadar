# TopicRadar 技術債務與優化建議

**評估日期**: 2026-01-22  
**當前版本**: v2.1.0

---

## 目前程式碼現況

### 規模統計
- **app.py**: ~2,876 行
- **admin.html**: ~1,401 行
- **script.js**: ~566 行
- **index.html**: ~69 行
- **總計**: 約 4,900 行程式碼

### 架構特點
- 單一 Python 檔案（app.py）包含所有後端邏輯
- Vanilla JS（無框架）
- 混合式資料儲存（記憶體 + JSON 檔案 + Supabase）

---

## 技術債務清單

### 高優先級

#### 1. app.py 過於龐大（2,889 行）
**問題**：
- 所有後端邏輯集中在單一檔案
- 難以維護和測試
- 功能耦合度高

**影響**：
- 新功能開發困難
- Bug 修復風險高
- 程式碼可讀性差

**建議方案**：
```
app/
├── __init__.py
├── main.py          # Flask app 初始化
├── routes/          # API 路由
│   ├── api.py
│   ├── admin.py
│   └── auth.py
├── services/        # 業務邏輯
│   ├── news.py      # RSS 抓取
│   ├── ai.py        # AI 整合
│   └── keywords.py  # 關鍵字處理
├── models/          # 資料模型
│   └── topic.py
└── utils/           # 工具函數
    ├── translation.py
    └── scheduler.py
```

**備註**：需先建立測試框架再進行重構（v2.3 或 v3.0）

---

### 中優先級

#### 2. 缺乏單元測試
**問題**：
- 零測試覆蓋率
- 重構風險極高
- 難以驗證功能正確性

**建議方案**：
- 使用 pytest 建立測試框架
- 優先測試核心功能（RSS 抓取、關鍵字過濾）
- 目標：至少 50% 覆蓋率

**預估工作量**：v2.2 版本，約 4-6 小時

#### 3. 前端狀態管理混亂
**問題**：
- 全域變數散落各處
- DOM 操作直接耦合邏輯
- 難以除錯

**建議方案**：
- 考慮輕量級框架（Alpine.js 或 Petite Vue）
- 或建立簡單的狀態管理模式

**備註**：優先級較低，目前系統運作穩定

---

### 低優先級

#### 4. 缺少錯誤監控
**問題**：
- 只有 console.log
- 無法追蹤生產環境錯誤

**建議方案**：
- 整合 Sentry（免費方案）
- 或簡單的錯誤日誌系統

---

## 立即可執行的優化（Quick Wins）

以下三項優化**不需要大規模重構**，可以明天處理：

### 1. RSS 並行抓取（高效能提升）⭐

**目前狀況**：
- 逐一抓取 10 個台灣 RSS 來源
- 每個來源 2-5 秒
- 總耗時：20-50 秒

**優化方案**：
使用 `ThreadPoolExecutor` 並行處理

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_rss_parallel(sources_dict, max_workers=5):
    """並行抓取多個 RSS 來源"""
    all_news = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_source = {
            executor.submit(fetch_rss, url, name, max_items=50): name
            for name, url in sources_dict.items()
        }
        
        for future in as_completed(future_to_source, timeout=20):
            source_name = future_to_source[future]
            try:
                news_items = future.result()
                all_news.extend(news_items)
            except Exception as e:
                print(f"[PARALLEL] {source_name} 失敗: {e}")
    
    return all_news

# 使用方式：
all_news_tw = fetch_rss_parallel(RSS_SOURCES_TW, max_workers=5)
```

**預期效果**：
- 總耗時：10-15 秒
- 效能提升：**2-3 倍**
- 工作量：30-60 分鐘
- 風險：低

**修改位置**：
- `app.py` 約第 720 行：新增 `fetch_rss_parallel()` 函數
- `app.py` 第 1584-1585 行：修改 `update_domestic_news()`
- `app.py` 國際新聞處理：修改 `update_international_news()`

---

### 2. 環境變數驗證（減少配置錯誤）⭐

**目前狀況**：
- 啟動後才發現缺少 API Key
- 錯誤訊息不明確

**優化方案**：
```python
import sys

def validate_env():
    """啟動時驗證必要環境變數"""
    required = {
        'GEMINI_API_KEY': 'AI 關鍵字生成與翻譯',
        'PERPLEXITY_API_KEY': 'AI 摘要生成',
    }
    
    optional = {
        'SUPABASE_URL': '多使用者認證系統',
        'SUPABASE_KEY': '多使用者認證系統',
    }
    
    missing = []
    for key, desc in required.items():
        if not os.getenv(key):
            missing.append(f"  - {key} ({desc})")
    
    if missing:
        print("=" * 60)
        print("錯誤：缺少必要環境變數")
        print("=" * 60)
        print("\n".join(missing))
        print("\n請檢查 .env 檔案，參考 .env.example")
        print("=" * 60)
        sys.exit(1)
    
    # 顯示選用變數狀態
    print("[ENV] 環境變數檢查通過")
    for key, desc in optional.items():
        status = "✓" if os.getenv(key) else "✗"
        print(f"[ENV] {status} {key} ({desc})")

# 在 if __name__ == '__main__': 之前調用
if __name__ == '__main__':
    validate_env()  # 先驗證
    app.run(...)
```

**預期效果**：
- 立即發現配置問題
- 友善的錯誤訊息
- 避免執行時錯誤
- 工作量：20-30 分鐘
- 風險：極低

**修改位置**：
- `app.py` 約第 2860 行：新增 `validate_env()` 函數
- `app.py` 第 2885 行：在 `if __name__ == '__main__':` 前調用

---

### 3. API 錯誤處理統一（改善穩定性）⭐

**目前狀況**：
- 每個 API 端點自行處理錯誤
- 回應格式不一致
- 重複的錯誤處理程式碼

**優化方案**：
```python
from functools import wraps

def handle_api_errors(f):
    """統一 API 錯誤處理裝飾器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({
                'error': str(e),
                'code': 'INVALID_INPUT'
            }), 400
        except KeyError as e:
            return jsonify({
                'error': f'缺少必要參數: {str(e)}',
                'code': 'MISSING_PARAMETER'
            }), 400
        except Exception as e:
            print(f"[ERROR] {f.__name__}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': '伺服器內部錯誤',
                'code': 'INTERNAL_ERROR'
            }), 500
    return decorated

# 使用範例：
@app.route('/api/admin/topics', methods=['POST'])
@handle_api_errors  # 新增裝飾器
def add_topic():
    # 自動處理錯誤
    data = request.json
    name = data['name']  # KeyError 會被自動捕獲
    ...
```

**預期效果**：
- 統一錯誤格式
- 減少重複程式碼
- 更好的除錯體驗
- 自動記錄錯誤堆疊
- 工作量：1-2 小時
- 風險：低

**修改位置**：
- `app.py` 約第 2200 行：新增 `handle_api_errors()` 裝飾器
- 逐步為各 API 端點添加裝飾器（約 15-20 個端點）

---

---

## 效能優化建議

### 已完成優化（v2.1）
- ✅ 翻譯速度 3 倍提升（一次 API 請求翻譯三語）
- ✅ 新增專題 15 倍提升（背景執行緒處理）
- ✅ 前端自動刷新（每 5 分鐘輪詢）
- ✅ 資料持久化（Supabase topic_cache 表）

### 待優化項目

以上三個 Quick Wins 項目已納入技術債務文件，預計明天處理。

---

## 總結

### 已修正的項目
- ~~混合資料儲存~~：已使用 Supabase `topic_cache` 表持久化
- ~~前端自動刷新~~：已實作（每 5 分鐘 + 初次載入檢查）

### 技術債務優先順序
1. 🟢 **Quick Wins**（明天處理，3-4 小時）
   - RSS 並行抓取
   - 環境變數驗證
   - API 錯誤處理統一

2. 🟡 **測試框架**（v2.2，需先完成）

3. 🔴 **app.py 模組化**（v2.3-v3.0，需測試支援）

### 建議行動
1. **明天**：實作 Quick Wins（3-4 小時）
2. **v2.2**：建立測試框架，為重構鋪路
3. **v2.3**：漸進式模組化（AI 邏輯、RSS 邏輯分離）
4. **v3.0**：考慮使用 code-simplifier 進行大規模重構

### 是否使用 code-simplifier？
**建議等到 v2.3 或 v3.0**，當有完整測試覆蓋後再進行大規模重構。
