/**
 * DocuGen AI 可视化界面主要JavaScript文件
 * 实现数据获取、状态更新和界面交互功能
 */

// 状态更新间隔（毫秒）
const STATUS_UPDATE_INTERVAL = 1000;

// DOM元素缓存
const elements = {
    projectName: document.getElementById('project-name'),
    progressPercentage: document.getElementById('progress-percentage'),
    progressValue: document.getElementById('progress-value'),
    generationStatus: document.getElementById('generation-status'),
    documentsList: document.getElementById('documents-list'),
    consoleOutput: document.getElementById('console-output')
};

// 状态映射
const statusMap = {
    'ready': '准备就绪',
    'generating': '生成中',
    'completed': '已完成',
    'failed': '失败',
    'paused': '已暂停'
};

// 文档状态映射
const documentStatusMap = {
    'pending': '待处理',
    'generating': '生成中',
    'completed': '已完成',
    'failed': '失败'
};

// 全局状态数据
let currentStatus = null;

/**
 * 初始化应用
 */
function init() {
    // 首次加载状态
    fetchStatus();
    
    // 设置定时刷新
    setInterval(fetchStatus, STATUS_UPDATE_INTERVAL);
    
    // 添加控制台初始消息
    addConsoleMessage('Web可视化界面初始化完成', 'info');
}

/**
 * 从服务器获取状态数据
 */
async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        const data = await response.json();
        updateUI(data);
    } catch (error) {
        console.error('获取状态失败:', error);
        addConsoleMessage(`获取状态失败: ${error.message}`, 'error');
    }
}

/**
 * 更新用户界面
 * @param {Object} data - 状态数据
 */
function updateUI(data) {
    // 如果数据没有变化，则不更新UI
    if (currentStatus && JSON.stringify(currentStatus) === JSON.stringify(data)) {
        return;
    }
    
    // 更新当前状态
    currentStatus = data;
    
    // 更新项目名称
    elements.projectName.textContent = data.project_name || '未命名项目';
    
    // 更新进度
    elements.progressPercentage.textContent = `${data.progress}%`;
    elements.progressValue.style.width = `${data.progress}%`;
    
    // 更新状态
    const statusText = statusMap[data.status] || data.status;
    elements.generationStatus.textContent = statusText;
    
    // 清除所有状态类
    Object.keys(statusMap).forEach(status => {
        elements.generationStatus.classList.remove(status);
    });
    
    // 添加当前状态类
    elements.generationStatus.classList.add(data.status);
    
    // 更新文档列表
    updateDocumentsList(data.documents);
    
    // 更新控制台消息
    updateConsoleMessages(data.messages);
}

/**
 * 更新文档列表
 * @param {Array} documents - 文档状态数组
 */
function updateDocumentsList(documents) {
    if (!documents || documents.length === 0) {
        return;
    }
    
    // 清空列表（移除骨架屏）
    elements.documentsList.innerHTML = '';
    
    // 添加每个文档
    documents.forEach(doc => {
        const listItem = document.createElement('li');
        listItem.className = 'document-item';
        
        const statusLabel = documentStatusMap[doc.status] || doc.status;
        
        listItem.innerHTML = `
            <span class="document-name">${doc.name}</span>
            <span class="document-status status-${doc.status}">${statusLabel}</span>
        `;
        
        elements.documentsList.appendChild(listItem);
    });
}

/**
 * 更新控制台消息
 * @param {Array} messages - 消息数组
 */
function updateConsoleMessages(messages) {
    if (!messages || messages.length === 0) {
        return;
    }
    
    // 获取当前已有的消息数量
    const currentMessageCount = elements.consoleOutput.querySelectorAll('.console-message').length;
    
    // 如果有新消息才更新
    if (messages.length > currentMessageCount - 1) { // -1是因为初始有一条系统消息
        // 清空控制台（保留初始化消息）
        elements.consoleOutput.innerHTML = '';
        
        // 添加所有消息
        messages.forEach(msg => {
            addConsoleMessage(msg.text, msg.level, msg.time);
        });
        
        // 滚动到底部
        elements.consoleOutput.scrollTop = elements.consoleOutput.scrollHeight;
    }
}

/**
 * 添加控制台消息
 * @param {string} text - 消息文本
 * @param {string} level - 消息级别（info, success, warning, error）
 * @param {string} time - 时间戳（可选）
 */
function addConsoleMessage(text, level = 'info', time = null) {
    // 如果没有提供时间，则使用当前时间
    if (!time) {
        const now = new Date();
        time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    }
    
    const messageElement = document.createElement('div');
    messageElement.className = `console-message ${level}`;
    
    messageElement.innerHTML = `
        <span class="time">${time}</span>
        <span class="text">${text}</span>
    `;
    
    elements.consoleOutput.appendChild(messageElement);
    elements.consoleOutput.scrollTop = elements.consoleOutput.scrollHeight;
}

// 初始化应用
document.addEventListener('DOMContentLoaded', init); 