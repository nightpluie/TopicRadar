// 專題雷達 - Topic Radar
// 前端互動腳本

const API_BASE = '';

// 更新最後更新時間顯示
function updateLastUpdateDisplay(timestamp) {
    const el = document.getElementById('last-update');
    if (!el) return;

    if (!timestamp) {
        el.textContent = '--';
        return;
    }

    const date = new Date(timestamp);
    el.textContent = date.toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

// 即時時鐘更新
function updateRealtimeClock() {
    const el = document.getElementById('realtime-clock');
    if (!el) return;

    const now = new Date();
    el.textContent = now.toLocaleTimeString('zh-TW', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

// 全螢幕切換
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.error('[TopicRadar] 無法進入全螢幕:', err);
        });
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

// 更新全螢幕按鈕圖示
function updateFullscreenIcon() {
    const btn = document.getElementById('fullscreen-btn');
    if (!btn) return;

    const expandIcon = btn.querySelector('.expand-icon');
    const compressIcon = btn.querySelector('.compress-icon');

    if (document.fullscreenElement) {
        // 全螢幕狀態：顯示收縮圖示
        if (expandIcon) expandIcon.style.display = 'none';
        if (compressIcon) compressIcon.style.display = 'block';
        btn.title = '退出全螢幕';
    } else {
        // 非全螢幕狀態：顯示擴展圖示
        if (expandIcon) expandIcon.style.display = 'block';
        if (compressIcon) compressIcon.style.display = 'none';
        btn.title = '全螢幕模式';
    }
}

// 監聽全螢幕狀態變化
document.addEventListener('fullscreenchange', updateFullscreenIcon);

// 計算摘要更新時間差
function getUpdateBadgeText(timestamp) {
    if (!timestamp) return '等待更新';

    const updatedAt = new Date(timestamp);
    const now = new Date();
    const diffMinutes = Math.floor((now - updatedAt) / 60000);

    if (diffMinutes < 1) return '剛剛更新';
    if (diffMinutes < 60) return `${diffMinutes}分鐘前`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}小時前`;
    return `${Math.floor(diffMinutes / 1440)}天前`;
}

// 追蹤每個專題的新聞數量
let topicNewsCount = {};
let topicIntlNewsCount = {};

// 生成單個專題卡片的 HTML
function createTopicCard(topicId, topicData) {
    const card = document.createElement('div');
    card.className = 'topic-card';
    card.dataset.topicId = topicId;
    // 預設不可拖動，只有從 drag-handle 開始拖動時才啟用
    card.draggable = false;

    // 檢查是否有新新聞（國內動態）
    const currentNewsCount = (topicData.news || []).length;
    const previousCount = topicNewsCount[topicId] || 0;
    const hasNewNews = currentNewsCount > previousCount;
    topicNewsCount[topicId] = currentNewsCount;

    // 檢查是否有新國際報導
    const intlNews = topicData.international || [];
    const currentIntlCount = intlNews.length;
    const previousIntlCount = topicIntlNewsCount[topicId] || 0;
    const hasNewIntl = currentIntlCount > previousIntlCount;

    // Debug: 打印國際新聞追蹤信息
    console.log(`[${topicData.name}] 國際報導: 之前=${previousIntlCount}, 現在=${currentIntlCount}, 變紅=${hasNewIntl}`);

    topicIntlNewsCount[topicId] = currentIntlCount;

    // 關鍵字標籤 - 改為逗號分隔格式
    const keywords = (topicData.keywords || []).slice(0, 8).join('、');
    const keywordDisplay = keywords ? `關鍵字：${keywords}` : '無關鍵字';

    // 新聞列表
    const newsList = topicData.news || [];
    const newsHtml = newsList.length > 0
        ? newsList.map(item => `
            <div class="news-item">
                <div class="news-meta">
                    <span class="news-time">${item.time || '--:--'}</span>
                    <span class="news-source">${item.source || '未知'}</span>
                </div>
                <a href="${item.link || '#'}" target="_blank" class="news-title">${item.title || '無標題'}</a>
            </div>
        `).join('')
        : '<div class="news-item empty">目前沒有相關新聞</div>';

    // 國際新聞列表（含原文標題）
    const intlNewsList = topicData.international || [];
    const intlNewsHtml = intlNewsList.length > 0
        ? intlNewsList.map(item => {
            const originalTitle = item.title_original ?
                `<span class="news-title-original">${item.title_original}</span>` : '';
            return `
            <div class="news-item">
                <div class="news-meta">
                    <span class="news-time">${item.time || '--:--'}</span>
                    <span class="news-source">${item.source || '未知'}</span>
                </div>
                <a href="${item.link || '#'}" target="_blank" class="news-title">${item.title || '無標題'}</a>
                ${originalTitle}
            </div>
        `;
        }).join('')
        : '<div class="news-item empty">目前沒有相關國際報導</div>';

    // 清理摘要的開頭空行（多重清理）
    let cleanSummary = topicData.summary || '（載入中...）';
    // 移除開頭所有空白字符（包括空格、tab、換行）
    cleanSummary = cleanSummary.replace(/^[\s\n\r\t]+/g, '');
    // 移除結尾所有空白字符
    cleanSummary = cleanSummary.replace(/[\s\n\r\t]+$/g, '');
    // 使用 trim 最後確保
    cleanSummary = cleanSummary.trim();
    // 如果第一個字符還是空白，逐字符移除
    while (cleanSummary && /\s/.test(cleanSummary[0])) {
        cleanSummary = cleanSummary.substring(1);
    }

    card.innerHTML = `
        <div class="drag-handle">⋮⋮</div>
        <div class="topic-header">
            <div class="topic-name ${hasNewNews ? 'news-updated' : ''}">${topicData.name || '未命名專題'}</div>
        </div>
        <div class="topic-keywords">${keywordDisplay}</div>

        <div class="ai-summary">
            <div class="section-label">
                <span>最新進展與關注焦點</span>
                <span class="update-badge">${getUpdateBadgeText(topicData.summary_updated)}</span>
            </div>
            <div class="summary-content">
                ${cleanSummary}
            </div>
        </div>

        <div class="news-list">
            <div class="section-label ${hasNewNews ? 'news-updated' : ''}">
                <span>國內動態</span>
            </div>
            <div class="news-feed">
                ${newsHtml}
            </div>
        </div>

        <div class="intl-news-list">
            <div class="section-label ${hasNewIntl ? 'news-updated' : ''}">
                <span>國際報導</span>
            </div>
            <div class="intl-news-feed">
                ${intlNewsHtml}
            </div>
        </div>
    `;

    // 綁定拖動事件
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);
    card.addEventListener('dragenter', handleDragEnter);
    card.addEventListener('dragover', handleDragOver);
    card.addEventListener('dragleave', handleDragLeave);
    card.addEventListener('drop', handleDrop);

    // 只有從 drag-handle 開始拖動時才啟用 draggable
    const dragHandle = card.querySelector('.drag-handle');
    if (dragHandle) {
        dragHandle.addEventListener('mousedown', () => {
            card.draggable = true;
        });
        dragHandle.addEventListener('mouseup', () => {
            card.draggable = false;
        });
    }

    // 當拖動結束後重設 draggable
    card.addEventListener('dragend', () => {
        card.draggable = false;
    });

    return card;
}

// 載入所有資料並動態生成專題卡片
async function loadAllData() {
    const container = document.getElementById('dashboard-container');

    try {
        const response = await fetch(`${API_BASE}/api/all`);
        if (!response.ok) throw new Error('API 錯誤');

        const data = await response.json();
        const topics = data.topics || {};
        const topicIds = Object.keys(topics);

        // 更新最後更新時間
        updateLastUpdateDisplay(data.last_update);

        // 更新專題數量
        const countEl = document.getElementById('topic-count');
        if (countEl) countEl.textContent = topicIds.length;

        // 清空容器
        container.innerHTML = '';

        // 排序專題（按 order 欄位）
        const sortedTopicIds = topicIds.sort((a, b) => {
            const orderA = topics[a].order || 999;
            const orderB = topics[b].order || 999;
            return orderA - orderB;
        });

        // 動態生成每個專題卡片
        sortedTopicIds.forEach(topicId => {
            const topicData = topics[topicId];
            const card = createTopicCard(topicId, topicData);
            container.appendChild(card);
        });

        // 如果沒有專題
        if (topicIds.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-text">尚未設定任何專題</div>
                    <a href="/admin" class="empty-action">前往後台新增專題</a>
                </div>
            `;
        }

        console.log('[TopicRadar] 資料載入完成，共 ' + topicIds.length + ' 個專題');

    } catch (error) {
        console.error('[TopicRadar] 載入失敗:', error);
        container.innerHTML = `
            <div class="error-state">
                <div class="error-text">載入失敗，請確認伺服器是否運行中</div>
                <button onclick="loadAllData()" class="retry-btn">重試</button>
            </div>
        `;
    }
}

