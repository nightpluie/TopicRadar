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
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

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

    // 國際新聞列表
    const intlNewsList = topicData.international || [];
    const intlNewsHtml = intlNewsList.length > 0
        ? intlNewsList.map(item => `
            <div class="news-item">
                <div class="news-meta">
                    <span class="news-time">${item.time || '--:--'}</span>
                    <span class="news-source">${item.source || '未知'}</span>
                </div>
                <a href="${item.link || '#'}" target="_blank" class="news-title">${item.title || '無標題'}</a>
            </div>
        `).join('')
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

    // 每 5 分鐘自動刷新
    setInterval(loadAllData, 5 * 60 * 1000);
});

// 載入進度檢查
let loadingCheckInterval = null;

function startLoadingStatusCheck() {
    checkLoadingStatus();
    loadingCheckInterval = setInterval(checkLoadingStatus, 2000);
}

async function checkLoadingStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/loading-status`);
        const status = await response.json();
        const statusEl = document.getElementById('loading-status');
        if (!statusEl) return;

        if (status.is_loading) {
            statusEl.textContent = `載入中 ${status.current}/${status.total}`;
            statusEl.className = 'status-loading';
        } else if (status.total > 0) {
            statusEl.textContent = '已載入';
            statusEl.className = 'status-loaded';
            // 載入完成後重新讀取資料
            await loadAllData();
        } else {
            statusEl.textContent = '等待載入';
            statusEl.className = '';
        }
    } catch (error) {
        console.error('[TopicRadar] 檢查載入狀態失敗:', error);
    }
}

// 暴露給 console 和按鈕使用
window.TopicRadar = {
    refresh: refreshNews,
    refreshSummary: refreshSummary,
    reload: loadAllData
};
