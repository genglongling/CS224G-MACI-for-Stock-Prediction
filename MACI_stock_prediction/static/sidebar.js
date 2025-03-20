// sidebar.js - Sidebar functionality

// Initialize sidebar after document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar
    initSidebar();
    
    // If on generate_agent.html page
    if (window.location.pathname.includes('generate_agent.html')) {
        // Check if there’s a preset Agent to load
        const agentIdToLoad = sessionStorage.getItem('load_agent_id');
        if (agentIdToLoad) {
            // Call function from script.js to load Agent
            if (typeof window.loadSavedAgent === 'function') {
                window.loadSavedAgent(agentIdToLoad);
            }
            
            // Clear sessionStorage ID to prevent reloading on next page load
            sessionStorage.removeItem('load_agent_id');
            sessionStorage.removeItem('agent_edit_mode');
        }
        
        // Add "Create New" button
        addCreateNewAgentMenu();
    }
});

// Initialize sidebar
function initSidebar() {
    // Check if sidebar element already exists on the page
    if (document.getElementById('app-sidebar')) {
        console.log('Sidebar already exists');
        return;
    }
    
    // Create sidebar HTML
    createSidebarHTML();
    
    // Add event listeners
    addSidebarEventListeners();
    
    // Load saved Agents list
    loadSavedAgentsToSidebar();
}

// Create sidebar HTML
function createSidebarHTML() {
    // Create sidebar container
    const sidebar = document.createElement('div');
    sidebar.id = 'app-sidebar';
    sidebar.className = 'sidebar';
    
    // Sidebar content
    sidebar.innerHTML = `
        <div class="sidebar-header">
            <h3>MACI Menu</h3>
            <button class="sidebar-close">×</button>
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
            <li id="agent-settings-menu" onclick="openSettingsModal()">
                <i>⚙️</i> Settings
            </li>
            <li id="new-workspace-menu" onclick="openAgentSelectionModal()">
                <i>🚀</i> New Workspace
            </li>
        </ul>
    `;
    
    // Create overlay
    const overlay = document.createElement('div');
    overlay.id = 'sidebar-overlay';
    overlay.className = 'sidebar-overlay';
    
    // Create user avatar button
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
    
    // Add to document
    document.body.appendChild(sidebar);
    document.body.appendChild(overlay);
    
    // Add Agent selection modal
    createAgentSelectionModal();
    
    // Add Settings modal
    createSettingsModal();
}

