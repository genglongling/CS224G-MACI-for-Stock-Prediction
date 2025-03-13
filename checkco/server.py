import os
from langchain_together import ChatTogether
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.utilities import PythonREPL
from langgraph.types import Command
from typing import Literal
from typing_extensions import TypedDict

import getpass
import os
import json
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from IPython.display import Image, display
from datetime import datetime

import auth

# Global variables to store API keys
tavily_api_key = None
together_api_key = None
users = {}  # Store user information and their API keys
selected_model = "meta-llama/Llama-Vision-Free" # Default model
custom_api_url = None  # Store custom API URL
custom_model_name = None  # Store custom model name
is_custom_api = False  # Flag to indicate custom API usage

from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import MessagesState, START, END
from langgraph.types import Command
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.messages import BaseMessage
from typing import Sequence
from typing_extensions import Annotated

# Define available agents
members = ["web_researcher", "rag", "nl2sql"]
# Add FINISH as an option for task completion
options = members + ["FINISH"]

# Create system prompt for supervisor
system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    f" following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)

# Define router type for structured output
class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal["web_researcher", "rag", "nl2sql", "FINISH"]  # Add all workers here

# Function to initialize LLM and tools
def initialize_llm_and_tools():
    global llm, web_search_tool, websearch_agent, selected_model, is_custom_api, custom_api_url, custom_model_name
    
    # Verify API keys are set
    if not os.getenv("TAVILY_API_KEY") or not os.getenv("TOGETHER_API_KEY"):
        print("API keys not set")
        return False
    
    try:
        # Try to initialize components without strict validation first
        try:
            # Create components with the provided API keys and selected model
            llm = ChatTogether(model_name=selected_model)
            web_search_tool = TavilySearchResults(max_results=5, api_key=os.getenv("TAVILY_API_KEY"))
            websearch_agent = create_agent(llm, [web_search_tool])
            
            # 简单测试以验证组件是否正常工作
            # 测试LLM
            test_response = llm.invoke("Hello, are you working?")
            print("LLM test response received")
            
            # 测试搜索工具
            test_search = web_search_tool.invoke("test query")
            print("Search tool test response received")
            
            print(f"LLM (model: {selected_model}) and tools initialized and tested successfully")
            return True
            
        except Exception as component_error:
            print(f"Component initialization error: {component_error}")
            
            # 如果组件初始化失败，尝试基本API验证
            import requests
            from requests.exceptions import RequestException
            
            # 基本验证Tavily
            try:
                tavily_key = os.getenv("TAVILY_API_KEY")
                tavily_test_url = "https://api.tavily.com/search"
                tavily_payload = {
                    "query": "test",
                    "search_depth": "basic",
                    "max_results": 1
                }
                tavily_headers = {
                    "Content-Type": "application/json",
                    "X-API-Key": tavily_key
                }
                
                tavily_response = requests.post(
                    tavily_test_url, 
                    json=tavily_payload,
                    headers=tavily_headers,
                    timeout=5
                )
                
                if tavily_response.status_code >= 400:
                    print(f"Tavily API key validation failed with status {tavily_response.status_code}")
                    return False
                    
            except RequestException as e:
                print(f"Tavily API connection error: {e}")
                return False
            
            # 基本验证Together API或自定义API
            try:
                together_key = os.getenv("TOGETHER_API_KEY")
                together_headers = {"Authorization": f"Bearer {together_key}"}
                together_test_url = "https://api.together.xyz/v1/models"
                
                together_response = requests.get(
                    together_test_url,
                    headers=together_headers,
                    timeout=5
                )
                
                if together_response.status_code >= 400:
                    print(f"Together API key validation failed with status {together_response.status_code}")
                    return False
                    
            except RequestException as e:
                print(f"Together API connection error: {e}")
                return False
                
            # 如果基本验证通过但组件初始化失败
            print("API keys appear valid but component initialization failed")
            return False
            
    except Exception as e:
        print(f"Error in validation process: {e}")
        return False

# Create supervisor node function
def supervisor_node(state: MessagesState) -> Command[Literal["web_researcher", "rag", "nl2sql", "__end__"]]:
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    print(f"Next Worker: {goto}")
    if goto == "FINISH":
        goto = END
    return Command(goto=goto)

