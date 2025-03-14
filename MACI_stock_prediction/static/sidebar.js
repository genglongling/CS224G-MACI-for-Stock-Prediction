// sidebar.js - 侧边栏功能

// 在文档加载完成后初始化侧边栏
document.addEventListener('DOMContentLoaded', function() {
    // 初始化侧边栏
    initSidebar();
    
    // 如果在generate_agent.html页面
    if (window.location.pathname.includes('generate_agent.html')) {
        // 检查是否有预设Agent需要加载
        const agentIdToLoad = sessionStorage.getItem('load_agent_id');
        if (agentIdToLoad) {
            // 调用script.js中的函数加载Agent
            if (typeof window.loadSavedAgent === 'function') {
                window.loadSavedAgent(agentIdToLoad);
            }
            
            // 清除sessionStorage中的ID，避免下次加载页面时再次加载
            sessionStorage.removeItem('load_agent_id');
            sessionStorage.removeItem('agent_edit_mode');
        }
        
        // 添加"Create New"按钮
        addCreateNewAgentMenu();
    }
});

// 初始化侧边栏
function initSidebar() {
    // 检查页面上是否已经有侧边栏元素
    if (document.getElementById('app-sidebar')) {
        console.log('Sidebar already exists');
        return;
    }
    
    // 创建侧边栏HTML
    createSidebarHTML();
    
    // 添加事件监听器
    addSidebarEventListeners();
    
    // 加载保存的Agent列表
    loadSavedAgentsToSidebar();
}

// 创建侧边栏HTML
function createSidebarHTML() {
    // 创建侧边栏容器
    const sidebar = document.createElement('div');
    sidebar.id = 'app-sidebar';
    sidebar.className = 'sidebar';
    
    // 侧边栏内容
    sidebar.innerHTML = `
        <div class="sidebar-header">
            <h3>MACI Menu</h3>
            <button class="sidebar-close">&times;</button>
        </div>
        
        <div class="user-info">
            <div class="user-avatar">
                <span>D</span>
            </div>
            <div class="user-details">
                <div class="user-name">Demo User</div>
                <div class="user-email">demo@example.com</div>
            </div>
        </div>
        
        <ul class="sidebar-menu">
            <li id="create-agent-menu" onclick="navigateTo('generate_agent.html')">
                <i>🔧</i> Create New Agent
            </li>
            <li id="agent-settings-menu" onclick="toggleSavedAgentsList()">
                <i>⚙️</i> Settings
                <div class="saved-agents-dropdown" id="saved-agents-list">
                    <div class="saved-agent-loading">Loading agents...</div>
                </div>
            </li>
            <li id="new-workspace-menu" onclick="openAgentSelectionModal()">
                <i>🚀</i> New Workspace
            </li>
        </ul>
    `;
    
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.id = 'sidebar-overlay';
    overlay.className = 'sidebar-overlay';
    
    // 创建用户头像按钮
    const header = document.querySelector('.header');
    if (header) {
        const avatarBtn = document.createElement('button');
        avatarBtn.className = 'user-avatar-btn';
        avatarBtn.id = 'user-avatar-btn';
        avatarBtn.innerHTML = 'D';
        avatarBtn.setAttribute('title', 'Menu');
        header.appendChild(avatarBtn);
    } else {
        console.warn('Header element not found');
    }
    
    // 添加到文档
    document.body.appendChild(sidebar);
    document.body.appendChild(overlay);
    
    // 添加Agent选择模态框
    createAgentSelectionModal();
}

// 添加侧边栏事件监听器
function addSidebarEventListeners() {
    // 用户头像按钮点击事件
    const avatarBtn = document.getElementById('user-avatar-btn');
    if (avatarBtn) {
        avatarBtn.addEventListener('click', toggleSidebar);
    }
    
    // 关闭按钮点击事件
    const closeBtn = document.querySelector('.sidebar-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', toggleSidebar);
    }
    
    // 遮罩层点击事件
    const overlay = document.getElementById('sidebar-overlay');
    if (overlay) {
        overlay.addEventListener('click', toggleSidebar);
    }
}

// 切换侧边栏显示/隐藏
function toggleSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    
    if (sidebar && overlay) {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }
}

// 页面导航
function navigateTo(url) {
    window.location.href = url;
}

// 切换已保存Agent列表显示/隐藏
function toggleSavedAgentsList() {
    const agentsList = document.getElementById('saved-agents-list');
    
    if (agentsList) {
        agentsList.classList.toggle('active');
        
        // 如果打开列表，则加载Agent
        if (agentsList.classList.contains('active')) {
            loadSavedAgentsToSidebar();
        }
    }
}

