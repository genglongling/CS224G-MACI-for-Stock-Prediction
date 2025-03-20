// script.js - Handle Agent generation, configuration, and stock data queries

// Global variable to store the ID of the currently edited Agent
window.currentEditingAgentId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Check if on the Agent configuration page
    const generateButton = document.querySelector('button[onclick="goToIndex()"]');
    if (generateButton) {
        generateButton.removeAttribute('onclick');
        generateButton.addEventListener('click', saveAgentConfig);
    }
    
    // Check if on the stock query page
    const queryButton = document.getElementById('queryButton');
    if (queryButton) {
        queryButton.addEventListener('click', fetchStockData);
    }
});

// Save Agent configuration to the backend

async function deleteAgent(agentId) {
    try {
        const response = await fetch(`/delete_agent/${agentId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`Agent ${agentId} has been deleted successfully.`);
            return true;
        } else {
            console.error("Error deleting agent:", data.error || "Unknown error");
            return false;
        }
    } catch (error) {
        console.error("Error deleting agent:", error);
        return false;
    }
}

async function deleteAndReCreateAgent(agentId) {
    try {
        const agent = await loadAgent(agentId);
        if (!agent) {
            throw new Error("Could not load the agent to update");
        }
        
        const dataSource = document.getElementById('data-source').value;
        const modelSource = document.getElementById('model-source').value;
        const frameworkSource = document.getElementById('framework-source').value;
        const featureCheckboxes = document.querySelectorAll('.selection-box input[type="checkbox"]:checked');
        const features = Array.from(featureCheckboxes).map(checkbox => checkbox.value);
        const constraints = document.getElementById('constraint-name').value;
        const agentName = document.getElementById('agent-name').value || "Investment Research Assistant";
        const apiKey = document.getElementById('api-key-input')?.value || "API_KEY"; 
        
        const updatedConfig = {
            data_source: dataSource,
            model_source: modelSource,
            framework_source: frameworkSource,
            features: features,
            constraints: constraints,
            agent_name: agentName,
            api_key: api_key // Add API Key
        };
        
        const deleteSuccess = await deleteAgent(agentId);
        if (!deleteSuccess) {
            throw new Error("Failed to delete the existing agent");
        }
        
        const response = await fetch('/save_agent_for_reuse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedConfig)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`Agent has been successfully updated with ID: ${data.agent_id}`);
            window.currentEditingAgentId = data.agent_id;
            sessionStorage.setItem('currentEditingAgentId', data.agent_id);
            return data.agent_id;
        } else {
            throw new Error(data.error || "Unknown error creating new agent");
        }
    } catch (error) {
        console.error("Error updating agent:", error);
        alert("Error updating agent: " + error.message);
        return null;
    }
}

async function updateExistingAgent(agentId) {
    try {
        const newAgentId = await deleteAndReCreateAgent(agentId);
        if (newAgentId) {
            alert(`Agent has been successfully updated!`);
            return newAgentId;
        } else {
            alert("Failed to update the agent. Please try again.");
            return null;
        }
    } catch (error) {
        console.error("Error updating agent:", error);
        alert("Error updating agent: " + error.message);
        return null;
    }
}

async function saveAgentOnly() {
    let agentId;
    
    if (window.currentEditingAgentId) {
        agentId = await updateExistingAgent(window.currentEditingAgentId);
    } else {
        agentId = await saveAgentForReuse();
    }
    
    if (agentId) {
        const section = document.getElementById('saved-agents-section');
        if (section) {
            if (section.style.display === 'none') {
                toggleSavedAgents();
            } else {
                loadSavedAgentsList();
            }
        }
    }
}

async function saveAgentForReuse() {
    const dataSource = document.getElementById('data-source').value;
    const modelSource = document.getElementById('model-source').value;
    const frameworkSource = document.getElementById('framework-source').value;
    const featureCheckboxes = document.querySelectorAll('.selection-box input[type="checkbox"]:checked');
    const features = Array.from(featureCheckboxes).map(checkbox => checkbox.value);
    const constraints = document.getElementById('constraint-name').value;
    const agentName = document.getElementById('agent-name').value || "Investment Research Assistant";
    const apiKey = document.getElementById('api-key-input')?.value || null; // Get API Key
    
    const config = {
        data_source: dataSource,
        model_source: modelSource,
        framework_source: frameworkSource,
        features: features,
        constraints: constraints,
        agent_name: agentName,
        api_key: apiKey // Add API Key
    };
    
    try {
        const response = await fetch('/save_agent_for_reuse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            alert(`Agent "${agentName}" has been saved and can be reused later!`);
            return data.agent_id;
        } else {
            alert("Error saving agent: " + (data.error || "Unknown error"));
            return null;
        }
    } catch (error) {
        console.error("Error saving agent:", error);
        alert("Error saving agent. Please try again.");
        return null;
    }
}

async function listSavedAgents() {
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

async function loadAgent(agentId) {
    try {
        const response = await fetch(`/load_agent/${agentId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            return data.agent;
        } else {
            alert("Error loading agent: " + (data.error || "Unknown error"));
            return null;
        }
    } catch (error) {
        console.error("Error loading agent:", error);
        alert("Error loading agent. Please try again.");
        return null;
    }
}

async function loadSavedAgent(agentId) {
    try {
        const agent = await loadAgent(agentId);
        
        if (!agent) return;
        
        window.currentEditingAgentId = agentId;
        sessionStorage.setItem('currentEditingAgentId', agentId);
        
        document.getElementById('data-source').value = agent.data_source || 'alphavantage';
        document.getElementById('model-source').value = agent.model_source || 'deepseek';
        document.getElementById('framework-source').value = agent.framework_source || 'magnetic';
        
        document.querySelectorAll('.selection-box input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = agent.features && agent.features.includes(checkbox.value);
        });
        
        document.getElementById('constraint-name').value = agent.constraints || '';
        document.getElementById('agent-name').value = agent.agent_name || '';
        document.getElementById('api-key-input').value = agent.api_key || ''; // Load API Key
        
        const pageTitle = document.querySelector('h1');
        if (pageTitle) {
            pageTitle.textContent = `MACI - Edit Agent: ${agent.agent_name || 'Unnamed Agent'}`;
        }
        
        const generateBtn = document.getElementById('generate-btn');
        if (generateBtn) {
            generateBtn.textContent = 'Update & Use Agent';
        }
        
        const saveBtn = document.getElementById('save-btn');
        if (saveBtn) {
            saveBtn.textContent = 'Update Agent Only';
        }
        
        const savedAgentsSection = document.getElementById('saved-agents-section');
        if (savedAgentsSection) {
            savedAgentsSection.style.display = 'none';
        }
        
        console.log(`Agent ${agentId} loaded successfully for editing`);
        
    } catch (error) {
        console.error("Error loading agent:", error);
        alert("Error loading agent. Please try again.");
    }
}