def rag_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    # 这里是RAG（检索增强生成）节点的实现
    # 目前只返回一个简单的消息，实际应用中应该实现RAG功能
    return Command(
        update={
            "messages": [
                HumanMessage(content="RAG processing completed. No documents were retrieved at this time.", name="rag")
            ]
        },
        goto="supervisor",
    )

def nl2sql_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    # 这里是自然语言到SQL查询节点的实现
    # 目前只返回一个简单的消息，实际应用中应该实现NL2SQL功能
    return Command(
        update={
            "messages": [
                HumanMessage(content="NL2SQL processing completed. No SQL queries were generated at this time.", name="nl2sql")
            ]
        },
        goto="supervisor",
    )

class AgentState(TypedDict):
    """The state of the agent."""
    messages: Sequence[BaseMessage] #Annotated[Sequence[BaseMessage], add_messages]

def create_agent(llm, tools):
    llm_with_tools = llm.bind_tools(tools)
    def chatbot(state: AgentState):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("agent", chatbot)

    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges(
        "agent",
        tools_condition,
    )
    graph_builder.add_edge("tools", "agent")
    graph_builder.set_entry_point("agent")
    return graph_builder.compile()

def web_research_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    result = websearch_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="web_researcher")
            ]
        },
        goto="supervisor",
    )