// 手動刷新新聞
async function refreshNews() {
    const btn = document.querySelector('.btn-refresh');
    if (btn) {
        btn.textContent = '更新中...';
        btn.disabled = true;
    }

    try {
        const response = await fetch(`${API_BASE}/api/refresh`, { method: 'POST' });
        if (response.ok) {
            console.log('[TopicRadar] 新聞已刷新');
            await loadAllData();
        }
    } catch (error) {
        console.error('[TopicRadar] 刷新失敗:', error);
    } finally {
        if (btn) {
            btn.textContent = '更新';
            btn.disabled = false;
        }
    }
}

// 手動刷新 AI 摘要
async function refreshSummary() {
    const btn = document.querySelector('.btn-refresh-summary');
    if (btn) {
        btn.textContent = '更新中...';
        btn.disabled = true;
    }

    try {
        const response = await fetch(`${API_BASE}/api/refresh-summary`, { method: 'POST' });
        if (response.ok) {
            console.log('[TopicRadar] AI 摘要已刷新');
            await loadAllData();
        }
    } catch (error) {
        console.error('[TopicRadar] 摘要刷新失敗:', error);
    } finally {
        if (btn) {
            btn.textContent = '更新摘要';
            btn.disabled = false;
        }
    }
}

// 初始載入
document.addEventListener('DOMContentLoaded', () => {
    console.log('[TopicRadar] 專題雷達啟動中...');
    loadAllData();
    startLoadingStatusCheck();

    // 即時時鐘啟動
    updateRealtimeClock();
    setInterval(updateRealtimeClock, 1000);

    // 每 5 分鐘自動刷新
    setInterval(loadAllData, 5 * 60 * 1000);
});