// Open Agent Settings modal
function createSettingsModal() {
    const modal = document.createElement('div');
    modal.id = 'settings-modal';
    modal.className = 'modal';
    modal.style.display = 'none';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Agent Settings</h2>
                <span class="modal-close">×</span>
            </div>
            <div class="modal-body">
                <p>Select an agent to edit:</p>
                <div id="modal-settings-list">
                    <p>Loading agents...</p>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    const closeBtn = modal.querySelector('.modal-close');
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

async function openSettingsModal() {
    const modal = document.getElementById('settings-modal');
    const agentList = document.getElementById('modal-settings-list');
    
    if (!modal || !agentList) return;
    
    // Show modal
    modal.style.display = 'block';
    
    // Load Agents list
    agentList.innerHTML = '<p>Loading agents...</p>';
    
    try {
        // Use function from script.js if available
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
        
        // Create Agents list HTML
        let html = '';
        
        agents.forEach(agent => {
            const features = agent.features && agent.features.length > 0 
                ? `<div>Features: ${agent.features.join(', ')}</div>` 
                : '';
            
            html += `
                <div class="modal-agent-item" onclick="navigateToAgentSettings('${agent.id}')">
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
    
    // Close sidebar
    toggleSidebar();
}


// Add sidebar event listeners
function addSidebarEventListeners() {
    // User avatar button click event
    const avatarBtn = document.getElementById('user-avatar-btn');
    if (avatarBtn) {
        avatarBtn.addEventListener('click', toggleSidebar);
    }
    
    // Close button click event
    const closeBtn = document.querySelector('.sidebar-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', toggleSidebar);
    }
    
    // Overlay click event
    const overlay = document.getElementById('sidebar-overlay');
    if (overlay) {
        overlay.addEventListener('click', toggleSidebar);
    }
}

// Toggle sidebar show/hide
function toggleSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    
    if (sidebar && overlay) {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }
}

// Page navigation
function navigateTo(url) {
    window.location.href = url;
}

// Toggle saved Agents list show/hide
function toggleSavedAgentsList() {
    const agentsList = document.getElementById('saved-agents-list');
    
    if (agentsList) {
        agentsList.classList.toggle('active');
        
        // If list is opened, load Agents
        if (agentsList.classList.contains('active')) {
            loadSavedAgentsToSidebar();
        }
    }
}

// Save Agent configuration to backend
async function saveAgentConfig() {
    const dataSource = document.getElementById('data-source').value;
    const modelSource = document.getElementById('model-source').value;
    const frameworkSource = document.getElementById('framework-source').value;
    const featureCheckboxes = document.querySelectorAll('.selection-box input[type="checkbox"]:checked');
    const features = Array.from(featureCheckboxes).map(checkbox => checkbox.value);
    const constraints = document.getElementById('constraint-name').value;
    const agentName = document.getElementById('agent-name').value || "Investment Research Assistant";
    
    // Create configuration object
    const config = {
        data_source: dataSource,
        model_source: modelSource,
        framework_source: frameworkSource,
        features: features,
        constraints: constraints,
        agent_name: agentName
    };
    
    console.log("Saving agent configuration:", config);
    
    try {
      // Save current configuration for session
      const response = await fetch('/save_agent_config', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify(config)
      });
      
      if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        console.log("Agent is set correctly for this conversation");
        
        // Decide whether to update or save based on edit mode
        let newAgentId;
        
        if (window.currentEditingAgentId) {
            // Update by deleting and recreating
            newAgentId = await deleteAndReCreateAgent(window.currentEditingAgentId);
            alert("Agent is updated successfully! Redirecting to your stock prediction workspace...");
        } else {
            // Ask if this Agent should be saved for future use
            if (confirm("Agent is updated successfully! Do you want to save this Agent for future use?")) {
                // Get agent_id returned by saveAgentForReuse
                newAgentId = await saveAgentForReuse();
                console.log("saveAgentForReuse():", newAgentId);
                
            }
            alert("Redirecting to your stock prediction workspace...");
        }
        
        // Redirect regardless of success or failure
        setTimeout(() => {
            if (newAgentId) {
                window.loadAgentAndRedirect(newAgentId);
            }
        }, 500);
      } else {
          console.error("Agent has problem during setting:", data.message);
          alert("Agent has problem during saving: " + (data.message || "unknown mistake"));
      }
  } catch (error) {
      console.error("Agent has problem during saving:", error);
      alert("Agent has problem during saving, please retry.");
  }
}

// Load saved Agents list to sidebar
async function loadSavedAgentsToSidebar() {
    const agentsList = document.getElementById('saved-agents-list');
    if (!agentsList) return;
    
    agentsList.innerHTML = '<div class="saved-agent-loading">Loading agents...</div>';
    
    try {
        // Use function from script.js if available
        const agents = typeof window.listSavedAgents === 'function' 
            ? await window.listSavedAgents() 
            : await listSavedAgentsInternal();
        
        if (agents.length === 0) {
            agentsList.innerHTML = '<div class="saved-agent-loading">No saved agents found</div>';
            return;
        }
        
        // Create Agents list HTML
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

// Internal implementation of listing Agents, in case script.js function is unavailable
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

// Handle Agent selection
function handleAgentSelection(agentId) {
    const currentPage = window.location.pathname.split('/').pop();
    
    // Decide behavior based on current page
    if (currentPage === 'generate_agent.html') {
        // On generation page, use script.js function to load Agent configuration
        if (typeof window.loadSavedAgent === 'function') {
            window.loadSavedAgent(agentId);
        }
    } else {
        // Determine behavior based on click source
        const clickSource = event.target.closest('li') ? event.target.closest('li').id : '';
        
        if (clickSource === 'agent-settings-menu' || 
            event.target.closest('#saved-agents-list')) {
            // If clicked from Agent Settings menu, navigate to generate_agent page and load configuration
            navigateToAgentSettings(agentId);
        } else {
            // Otherwise, use script.js function to load Agent and redirect to workspace
            if (typeof window.loadAgentAndRedirect === 'function') {
                window.loadAgentAndRedirect(agentId);
            } else {
                loadAgentAndRedirectInternal(agentId);
            }
        }
    }
    
    // Close sidebar
    toggleSidebar();
}

// Navigate to Agent settings page
function navigateToAgentSettings(agentId) {
    // Store agentId in sessionStorage for use when loading generate_agent page
    sessionStorage.setItem('load_agent_id', agentId);
    // Mark as edit mode rather than new mode
    sessionStorage.setItem('agent_edit_mode', 'true');
    
    // Navigate to generate_agent page
    window.location.href = "generate_agent.html";
}

// Internal implementation of loading Agent and redirecting, in case script.js function is unavailable
async function loadAgentAndRedirectInternal(agentId) {
    try {
        const response = await fetch(`/load_agent/${agentId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            alert(`Agent "${data.agent.agent_name}" has been loaded! Redirecting to workspace...`);
            
            // Navigate to index.html and pass agentId as URL parameter
            setTimeout(() => {
                window.location.href = `index.html?agentId=${encodeURIComponent(agentId)}`;
            }, 500);
        } else {
            alert("Error loading agent: " + (data.error || "Unknown error"));
        }
    } catch (error) {
        console.error("Error loading agent:", error);
        alert("Error loading agent. Please try again.");
    }
}

// Add Create New button
function addCreateNewAgentMenu() {
    // If already on generate_agent.html page, add a "Create New" button
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
                // Call reset function from script.js if available
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

// Internal implementation of form reset, in case script.js function is unavailable
function resetAgentFormInternal() {
    // Clear global variable and sessionStorage
    if (typeof window.currentEditingAgentId !== 'undefined') {
        window.currentEditingAgentId = null;
    }
    sessionStorage.removeItem('currentEditingAgentId');
    
    // Reset form
    const form = document.querySelector('form');
    if (form) form.reset();
    
    // Clear all checkboxes
    document.querySelectorAll('.selection-box input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Reset dropdowns to default values
    document.getElementById('data-source').value = 'alphavantage';
    document.getElementById('model-source').value = 'deepseek';
    document.getElementById('framework-source').value = 'magnetic';
    
    // Clear constraints and name
    document.getElementById('constraint-name').value = '';
    document.getElementById('agent-name').value = '';
    
    // Restore page title
    const pageTitle = document.querySelector('h1');
    if (pageTitle) {
        pageTitle.textContent = 'MACI - Agent Setting';
    }
    
    // Restore button text
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

// Create Agent selection modal
function createAgentSelectionModal() {
    const modal = document.createElement('div');
    modal.id = 'agent-selection-modal';
    modal.className = 'modal';
    modal.style.display = 'none';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Select an Agent</h2>
                <span class="modal-close">×</span>
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
    
    // Add styles
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
    
    // Add event listeners
    const closeBtn = modal.querySelector('.modal-close');
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Open Agent selection modal
async function openAgentSelectionModal() {
    const modal = document.getElementById('agent-selection-modal');
    const agentList = document.getElementById('modal-agent-list');
    
    if (!modal || !agentList) return;
    
    // Show modal
    modal.style.display = 'block';
    
    // Load Agents list
    agentList.innerHTML = '<p>Loading agents...</p>';
    
    try {
        // Use function from script.js if available
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
        
        // Create Agents list HTML
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
    
    // Close sidebar
    toggleSidebar();
}