// 加载保存的Agent列表到侧边栏
async function loadSavedAgentsToSidebar() {
    const agentsList = document.getElementById('saved-agents-list');
    if (!agentsList) return;
    
    agentsList.innerHTML = '<div class="saved-agent-loading">Loading agents...</div>';
    
    try {
        // 使用script.js中的函数，如果可用
        const agents = typeof window.listSavedAgents === 'function' 
            ? await window.listSavedAgents() 
            : await listSavedAgentsInternal();
        
        if (agents.length === 0) {
            agentsList.innerHTML = '<div class="saved-agent-loading">No saved agents found</div>';
            return;
        }
        
        // 创建Agent列表HTML
        let html = '';
        
        agents.forEach(agent => {
            const features = agent.features && agent.features.length > 0 
                ? agent.features.join(', ') 
                : 'No special features';
            
            html += `
                <div class="saved-agent-item" onclick="handleAgentSelection('${agent.id}')">
                    <div class="saved-agent-name">${agent.name || 'Unnamed Agent'}</div>
                    <div class="saved-agent-details">${agent.model || 'Unknown model'} | ${features}</div>
                </div>
            `;
        });
        
        agentsList.innerHTML = html;
        
    } catch (error) {
        console.error("Error loading saved agents:", error);
        agentsList.innerHTML = '<div class="saved-agent-loading">Error loading agents</div>';
    }
}

// 内部实现的列出Agent函数，以防script.js的函数不可用
async function listSavedAgentsInternal() {
    try {
        const response = await fetch('/list_saved_agents');
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            return data.agents;
        } else {
            console.error("Error listing agents:", data.error);
            return [];
        }
    } catch (error) {
        console.error("Error listing agents:", error);
        return [];
    }
}

// 处理Agent选择
function handleAgentSelection(agentId) {
    const currentPage = window.location.pathname.split('/').pop();
    
    // 根据当前页面决定行为
    if (currentPage === 'generate_agent.html') {
        // 在生成页面，使用script.js中的函数加载Agent配置
        if (typeof window.loadSavedAgent === 'function') {
            window.loadSavedAgent(agentId);
        }
    } else {
        // 根据用户点击来源确定行为
        const clickSource = event.target.closest('li') ? event.target.closest('li').id : '';
        
        if (clickSource === 'agent-settings-menu' || 
            event.target.closest('#saved-agents-list')) {
            // 如果是从Agent Settings菜单点击的，跳转到generate_agent页面并加载配置
            navigateToAgentSettings(agentId);
        } else {
            // 否则，使用script.js中的函数加载Agent并跳转到workspace
            if (typeof window.loadAgentAndRedirect === 'function') {
                window.loadAgentAndRedirect(agentId);
            } else {
                loadAgentAndRedirectInternal(agentId);
            }
        }
    }
    
    // 关闭侧边栏
    toggleSidebar();
}

// 导航到Agent设置页面
function navigateToAgentSettings(agentId) {
    // 将agentId存储在sessionStorage中，以便在generate_agent页面加载时使用
    sessionStorage.setItem('load_agent_id', agentId);
    // 标记这是编辑模式而非新建模式
    sessionStorage.setItem('agent_edit_mode', 'true');
    
    // 跳转到generate_agent页面
    window.location.href = "generate_agent.html";
}