// 載入進度檢查
let loadingCheckInterval = null;

function startLoadingStatusCheck() {
    checkLoadingStatus();
    loadingCheckInterval = setInterval(checkLoadingStatus, 2000);
}

let lastLoadingStatus = null;

async function checkLoadingStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/loading-status`);
        const status = await response.json();
        const statusEl = document.getElementById('loading-status');
        if (!statusEl) return;

        if (status.is_loading) {
            statusEl.textContent = `載入中 ${status.current}/${status.total}`;
            statusEl.className = 'status-loading';
            lastLoadingStatus = 'loading';
        } else if (status.total > 0) {
            statusEl.textContent = '已載入';
            statusEl.className = 'status-loaded';

            // 只在從「載入中」變成「已載入」時才重新讀取資料
            if (lastLoadingStatus === 'loading') {
                await loadAllData();
                lastLoadingStatus = 'loaded';
            }
        } else {
            statusEl.textContent = '等待載入';
            statusEl.className = '';
            lastLoadingStatus = null;
        }
    } catch (error) {
        console.error('[TopicRadar] 檢查載入狀態失敗:', error);
    }
}

// 暴露給 console 和按鈕使用
window.TopicRadar = {
    refresh: refreshNews,
    refreshSummary: refreshSummary,
    reload: loadAllData,
    toggleFullscreen: toggleFullscreen
};

// ============ 拖動排序功能 ============
let draggedElement = null;

function handleDragStart(e) {
    draggedElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
}

function handleDragEnd(e) {
    this.classList.remove('dragging');

    // 移除所有 drag-over class
    document.querySelectorAll('.drag-over').forEach(el => {
        el.classList.remove('drag-over');
    });

    // 儲存新順序
    saveNewOrder();
}

function handleDragEnter(e) {
    if (this.classList.contains('topic-card') && this !== draggedElement) {
        this.classList.add('drag-over');
    }
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDragLeave(e) {
    if (e.target === this) {
        this.classList.remove('drag-over');
    }
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();

    if (this !== draggedElement && this.classList.contains('topic-card')) {
        this.classList.remove('drag-over');

        // 真正的交換邏輯（swap）
        const container = document.getElementById('dashboard-container');

        // 記錄兩個元素的位置
        const draggedNext = draggedElement.nextSibling;
        const targetNext = this.nextSibling;

        if (draggedNext === this) {
            // 相鄰的情況：dragged 在 target 前面
            container.insertBefore(this, draggedElement);
        } else if (targetNext === draggedElement) {
            // 相鄰的情況：target 在 dragged 前面
            container.insertBefore(draggedElement, this);
        } else {
            // 不相鄰的情況：先用 placeholder 佔位
            const placeholder = document.createElement('div');
            container.insertBefore(placeholder, this);
            container.insertBefore(this, draggedNext === null ? null : draggedNext);
            container.insertBefore(draggedElement, placeholder);
            container.removeChild(placeholder);
        }
    }

    return false;
}

// 儲存新的排序到後端
async function saveNewOrder() {
    const allCards = Array.from(document.querySelectorAll('.topic-card'));
    const newOrder = allCards.map((card, index) => ({
        id: card.dataset.topicId,
        order: index
    }));

    console.log('[TopicRadar] 準備儲存新順序:', newOrder);

    try {
        const response = await fetch(`${API_BASE}/api/admin/topics/reorder`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order: newOrder })
        });

        if (response.ok) {
            const result = await response.json();
            console.log('[TopicRadar] 排序已儲存成功:', result);
        } else {
            const error = await response.text();
            console.error('[TopicRadar] 排序儲存失敗:', error);
            await loadAllData(); // 重新載入復原
        }
    } catch (error) {
        console.error('[TopicRadar] 排序儲存錯誤:', error);
        await loadAllData(); // 重新載入復原
    }
}
