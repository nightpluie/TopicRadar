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

// 生成單個專題卡片的 HTML
function createTopicCard(topicId, topicData) {
    const card = document.createElement('div');
    card.className = 'topic-card';
    card.dataset.topicId = topicId;

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

    card.innerHTML = `
        <div class="topic-header">
            <div class="topic-name">${topicData.name || '未命名專題'}</div>
        </div>
        <div class="topic-keywords">${keywordDisplay}</div>

        <div class="ai-summary">
            <div class="section-label">
                <span>最新進展摘要</span>
                <span class="update-badge">${getUpdateBadgeText(topicData.summary_updated)}</span>
            </div>
            <div class="summary-content">
                ${topicData.summary || '（載入中...）'}
            </div>
        </div>

        <div class="news-list">
            <div class="section-label">
                <span>相關資訊動態</span>
            </div>
            <div class="news-feed">
                ${newsHtml}
            </div>
        </div>

        <div class="intl-news-list">
            <div class="section-label">
                <span>國際相關報導</span>
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

        // 動態生成每個專題卡片
        topicIds.forEach(topicId => {
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
    try {
        const response = await fetch(`${API_BASE}/api/refresh-summary`, { method: 'POST' });
        if (response.ok) {
            console.log('[TopicRadar] AI 摘要已刷新');
            await loadAllData();
        }
    } catch (error) {
        console.error('[TopicRadar] 摘要刷新失敗:', error);
    }
}

// 初始載入
document.addEventListener('DOMContentLoaded', () => {
    console.log('[TopicRadar] 專題雷達啟動中...');
    loadAllData();

    // 每 5 分鐘自動刷新
    setInterval(loadAllData, 5 * 60 * 1000);
});

// 暴露給 console 和按鈕使用
window.TopicRadar = {
    refresh: refreshNews,
    refreshSummary: refreshSummary,
    reload: loadAllData
};