// 内部实现的加载Agent并跳转函数，以防script.js的函数不可用
async function loadAgentAndRedirectInternal(agentId) {
    try {
        const response = await fetch(`/load_agent/${agentId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            alert(`Agent "${data.agent.agent_name}" has been loaded! Redirecting to workspace...`);
            
            // 跳转到index页面
            setTimeout(() => {
                window.location.href = "index.html";
            }, 500);
        } else {
            alert("Error loading agent: " + (data.error || "Unknown error"));
        }
    } catch (error) {
        console.error("Error loading agent:", error);
        alert("Error loading agent. Please try again.");
    }
}

// 添加Create New按钮
function addCreateNewAgentMenu() {
    // 如果已经在generate_agent.html页面，添加一个"Create New"按钮
    if (window.location.pathname.includes('generate_agent.html')) {
        const header = document.querySelector('h1');
        if (header && !document.getElementById('create-new-btn')) {
            const createNewBtn = document.createElement('button');
            createNewBtn.id = 'create-new-btn';
            createNewBtn.textContent = '';
            createNewBtn.style.fontSize = '0.8em';
            createNewBtn.style.marginLeft = '0px';
            createNewBtn.style.padding = '0px 0px';
            createNewBtn.onclick = function() {
                // 调用script.js中的重置函数，如果可用
                if (typeof window.resetAgentForm === 'function') {
                    window.resetAgentForm();
                } else {
                    resetAgentFormInternal();
                }
            };
            header.appendChild(createNewBtn);
        }
    }
}

// 内部实现的表单重置函数，以防script.js的函数不可用
function resetAgentFormInternal() {
    // 清除全局变量和sessionStorage
    if (typeof window.currentEditingAgentId !== 'undefined') {
        window.currentEditingAgentId = null;
    }
    sessionStorage.removeItem('currentEditingAgentId');
    
    // 重置表单
    const form = document.querySelector('form');
    if (form) form.reset();
    
    // 清除所有复选框
    document.querySelectorAll('.selection-box input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // 重置下拉框为默认值
    document.getElementById('data-source').value = 'alphavantage';
    document.getElementById('model-source').value = 'deepseek';
    document.getElementById('framework-source').value = 'magnetic';
    
    // 清空约束和名称
    document.getElementById('constraint-name').value = '';
    document.getElementById('agent-name').value = '';
    
    // 恢复页面标题
    const pageTitle = document.querySelector('h1');
    if (pageTitle) {
        pageTitle.textContent = 'MACI - Agent Setting';
    }
    
    // 恢复按钮文本
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) {
        generateBtn.textContent = 'Generate Agent';
    }
    
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.textContent = 'Save Agent Only';
    }
    
    alert('Form reset successfully. You can now create a new Agent.');
}

// 创建Agent选择模态框
function createAgentSelectionModal() {
    const modal = document.createElement('div');
    modal.id = 'agent-selection-modal';
    modal.className = 'modal';
    modal.style.display = 'none';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Select an Agent</h2>
                <span class="modal-close">&times;</span>
            </div>
            <div class="modal-body">
                <p>Please select an agent to use in your new workspace:</p>
                <div id="modal-agent-list">
                    <p>Loading agents...</p>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
        .modal {
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
        }
        
        .modal-content {
            background-color: #292929;
            color: white;
            margin: 15% auto;
            padding: 20px;
            border-radius: 8px;
            width: 60%;
            max-width: 600px;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #3c3c3c;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .modal-header h2 {
            margin: 0;
        }
        
        .modal-close {
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .modal-close:hover {
            color: #fff;
        }
        
        .modal-agent-item {
            padding: 15px;
            margin: 10px 0;
            background-color: #3c3c3c;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .modal-agent-item:hover {
            background-color: #4d4d4d;
        }
    `;
    
    document.head.appendChild(style);
    
    // 添加事件监听器
    const closeBtn = modal.querySelector('.modal-close');
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// 打开Agent选择模态框
async function openAgentSelectionModal() {
    const modal = document.getElementById('agent-selection-modal');
    const agentList = document.getElementById('modal-agent-list');
    
    if (!modal || !agentList) return;
    
    // 显示模态框
    modal.style.display = 'block';
    
    // 加载Agent列表
    agentList.innerHTML = '<p>Loading agents...</p>';
    
    try {
        // 使用script.js中的函数，如果可用
        const agents = typeof window.listSavedAgents === 'function' 
            ? await window.listSavedAgents() 
            : await listSavedAgentsInternal();
        
        if (agents.length === 0) {
            agentList.innerHTML = `
                <p>No saved agents found. Please create an agent first.</p>
                <button onclick="navigateTo('generate_agent.html')">Create New Agent</button>
            `;
            return;
        }
        
        // 创建Agent列表HTML
        let html = '';
        
        agents.forEach(agent => {
            const features = agent.features && agent.features.length > 0 
                ? `<div>Features: ${agent.features.join(', ')}</div>` 
                : '';
            
            const loadFunctionCall = typeof window.loadAgentAndRedirect === 'function'
                ? `window.loadAgentAndRedirect('${agent.id}')`
                : `loadAgentAndRedirectInternal('${agent.id}')`;
            
            html += `
                <div class="modal-agent-item" onclick="${loadFunctionCall}">
                    <div style="font-weight: bold; font-size: 1.1em;">${agent.name || 'Unnamed Agent'}</div>
                    <div>Model: ${agent.model || 'Unknown model'}</div>
                    ${features}
                </div>
            `;
        });
        
        agentList.innerHTML = html;
        
    } catch (error) {
        console.error("Error loading saved agents:", error);
        agentList.innerHTML = '<p>Error loading agents. Please try again.</p>';
    }
    
    // 关闭侧边栏
    toggleSidebar();
}