async function loadAgentAndRedirect(agentId) {
    try {
        const agent = await loadAgent(agentId);
        
        if (!agent) return;
        
        alert(`Agent "${agent.agent_name}" has been loaded! Redirecting to workspace...`);
        
        setTimeout(() => {
            window.location.href = `index.html?agentId=${encodeURIComponent(agentId)}`;
        }, 500);
        
    } catch (error) {
        console.error("Error loading agent:", error);
        alert("Error loading agent. Please try again.");
    }
}

function resetAgentForm() {
    window.currentEditingAgentId = null;
    sessionStorage.removeItem('currentEditingAgentId');
    
    const form = document.querySelector('form');
    if (form) form.reset();
    
    document.querySelectorAll('.selection-box input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    document.getElementById('data-source').value = 'alphavantage';
    document.getElementById('model-source').value = 'deepseek';
    document.getElementById('framework-source').value = 'magnetic';
    document.getElementById('constraint-name').value = '';
    document.getElementById('agent-name').value = '';
    document.getElementById('api-key-input').value = ''; // Reset API Key
    
    const pageTitle = document.querySelector('h1');
    if (pageTitle) {
        pageTitle.textContent = 'MACI - Agent Setting';
    }
    
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

async function fetchStockData() {
    let symbols = document.getElementById("stockSymbols").value;
    let resultDiv = document.getElementById("result");

    if (!symbols) {
        resultDiv.innerHTML = "<p style='color: red;'>Please enter stock symbols.</p>";
        return;
    }

    resultDiv.innerHTML = "<p>Fetching data...</p>";

    try {
        let response = await fetch(`/investment_research?question=${encodeURIComponent(symbols)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        let data = await response.text();
        resultDiv.innerHTML = `<pre>${data}</pre>`;
    } catch (error) {
        resultDiv.innerHTML = `<p style='color: red;'>Failed to fetch stock data: ${error.message}</p>`;
    }
}

function generateAndExportAgent() {
    alert("Agent Generated! Redirecting to Stock Prediction...");
    window.location.href = "index.html";
}

async function setApiKeys(apiKeys) {
    try {
        const response = await fetch('/set-api-keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(apiKeys)
        });
        
        const data = await response.json();
        return data.success;
    } catch (error) {
        console.error("Error setting API keys:", error);
        return false;
    }
}

if (typeof toggleSavedAgents !== 'function') {
    function toggleSavedAgents() {
        const section = document.getElementById('saved-agents-section');
        if (section) {
            if (section.style.display === 'none') {
                section.style.display = 'block';
                loadSavedAgentsList();
            } else {
                section.style.display = 'none';
            }
        }
    }
}

if (typeof loadSavedAgentsList !== 'function') {
    async function loadSavedAgentsList() {
        const listContainer = document.getElementById('agent-list');
        if (!listContainer) return;
        
        listContainer.innerHTML = '<p>Loading saved agents...</p>';
        
        try {
            const agents = await listSavedAgents();
            
            if (agents.length === 0) {
                listContainer.innerHTML = '<p>No saved agents found.</p>';
                return;
            }
            
            let html = '<ul class="agent-items" style="list-style-type: none; padding: 0;">';
            agents.forEach(agent => {
                const features = agent.features && agent.features.length > 0 
                    ? `Features: ${agent.features.join(', ')}` 
                    : 'No special features';
                const createdDate = agent.created_at 
                    ? new Date(agent.created_at).toLocaleString() 
                    : 'Unknown date';
                html += `
                    <li style="margin-bottom: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px;">
                        <div><strong>${agent.name || 'Unnamed Agent'}</strong> (${agent.model || 'Unknown model'})</div>
                        <div style="font-size: 0.9em; color: #666;">${features}</div>
                        <div style="font-size: 0.8em; color: #888;">Created: ${createdDate}</div>
                        <button onclick="loadSavedAgent('${agent.id}')" style="margin-top: 5px;">Load Agent</button>
                    </li>
                `;
            });
            html += '</ul>';
            listContainer.innerHTML = html;
        } catch (error) {
            console.error("Error loading saved agents:", error);
            listContainer.innerHTML = '<p>Error loading saved agents. Please try again.</p>';
        }
    }
}

// Expose core functions to the window object for use in sidebar.js
window.loadSavedAgent = loadSavedAgent;
window.loadAgentAndRedirect = loadAgentAndRedirect;
window.listSavedAgents = listSavedAgents;
window.resetAgentForm = resetAgentForm;