def process_query_streaming(handler, query):
    print(f"---- Start process_query_streaming: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")

    """Process query and send results in real-time with clean, user-friendly output"""
    # Use local instances instead of global variables
    local_llm = None
    local_websearch_agent = None
    
    try:
        # Check if API keys are set
        print(f"---- Check if API keys are set: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")

        if not os.getenv("TAVILY_API_KEY") or not os.getenv("TOGETHER_API_KEY"):
            handler.send_sse_message({
                "type": "error",
                "data": "API keys are not set. Please refresh the page and enter your API keys."
            })
            return
        
        # Send an immediate update
        handler.send_sse_message({
            "type": "status_update",
            "data": "Starting to process your query: " + query
        })
        
        # Initialize local LLM and tools for this request
        local_llm = ChatTogether(model_name=selected_model)
        web_search_tool = TavilySearchResults(max_results=5, api_key=os.getenv("TAVILY_API_KEY"))
        local_websearch_agent = create_agent(local_llm, [web_search_tool])
        
        # Create processing graph
        print(f"---- Creating processing graph: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
        builder = StateGraph(MessagesState)
        builder.add_edge(START, "supervisor")
        builder.add_node("supervisor", supervisor_node)
        builder.add_node("web_researcher", web_research_node)

        # Add these nodes if they're implemented
        builder.add_node("rag", rag_node)  # Make sure rag_node is implemented
        builder.add_node("nl2sql", nl2sql_node)  # Make sure nl2sql_node is implemented

        graph = builder.compile()

        try:
            # No need to display technical graph visualization to users
            print("Processing graph initialized")
            print(f"---- Graph initialized: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
            handler.send_sse_message({
                "type": "status_update",
                "data": "Searching for relevant information..."
            })
        except Exception as e:
            print(f"---- Error encountered: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
            handler.send_sse_message({
                "type": "error",
                "data": f"Error in query processing: {str(e)}"
            })
        
        # Collect search results and processing outputs
        search_results = []
        analysis_steps = []
        final_analysis = ""
        print(f"---- Create final_analysis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
        
        # Execute graph flow and send updates incrementally
        print(f"---- Starting graph execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
        step_counter = 0
        try:
            # Get iterator instead of using for loop directly
            stream_iterator = graph.stream(
                    {"messages": [("user", query)]},
                    {"recursion_limit": 5},
                    subgraphs=True,
            )
            
            # Manually iterate to have better control
            for s in stream_iterator:
                # Convert output to readable string for logging
                s_str = str(s)
                print(s)  # Keep original terminal output
                print(f"---- Print s: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                
                # Extract meaningful information from the step
                if isinstance(s, tuple) and len(s) >= 2:
                    # Track which agent is processing
                    if s[0] and isinstance(s[0], str) and "web_researcher" in s[0]:
                        print(f"---- Web researcher active: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                        step_description = "Researching relevant information..."
                        analysis_steps.append(step_description)
                        handler.send_sse_message({
                            "type": "processing_step",
                            "data": step_description
                        })
                    
                    # Extract search results if available
                    if isinstance(s[1], dict):
                        # Extract tool responses (search results)
                        if 'tools' in s[1] and 'messages' in s[1]['tools']:
                            print(f"---- Processing tool messages: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                            for msg in s[1]['tools']['messages']:
                                if hasattr(msg, 'content') and msg.content and msg.name == 'tavily_search_results_json':
                                    try:
                                        # Parse search results
                                        print(f"---- Parsing search results: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                                        import json
                                        content = msg.content
                                        if content.startswith('[') and content.endswith(']'):
                                            items = json.loads(content)
                                            for item in items:
                                                if 'url' in item and 'content' in item:
                                                    # Add to search results if not already present
                                                    result_item = {
                                                        'source': item['url'],
                                                        'content': item['content']
                                                    }
                                                    if result_item not in search_results:
                                                        search_results.append(result_item)
                                                        
                                            # Send search results update
                                            print(f"---- Sending search results: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                                            handler.send_sse_message({
                                                "type": "search_results",
                                                "items": search_results[-3:] if len(search_results) > 3 else search_results  # Send the latest results
                                            })
                                    except Exception as e:
                                        print(f"---- Error parsing results: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                                        print(f"Error parsing search results: {str(e)}")
                        
                        # Extract AI analysis if available
                        if 'agent' in s[1] and 'messages' in s[1]['agent']:
                            print(f"---- Processing agent messages: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                            for msg in s[1]['agent']['messages']:
                                if hasattr(msg, 'content') and msg.content:
                                    # This is likely the AI's analysis
                                    print(f"---- Found AI analysis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                                    final_analysis = msg.content
                                    handler.send_sse_message({
                                        "type": "main_response",
                                        "data": final_analysis
                                    })
                
                step_counter += 1
                if step_counter == 4:  # Limiting steps for now
                    print(f"---- Step limit reached: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                    # Try to explicitly close the stream iterator (if supported)
                    if hasattr(stream_iterator, 'close'):
                        print(f"---- Closing stream iterator: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                        stream_iterator.close()
                        print(f"---- stream_iterator closed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                    # Try to send a cancel signal to the graph (if supported)
                    if hasattr(graph, 'cancel') and callable(graph.cancel):
                        print(f"---- Cancelling graph: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                        graph.cancel()
                    # Force break the loop regardless    
                    break
                
                # Small delay to allow frontend to process
                print(f"---- time.sleep(0.1): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                time.sleep(0.1)
            
            # Execute next steps immediately after exiting the loop
            print(f"---- Stream processing complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                
        except Exception as e:
            print(f"---- Exception in graph execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
            handler.send_sse_message({
                "type": "error",
                "data": f"Error processing query: {str(e)}"
            })
        
        # If we haven't received a final analysis yet, generate one from the search results
        print(f"---- Checking for final analysis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
        if not final_analysis and search_results:
            try:
                # Create a dynamic summary prompt based on the user's query
                # This avoids hardcoding specific topics or expectations
                print(f"---- Creating summary prompt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                summary_prompt = f"Based on the following information related to the user's query: '{query}', provide a concise and helpful summary. Information:\n\n"
                for result in search_results:
                    summary_prompt += f"- {result['content']}\n\n"
                
                handler.send_sse_message({
                    "type": "status_update",
                    "data": "Analyzing gathered information..."
                })
                
                # Use the LLM to generate a summary
                print(f"---- Invoking LLM for summary: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                summary_response = local_llm.invoke(summary_prompt)
                final_analysis = summary_response.content
                print(f"---- final_analysis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                print(final_analysis)
                
                # Send the generated summary
                print(f"---- Sending final analysis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                handler.send_sse_message({
                    "type": "main_response",
                    "data": final_analysis
                })
            except Exception as e:
                print(f"---- Error generating summary: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
                print(f"Error generating summary: {str(e)}")
                final_analysis = "Unable to generate a summary from the search results. Please try refining your query."
                handler.send_sse_message({
                    "type": "main_response",
                    "data": final_analysis
                })
        
        # Send final summary results
        print(f"---- Preparing final response: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
        summary = {
            "type": "final_response",
            "main_response": final_analysis if final_analysis else "Analysis could not be completed. Please try again.",
            "search_results": search_results
        }
        
        print(f"---- Sending final summary: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
        print(final_analysis)
        handler.send_sse_message(summary)
        
    except Exception as e:
        # Handle any unexpected exceptions
        print(f"---- Critical error in processing: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
        print(f"Error: {str(e)}")
        handler.send_sse_message({
            "type": "error",
            "data": f"An unexpected error occurred: {str(e)}"
        })
    finally:
        # Ensure resources are cleaned up
        print(f"---- Cleaning up resources: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
        
        # Clean up LLM resources if possible
        if local_llm and hasattr(local_llm, 'close'):
            try:
                local_llm.close()
            except Exception as cleanup_error:
                print(f"Error during LLM cleanup: {str(cleanup_error)}")
        
        # Clean up agent resources if possible
        if local_websearch_agent and hasattr(local_websearch_agent, 'close'):
            try:
                local_websearch_agent.close()
            except Exception as cleanup_error:
                print(f"Error during agent cleanup: {str(cleanup_error)}")
        
        # Send completion event to ensure frontend knows processing is done
        try:
            handler.send_sse_message("Processing complete", event="complete")
        except Exception as event_error:
            print(f"Error sending completion event: {str(event_error)}")
            
        print(f"---- Request processing finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")

# Modified request handler class to add API key setting method
class RequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS, POST')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        global tavily_api_key, together_api_key
        # First, declare the global variables
        global selected_model, custom_api_url, custom_model_name, is_custom_api
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            if self.path == '/set-api-keys':
                print("API key setting request received")
                # Handle API key setting request
                tavily_api_key = data.get('tavily_api_key', '')
                together_api_key = data.get('together_api_key', '')
                user_info = data.get('user', {})
                
                # 获取模型信息，如果有的话
                model_name = data.get('model_name', '')
                if model_name:
                    global selected_model
                    selected_model = model_name
                    print(f"Model from API key request: {selected_model}")
                
                # Check if API keys are provided
                if not tavily_api_key or not together_api_key:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False, 
                        'error': 'Both Tavily and Together API keys are required.'
                    }).encode())
                    return
                
                # If user info exists, store the user's API keys
                if user_info and 'email' in user_info:
                    user_email = user_info['email']
                    users[user_email] = {
                        'info': user_info,
                        'tavily_api_key': tavily_api_key,
                        'together_api_key': together_api_key
                    }
                    
                    # 存储用户的自定义API设置，如果有的话
                    global is_custom_api, custom_api_url, custom_model_name
                    if is_custom_api and custom_api_url:
                        users[user_email]['is_custom_api'] = is_custom_api
                        users[user_email]['custom_api_url'] = custom_api_url
                        if custom_model_name:
                            users[user_email]['custom_model_name'] = custom_model_name
                    
                    print(f"User {user_email} has set API keys")
                    
                    # Save user API keys to auth module
                    auth.save_user_api_keys(user_email, tavily_api_key, together_api_key)
                
                # Set environment variables
                os.environ["TAVILY_API_KEY"] = tavily_api_key
                os.environ["TOGETHER_API_KEY"] = together_api_key
                
                print("API keys set in environment variables")
                
                # Initialize LLM and search tools and validate API keys
                try:
                    print("Starting initialization and validation...")
                    print(f"Using model: {selected_model}")
                    if is_custom_api:
                        print(f"Using custom API URL: {custom_api_url}")
                        if custom_model_name:
                            print(f"Using custom model name: {custom_model_name}")
                            
                    init_success = initialize_llm_and_tools()
                    
                    # Send response
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    if init_success:
                        print("Initialization successful")
                        response_data = {'success': True}
                        if is_custom_api:
                            response_data['custom_api'] = True
                            response_data['custom_api_url'] = custom_api_url
                            if custom_model_name:
                                response_data['custom_model_name'] = custom_model_name
                        self.wfile.write(json.dumps(response_data).encode())
                    else:
                        error_msg = 'API validation failed. The API keys may be incorrect or the services may be unavailable.'
                        print(error_msg)
                        self.wfile.write(json.dumps({
                            'success': False, 
                            'error': error_msg
                        }).encode())
                    
                except Exception as init_error:
                    print(f"Error during initialization: {str(init_error)}")
                    self.send_response(200)  # Still send 200 to let the client process the error
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False, 
                        'error': f'Error during initialization: {str(init_error)}'
                    }).encode())
                
            elif self.path == '/login':
                # Handle login request
                email = data.get('email', '')
                password = data.get('password', '')
                
                if not email or not password:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': 'Email and password are required'
                    }).encode())
                    return
                
                success, result = auth.verify_user(email, password)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                if success:
                    # Login successful
                    self.wfile.write(json.dumps({
                        'success': True,
                        'user': {
                            'name': result['name'],
                            'email': email,
                            'provider': 'local'
                        }
                    }).encode())
                else:
                    # Login failed
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': result
                    }).encode())
                    
            elif self.path == '/register':
                # Handle registration request
                email = data.get('email', '')
                password = data.get('password', '')
                name = data.get('name', '')
                
                if not email or not password:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': 'Email and password are required'
                    }).encode())
                    return
                
                success, message = auth.register_user(email, password, name)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps({
                    'success': success,
                    'message': message
                }).encode())
                
            elif self.path == '/sso-login':
                # Handle SSO login request
                provider = data.get('provider', '')
                email = data.get('email', '')
                
                if not provider or not email:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': 'Provider and email are required'
                    }).encode())
                    return
                
                success, user = auth.sso_login(provider, email)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps({
                    'success': success,
                    'user': user
                }).encode())

            # Add a new handler for setting the model in the RequestHandler class
            elif self.path == '/set-model':
                
                
                # Handle model selection request
                model_name = data.get('model_name', '')
                user_info = data.get('user', {})
                
                # Check if we're using a custom API connection
                is_custom = data.get('is_custom_api', False)
                custom_url = data.get('custom_api_url', '')
                custom_model = data.get('custom_model_name', '')
                
                # Check if model name is provided
                if not model_name:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False, 
                        'error': 'Model name is required.'
                    }).encode())
                    return
                
                # Now set the variables after declaring them global
                selected_model = model_name
                is_custom_api = is_custom
                
                if is_custom:
                    if not custom_url:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'success': False, 
                            'error': 'Custom API URL is required when using custom API.'
                        }).encode())
                        return
                        
                    custom_api_url = custom_url
                    custom_model_name = custom_model
                    print(f"Custom API set to: {custom_api_url}")
                    if custom_model_name:
                        print(f"Custom model name: {custom_model_name}")
                else:
                    # Reset custom API settings when using predefined model
                    custom_api_url = None
                    custom_model_name = None
                    
                print(f"Model set to: {selected_model}")
                
                # If user info exists, update the user's model preference
                if user_info and 'email' in user_info:
                    user_email = user_info['email']
                    if user_email in users:
                        users[user_email]['selected_model'] = model_name
                        if is_custom:
                            users[user_email]['custom_api_url'] = custom_api_url
                            users[user_email]['custom_model_name'] = custom_model_name
                            users[user_email]['is_custom_api'] = is_custom
                    else:
                        users[user_email] = {
                            'info': user_info,
                            'selected_model': model_name
                        }
                        if is_custom:
                            users[user_email]['custom_api_url'] = custom_api_url
                            users[user_email]['custom_model_name'] = custom_model_name
                            users[user_email]['is_custom_api'] = is_custom
                            
                    print(f"User {user_email} has set model to {model_name}")
                    if is_custom:
                        print(f"User {user_email} is using custom API: {custom_api_url}")

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response_data = {
                    'success': True,
                    'model': selected_model
                }
                if is_custom:
                    response_data['custom_api_url'] = custom_api_url
                    if custom_model_name:
                        response_data['custom_model_name'] = custom_model_name
                        
                self.wfile.write(json.dumps(response_data).encode())
                
        except Exception as e:
            # Handle any uncaught exceptions
            print(f"Error processing request: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False, 
                'error': f'Server error: {str(e)}'
            }).encode())

    def do_GET(self):
        """Handle GET requests, mainly for SSE connections"""
        if self.path.startswith('/query'):
            try:
                # Parse URL parameters
                query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                query = query_params.get('query', [''])[0]
                
                if not query:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Missing query parameter"}).encode())
                    return
                
                # Send response headers, set to SSE format
                self.send_response(200)
                self.send_header('Content-type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'keep-alive')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Send initial message immediately
                self.send_sse_message("Starting query processing: " + query)
                
                # Process query and send real-time updates
                process_query_streaming(self, query)
                
                # Send completion signal
                self.send_sse_message("Processing complete", event="complete")
                
            except Exception as e:
                # Handle exceptions
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        elif self.path == '/get-available-functions':
            try:
                # Send response headers
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
                self.send_header('Access-Control-Allow-Methods', 'GET')
                self.end_headers()
                
                # Return the available functions (members list)
                self.wfile.write(json.dumps({
                    'success': True,
                    'functions': members  # This is your global list of members
                }).encode())
                
            except Exception as e:
                print(f"Error serving available functions: {str(e)}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False, 
                    'error': f'Server error: {str(e)}'
                }).encode())
        else:
            # Handle other GET requests, such as static files
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Server is running. Use /query endpoint for queries.")
            
    def send_sse_message(self, data, event=None):
        """Send message in SSE format"""
        message = ""
        if event:
            message += f"event: {event}\n"
        
        # Convert data to JSON string
        if isinstance(data, str):
            json_data = json.dumps({"message": data})
        else:
            json_data = json.dumps(data)
            
        # Escape any data containing newlines
        encoded_data = json_data.replace('\n', '\\n')
        message += f"data: {encoded_data}\n\n"
        
        try:
            self.wfile.write(message.encode('utf-8'))
            self.wfile.flush()  # Ensure data is sent immediately
        except Exception as e:
            print(f"Error sending SSE message: {e}")

