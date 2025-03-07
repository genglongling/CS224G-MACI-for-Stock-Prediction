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

# Global variables to store API keys
tavily_api_key = None
together_api_key = None
users = {}  # Store user information and their API keys

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
    next: Literal["web_researcher", "FINISH"] # "rag", "nl2sql",

# Function to initialize LLM and tools
def initialize_llm_and_tools():
    global llm, web_search_tool, websearch_agent
    
    # Initialize LLM
    try:
        llm = ChatTogether(model_name="meta-llama/Llama-3.3-70B-Instruct-Turbo")
        
        # Initialize search tool
        web_search_tool = TavilySearchResults(max_results=5, api_key=os.getenv("TAVILY_API_KEY"))
        
        # Initialize web search agent
        websearch_agent = create_agent(llm, [web_search_tool])
        
        print("LLM and tools initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing LLM and tools: {e}")
        return False

# Create supervisor node function
def supervisor_node(state: MessagesState) -> Command[Literal["web_researcher", "__end__"]]: #"rag", "nl2sql",
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    print(f"Next Worker: {goto}")
    if goto == "FINISH":
        goto = END
    return Command(goto=goto)

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
    """Process query and send results in real-time with terminal output as primary content"""
    global llm, websearch_agent
    
    # Check if API keys are set
    if not os.getenv("TAVILY_API_KEY") or not os.getenv("TOGETHER_API_KEY"):
        handler.send_sse_message({
            "type": "error",
            "data": "API keys are not set. Please refresh the page and enter your API keys."
        })
        return
    
    # Send an immediate update
    handler.send_sse_message("Starting query processing: " + query)
    
    # Create processing graph
    builder = StateGraph(MessagesState)
    builder.add_edge(START, "supervisor")
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("web_researcher", web_research_node)
    graph = builder.compile()

    try:
        display(Image(graph.get_graph().draw_mermaid_png()))
        handler.send_sse_message("Processing graph initialized")
    except Exception as e:
        handler.send_sse_message(f"Error creating processing graph: {str(e)}")
    
    # Send message that graph is initialized
    handler.send_sse_message("Starting query execution...")
    
    # Collect all terminal outputs to show as the main response
    all_terminal_outputs = []
    final_output = ""
    search_results = []
    
    # Execute graph flow and send updates incrementally
    i = 0
    try:
        for s in graph.stream(
                {"messages": [("user", query)]},
                {"recursion_limit": 100},
                subgraphs=True,
        ):
            # Convert output to readable string
            s_str = str(s)
            all_terminal_outputs.append(s_str)
            all_terminal_outputs.append("----")
            
            # Add to final output that will be shown as the main response
            final_output += s_str + "\n----\n"
            
            # Send update for each step as terminal output (for debugging)
            handler.send_sse_message({
                "type": "terminal_output", 
                "step": i, 
                "data": s_str
            })
            
            # Send current output as a main response update
            handler.send_sse_message({
                "type": "main_response",
                "data": final_output
            })
            
            # Process any structured data if possible
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
                                                search_results.append({
                                                    'source': item['url'],
                                                    'content': item['content']
                                                })
                                except Exception as e:
                                    handler.send_sse_message(f"Error parsing results: {str(e)}")
            
            # Keep original terminal output
            print(s)
            print("----")
            i = i + 1
            if i == 4:
                break
            
            # Small delay to allow frontend to process
            time.sleep(0.1)
    except Exception as e:
        handler.send_sse_message(f"Error processing query: {str(e)}")
    
    # Send final summary results with terminal outputs as the main content
    summary = {
        "type": "final_response",
        "main_response": final_output,
        "has_search_results": len(search_results) > 0,
        "search_results": search_results
    }
    
    handler.send_sse_message(summary)

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
        
        if self.path == '/set-api-keys':
            # Handle API key setting request
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                tavily_api_key = data.get('tavily_api_key', '')
                together_api_key = data.get('together_api_key', '')
                user_info = data.get('user', {})
                
                # If user info exists, store the user's API keys
                if user_info and 'email' in user_info:
                    user_email = user_info['email']
                    users[user_email] = {
                        'info': user_info,
                        'tavily_api_key': tavily_api_key,
                        'together_api_key': together_api_key
                    }
                    print(f"User {user_email} has set API keys")
                
                # Set environment variables
                if tavily_api_key:
                    os.environ["TAVILY_API_KEY"] = tavily_api_key
                if together_api_key:
                    os.environ["TOGETHER_API_KEY"] = together_api_key
                
                # Initialize LLM and search tools
                init_success = initialize_llm_and_tools()
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                if init_success:
                    self.wfile.write(json.dumps({'success': True}).encode())
                else:
                    self.wfile.write(json.dumps({'success': False, 'error': 'Failed to initialize LLM and tools'}).encode())
                
            except Exception as e:
                # Send error response
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
            
        elif self.path == '/query':
            # Original query processing code
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data)
                query = data.get('query', '')

                self.send_response(200)
                self.send_header('Content-type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'keep-alive')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                self.send_sse_message("Starting query processing: " + query)
                
                process_query_streaming(self, query)
                
                self.send_sse_message("Processing complete", event="complete")
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

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
            print("----")
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