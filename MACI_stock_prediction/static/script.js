// script.js - 处理Agent生成、配置和股票数据查询

// 全局变量，保存当前正在编辑的Agent ID
window.currentEditingAgentId = null;

document.addEventListener('DOMContentLoaded', function() {
    // 检查是否在Agent配置页面
    const generateButton = document.querySelector('button[onclick="goToIndex()"]');
    if (generateButton) {
        // 移除原有的onclick属性
        generateButton.removeAttribute('onclick');
        // 添加新的事件监听器
        generateButton.addEventListener('click', saveAgentConfig);
    }
    
    // 检查是否在股票查询页面
    const queryButton = document.getElementById('queryButton');
    if (queryButton) {
        queryButton.addEventListener('click', fetchStockData);
    }
});

// 保存Agent配置到后端
async function saveAgentConfig() {
    // 获取数据源
    const dataSource = document.getElementById('data-source').value;
    
    // 获取LLM模型
    const modelSource = document.getElementById('model-source').value;
    
    // 获取框架
    const frameworkSource = document.getElementById('framework-source').value;
    
    // 获取所有选中的功能
    const featureCheckboxes = document.querySelectorAll('.selection-box input[type="checkbox"]:checked');
    const features = Array.from(featureCheckboxes).map(checkbox => checkbox.value);
    
    // 获取约束条件
    const constraints = document.getElementById('constraint-name').value;
    
    // 获取Agent名称
    const agentName = document.getElementById('agent-name').value || "Investment Research Assistant";
    
    // 创建配置对象
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
      // 保存当前配置用于会话
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
          
          // 根据是否在编辑模式决定是更新还是保存
          if (window.currentEditingAgentId) {
              // 使用删除后重建的方式来更新
              const newAgentId = await deleteAndReCreateAgent(window.currentEditingAgentId);
              if (newAgentId) {
                  alert("Agent is updated successfully! Redirecting to your stock prediction workspace...");
              } else {
                  alert("Agent has problem during update，but new update is saved。Redirecting now...");
              }
          } else {
              // 询问是否保存此Agent供将来使用
              if (confirm("Agent is updated successfully! Do you want to save this Agent for future use?")) {
                  await saveAgentForReuse();
              }
              alert("Redirecting to your stock prediction workspace...");
          }
          
          // 无论成功或失败都重定向
          setTimeout(() => {
              window.location.href = "index.html";
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

async function deleteAgent(agentId) {
  try {
      const response = await fetch(`/delete_agent/${agentId}`, {
          method: 'DELETE',
          headers: {
              'Content-Type': 'application/json',
          }
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

// 通过先删除再创建的方式更新Agent
async function deleteAndReCreateAgent(agentId) {
  try {
      // 首先，加载当前的Agent配置
      const agent = await loadAgent(agentId);
      if (!agent) {
          throw new Error("Could not load the agent to update");
      }
      
      // 获取当前表单中的配置，这是用户修改后的值
      const dataSource = document.getElementById('data-source').value;
      const modelSource = document.getElementById('model-source').value;
      const frameworkSource = document.getElementById('framework-source').value;
      
      // 获取所有选中的功能
      const featureCheckboxes = document.querySelectorAll('.selection-box input[type="checkbox"]:checked');
      const features = Array.from(featureCheckboxes).map(checkbox => checkbox.value);
      
      // 获取约束条件和Agent名称
      const constraints = document.getElementById('constraint-name').value;
      const agentName = document.getElementById('agent-name').value || "Investment Research Assistant";
      
      // 创建更新后的配置对象
      const updatedConfig = {
          data_source: dataSource,
          model_source: modelSource,
          framework_source: frameworkSource,
          features: features,
          constraints: constraints,
          agent_name: agentName
      };
      
      // 删除现有的Agent
      const deleteSuccess = await deleteAgent(agentId);
      if (!deleteSuccess) {
          throw new Error("Failed to delete the existing agent");
      }
      
      // 创建新的Agent配置
      const response = await fetch('/save_agent_for_reuse', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify(updatedConfig)
      });
      
      if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
          console.log(`Agent has been successfully updated with ID: ${data.agent_id}`);
          
          // 更新当前编辑的Agent ID
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
// 更新现有Agent的替代方法，使用deleteAndReCreateAgent
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

// 保存Agent配置而不跳转
async function saveAgentOnly() {
    let agentId;
    
    // 检查全局变量而不是局部变量
    if (window.currentEditingAgentId) {
        // 更新现有Agent
        agentId = await updateExistingAgent(window.currentEditingAgentId);
    } else {
        // 创建新Agent
        agentId = await saveAgentForReuse();
    }
    
    if (agentId) {
        // 刷新Agent列表
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

// 保存Agent供以后重用
async function saveAgentForReuse() {
    // 获取数据源
    const dataSource = document.getElementById('data-source').value;
    
    // 获取LLM模型
    const modelSource = document.getElementById('model-source').value;
    
    // 获取框架
    const frameworkSource = document.getElementById('framework-source').value;
    
    // 获取所有选中的功能
    const featureCheckboxes = document.querySelectorAll('.selection-box input[type="checkbox"]:checked');
    const features = Array.from(featureCheckboxes).map(checkbox => checkbox.value);
    
    // 获取约束条件
    const constraints = document.getElementById('constraint-name').value;
    
    // 获取Agent名称
    const agentName = document.getElementById('agent-name').value || "Investment Research Assistant";
    
    // 创建配置对象
    const config = {
        data_source: dataSource,
        model_source: modelSource,
        framework_source: frameworkSource,
        features: features,
        constraints: constraints,
        agent_name: agentName
    };
    
    try {
        // 发送配置到保存端点
        const response = await fetch('/save_agent_for_reuse', {
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

// 获取已保存的Agent列表
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

// 加载特定Agent
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

// 加载选中的已保存Agent到表单
async function loadSavedAgent(agentId) {
    try {
        const agent = await loadAgent(agentId);
        
        if (!agent) return;
        
        // 设置当前正在编辑的Agent ID
        window.currentEditingAgentId = agentId;
        // 同时存储到sessionStorage作为备份
        sessionStorage.setItem('currentEditingAgentId', agentId);
        
        // 更新UI选择
        document.getElementById('data-source').value = agent.data_source || 'alphavantage';
        document.getElementById('model-source').value = agent.model_source || 'deepseek';
        document.getElementById('framework-source').value = agent.framework_source || 'magnetic';
        
        // 更新功能复选框
        document.querySelectorAll('.selection-box input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = agent.features && agent.features.includes(checkbox.value);
        });
        
        // 更新约束和名称
        document.getElementById('constraint-name').value = agent.constraints || '';
        document.getElementById('agent-name').value = agent.agent_name || '';
        
        // 更新页面标题，表明这是编辑模式
        const pageTitle = document.querySelector('h1');
        if (pageTitle) {
            pageTitle.textContent = `MACI - Edit Agent: ${agent.agent_name || 'Unnamed Agent'}`;
        }
        
        // 更新按钮文本
        const generateBtn = document.getElementById('generate-btn');
        if (generateBtn) {
            generateBtn.textContent = 'Update & Use Agent';
        }
        
        const saveBtn = document.getElementById('save-btn');
        if (saveBtn) {
            saveBtn.textContent = 'Update Agent Only';
        }
        
        // 关闭已保存Agent列表
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

// 加载Agent并跳转
async function loadAgentAndRedirect(agentId) {
    try {
        const agent = await loadAgent(agentId);
        
        if (!agent) return;
        
        alert(`Agent "${agent.agent_name}" has been loaded! Redirecting to workspace...`);
        
        // 跳转到index页面
        setTimeout(() => {
            window.location.href = "index.html";
        }, 500);
        
    } catch (error) {
        console.error("Error loading agent:", error);
        alert("Error loading agent. Please try again.");
    }
}

// 重置Agent表单
function resetAgentForm() {
    // 清除currentEditingAgentId
    window.currentEditingAgentId = null;
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

// 获取股票数据 - 保留原有功能并增强
// async function fetchStockData() {
//     let symbols = document.getElementById("stockSymbols").value;
//     let resultDiv = document.getElementById("result");
//
//     if (!symbols) {
//         resultDiv.innerHTML = "<p style='color: red;'>Please enter stock symbols or a question about stocks.</p>";
//         return;
//     }
//
//     resultDiv.innerHTML = "<p>Processing your query with configured AI agent...</p>";
//
//     try {
//         // 使用事件源获取流式响应
//         const eventSource = new EventSource(`/investment_research?question=${encodeURIComponent(symbols)}`);
//
//         // 处理流式响应
//         eventSource.onmessage = function(event) {
//             try {
//                 const data = JSON.parse(event.data);
//
//                 // 如果是普通消息，直接添加
//                 if (typeof data === 'object' && data.message) {
//                     resultDiv.innerHTML += `<div>${data.message}</div>`;
//                 }
//                 // 如果是最终响应，替换整个内容
//                 else if (data.type === 'final_response') {
//                     resultDiv.innerHTML = `<div class="final-result">${data.main_response}</div>`;
//
//                     // 如果有搜索结果，添加
//                     if (data.has_search_results) {
//                         let searchResultsHtml = '<div class="search-results"><h3>Search Results</h3>';
//                         data.search_results.forEach(result => {
//                             searchResultsHtml += `
//                                 <div class="search-result">
//                                     <h4><a href="${result.source}" target="_blank">${result.source}</a></h4>
//                                     <p>${result.content}</p>
//                                 </div>
//                             `;
//                         });
//                         searchResultsHtml += '</div>';
//                         resultDiv.innerHTML += searchResultsHtml;
//                     }
//                 }
//                 // 如果是终端输出，添加到调试区域
//                 else if (data.type === 'terminal_output') {
//                     // 可以添加到一个隐藏的调试区域
//                     const debugDiv = document.getElementById("debug-output");
//                     if (debugDiv) {
//                         debugDiv.innerHTML += `<pre>${data.data}</pre>`;
//                     }
//                 }
//                 // 如果是主响应更新，替换主内容区域
//                 else if (data.type === 'main_response') {
//                     resultDiv.innerHTML = `<div class="main-response">${data.data}</div>`;
//                 }
//                 // 否则尝试将其作为字符串添加
//                 else if (typeof event.data === 'string') {
//                     resultDiv.innerHTML += `<div>${event.data}</div>`;
//                 }
//
//                 // 自动滚动到底部
//                 window.scrollTo(0, document.body.scrollHeight);
//             } catch (e) {
//                 // 如果解析JSON失败，直接添加文本
//                 resultDiv.innerHTML += `<div>${event.data}</div>`;
//             }
//         };
//
//         // 处理完成事件
//         eventSource.addEventListener('complete', function(event) {
//             console.log("Query processing complete");
//             eventSource.close();
//         });
//
//         // 处理错误
//         eventSource.onerror = function(event) {
//             console.error("EventSource error:", event);
//             resultDiv.innerHTML += `<p style='color: red;'>Error during data processing. Please try again.</p>`;
//             eventSource.close();
//         };
//     } catch (error) {
//         resultDiv.innerHTML = `<p style='color: red;'>Failed to fetch stock data: ${error.message}</p>`;
//     }
// }

// 原有函数，保留为兼容性
function generateAndExportAgent() {
    alert("Agent Generated! Redirecting to Stock Prediction...");
    window.location.href = "index.html";
}

// 辅助功能 - 设置API密钥
async function setApiKeys(apiKeys) {
    try {
        const response = await fetch('/set-api-keys', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(apiKeys)
        });
        
        const data = await response.json();
        return data.success;
    } catch (error) {
        console.error("Error setting API keys:", error);
        return false;
    }
}

// 检查toggle函数是否已经存在，否则定义一个基本版本
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

// 检查loadSavedAgentsList函数是否已经存在，否则定义一个基本版本
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
            
            // 创建列表HTML
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

async function fetchStockData() {
    let symbols = document.getElementById("stockSymbols").value;
    let resultDiv = document.getElementById("result");

    if (!symbols) {
      resultDiv.innerHTML = "<p style='color: red; '>Please enter stock symbols.</p>";
      return;
    }

    resultDiv.innerHTML = "<p>Fetching data...</p>";

    try {
      let response = await fetch(`/investment_research?question=${encodeURIComponent(symbols)}`);

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      let data = await response.text(); // Get raw response as text
      resultDiv.innerHTML = `<pre>${data}</pre>`; // Display full raw response

    } catch (error) {
      resultDiv.innerHTML = `<p style='color: red;'>Failed to fetch stock data: ${error.message}</p>`;
    }
}

// 将核心函数暴露给window对象，使sidebar.js可以使用
window.loadSavedAgent = loadSavedAgent;
window.loadAgentAndRedirect = loadAgentAndRedirect;
window.listSavedAgents = listSavedAgents;
window.resetAgentForm = resetAgentForm;