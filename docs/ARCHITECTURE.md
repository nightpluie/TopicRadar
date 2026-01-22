# TopicRadar 系統架構說明

這份文件說明了 TopicRadar 的運作原理、各個元件如何互動，以及它們在系統中的角色。

## 系統架構圖 (System Architecture)

```mermaid
graph TD
    User((使用者))
    
    subgraph Frontend [前端 (瀏覽器)]
        UI[網頁介面<br/>index.html / script.js]
    end

    subgraph DevTools [開發與部署]
        Git[GitHub<br/>原始碼管理]
    end

    subgraph Hosting [Render 雲端平台]
        Server[後端伺服器<br/>app.py (Flask)]
        Cache[快取檔案<br/>data_cache.json]
        Scheduler[排程器<br/>(每30分更新)]
    end

    subgraph Database [Supabase]
        AuthDB[(身分認證<br/>Auth Users)]
        ConfigDB[(專題設定<br/>Topics & Settings)]
    end

    subgraph External [外部資源]
        RSS[新聞來源<br/>RSS / Google News]
        AI[AI 模型<br/>Claude / Gemini / Perplexity]
    end

    %% 互動關係
    User <-->|瀏覽網站| UI
    UI <-->|API 请求 (獲取新聞)| Server
    
    %% 開發流程
    User -- "推送到 (Push)" --> Git
    Git -- "自動部署 (Auto Deploy)" --> Hosting
    
    Server <-->|驗證身分 & 讀取設定| Database
    Server <-->|讀寫快取| Cache
    
    Scheduler -->|1. 抓取新聞| RSS
    Scheduler -->|2. 處理與摘要| AI
    Scheduler -->|3. 更新結果| Cache
```

## 核心元件介紹

### 1. 前端 (Frontend)
*   **檔案**：`index.html`, `script.js`, `style.css`
*   **角色**：這是使用者的操作介面。它不負責儲存資料，而是透過 API 向後端請求資料並顯示。
*   **行為**：當你打開網頁時，`script.js` 會向後端發送 `/api/all` 請求，拿到新聞資料後，動態產生那些「專題卡片」。

----------------------------------------------------------------

### 2. 後端與託管 (Backend & Render)
*   **檔案**：`app.py`
*   **平台**：**Render**
*   **角色**：這是整個系統的「大腦」。
*   **它做了什麼**：
    1.  **提供 API**：回應前端的請求 (例如：「給我所有新聞」)。
    2.  **執行排程**：即使沒人上網，它也在背景默不做聲地工作（每 30 分鐘去抓一次新聞）。
    3.  **整合 AI**：把抓來的新聞丟給 Claude 或 Perplexity 進行摘要或關鍵字分析。

> **關於 Render**：
> Render 是一個雲端託管平台 (Hosting Platform)。它就像是一台永不關機的電腦，負責執行你的 `app.py`。
> *   單機版：是你電腦上的 Python 在跑 `app.py`。
> *   線上版：是 Render 的伺服器在跑 `app.py`。

----------------------------------------------------------------

### 3. 資料庫與設定 (Supabase)
*   **角色**：這是系統的「長期記憶」。
*   **為什麼需要它**：如果只靠 Render，每次重開機資料可能會遺失（或是難以管理多個使用者）。Supabase 專門用來記住「誰是誰」以及「誰想看什麼」。
*   **儲存內容**：
    1.  **使用者帳號 (Auth)**：Email、密碼、登入 Token。
    2.  **專題設定 (Topics)**：每個使用者設定了哪些關鍵字（例如：A使用者看「半導體」，B使用者看「房地產」）。
    3.  **邀請碼 (Invites)**：控制誰可以註冊。

----------------------------------------------------------------

### 4. 資料快取 (Data Cache)
*   **檔案**：`data_cache.json`
*   **角色**：這是系統的「短期記憶」或「暫存區」。
*   **運作方式**：
    *   新聞資料**不存**在 Supabase，因為新聞量大且更新快，存資料庫太慢且昂貴。
    *   後端抓到新聞後，會直接寫入這個 JSON 檔案。
    *   當使用者打開網頁時，後端直接讀取這個檔案回傳，速度最快。
    *   **剛才修復的問題**：就是後端有讀到這個檔案，但沒有正確把你的那份資料拿出來，導致系統以為你是空的。

----------------------------------------------------------------

### 5. 程式碼託管 (GitHub)
*   **角色**：這是系統的「設計圖倉庫」兼「發令台」。
*   **功能**：
    1.  **備份程式碼**：我們所有寫的程式碼 (`app.py`, `script.js` 等) 都安全地存放在這裡。
    2.  **觸發更新**：當我們把修正好的程式碼「推送 (Push)」到 GitHub 時，GitHub 會通知 Render：「有新版本了！」Render 就會自動去抓新程式碼並重新啟動伺服器。這就是為什麼我們剛剛 `git push` 之後，線上的網站也會跟著修好。

----------------------------------------------------------------

## 資料流：從新聞發生到你看見的過程

1.  **蒐集 (Collection)**：
    Render 上的排程器啟動，去各大新聞網站 (RSS) 和 Google News 抓取最新文章。

2.  **過濾 (Filtering)**：
    程式會去 **Supabase** 查閱你的「關鍵字設定」，然後把不相關的新聞丟掉，只留下你感興趣的。

3.  **處理 (Processing)**：
    如果需要摘要，程式會呼叫 **Perplexity/Claude** 的 API 來幫忙寫摘要。

4.  **儲存 (Caching)**：
    整理好的結果被寫入 `data_cache.json`。

5.  **呈現 (Serving)**：
    你打開網站 -> 前端呼叫 API -> 後端讀取 `data_cache.json` -> 立刻顯示在你的螢幕上。