# Original process_query function kept for backward compatibility
def process_query(query: str):
    # Create a list to collect all outputs
    collected_outputs = []
    collected_outputs.append(f"Query received: {query}")
    
    builder = StateGraph(MessagesState)
    builder.add_edge(START, "supervisor")
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("web_researcher", web_research_node)
    # builder.add_node("rag", rag_node)
    # builder.add_node("nl2sql", nl2sql_node)
    graph = builder.compile()

    try:
        display(Image(graph.get_graph().draw_mermaid_png()))
        collected_outputs.append("Processing graph initialized")
    except Exception as e:
        collected_outputs.append(f"Error creating processing graph: {str(e)}")
    
    result_data = []
    i = 0
    try:
        for s in graph.stream(
                {"messages": [("user", query)]},
                {"recursion_limit": 100},
                subgraphs=True,
        ):
            # Convert output to readable string and collect
            s_str = str(s)
            collected_outputs.append(s_str)
            collected_outputs.append("----")
            collected_outputs.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            collected_outputs.append("----")
            
            # Try to extract useful result data
            if isinstance(s, tuple) and len(s) >= 2:
                if isinstance(s[1], dict) and 'tools' in s[1]:
                    if 'messages' in s[1]['tools']:
                        for msg in s[1]['tools']['messages']:
                            if hasattr(msg, 'content') and msg.content:
                                try:
                                    # Try to extract specific data from content
                                    import json
                                    content = msg.content
                                    if content.startswith('[') and content.endswith(']'):
                                        items = json.loads(content)
                                        for item in items:
                                            if 'url' in item and 'content' in item:
                                                result_data.append({
                                                    'source': item['url'],
                                                    'content': item['content'][:200] + '...' if len(item['content']) > 200 else item['content']
                                                })
                                except Exception as e:
                                    collected_outputs.append(f"Error parsing results: {str(e)}")
            
            # Keep original terminal output
            print(s)
            print(f"---- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
            i = i + 1
            if i == 4:
                break
    except Exception as e:
        collected_outputs.append(f"Error processing query: {str(e)}")
    
    # Build nice-looking response
    final_response = ""
    
    # Add result summary
    if result_data:
        final_response += "## Search Results Summary\n\n"
        for idx, item in enumerate(result_data, 1):
            final_response += f"{idx}. **Source**: {item['source']}\n"
            final_response += f"   **Content**: {item['content']}\n\n"
    
    # Add original processing logs
    final_response += "\n## Processing Logs\n\n"
    final_response += "\n".join(collected_outputs)
    
    print("Response length:", len(final_response))
    return final_response

# Start HTTP server
def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()