"""
Function 2: Q&A module
This module handles general question answering functionality, like "what is apple stock price today?"
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Callable
from langchain_together import ChatTogether
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph
from langgraph.graph import MessagesState, START, END
from langgraph.types import Command
from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
from typing_extensions import TypedDict

class QAModule:
    """Q&A module that processes queries using LLM and web search."""
    
    def __init__(self):
        self.llm = None
        self.web_search_tool = None
        self.websearch_agent = None
        self.model_name = None
        self.model_name = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    
    def initialize(self, together_api_key, tavily_api_key, model_name=None):
        """Initialize LLM and search tool with provided API keys."""
        if model_name:
            self.model_name = model_name
        try:
            # Set environment variables
            os.environ["TAVILY_API_KEY"] = tavily_api_key
            os.environ["TOGETHER_API_KEY"] = together_api_key
            
            # Create components with the provided API keys
            self.llm = ChatTogether(model_name=self.model_name)
            self.web_search_tool = TavilySearchResults(max_results=5, api_key=tavily_api_key)
            self.websearch_agent = self._create_agent(self.llm, [self.web_search_tool])
            
            return True
        except Exception as e:
            print(f"Error initializing Q&A module: {str(e)}")
            return False
        
    def update_model(self, model_name):
        """Update the model being used."""
        try:
            old_model = self.model_name
            self.model_name = model_name
            self.llm = ChatTogether(model_name=self.model_name)
            return True, f"Model updated from {old_model} to {self.model_name}"
        except Exception as e:
            return False, f"Error updating model: {str(e)}"

    def _create_agent(self, llm, tools):
        """Create an agent with the provided LLM and tools."""
        from langgraph.prebuilt import create_react_agent
        return create_react_agent(llm, tools)
    
    def _supervisor_node(self, state: MessagesState) -> Command[Literal["web_researcher", "__end__"]]:
        """Supervise the processing flow."""
        # Define system prompt for supervisor
        system_prompt = (
            "You are a supervisor tasked with managing a conversation between the"
            " following workers: web_researcher. Given the following user request,"
            " respond with the worker to act next. Each worker will perform a"
            " task and respond with their results and status. When finished,"
            " respond with FINISH."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
        
        # Create router for structured output
        class Router(TypedDict):
            """Worker to route to next. If no workers needed, route to FINISH."""
            next: Literal["web_researcher", "FINISH"]
        
        response = self.llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        print(f"Next Worker: {goto}")
        if goto == "FINISH":
            goto = END
        return Command(goto=goto)
    
    def _web_research_node(self, state: MessagesState) -> Command[Literal["supervisor"]]:
        """Execute web research."""
        result = self.websearch_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="web_researcher")
                ]
            },
            goto="supervisor",
        )
    
    def process_query(self, query: str, sse_handler=None):
        """
        Process a query with web search and LLM summarization.
        
        Args:
            query: The user's question
            sse_handler: Optional handler for server-sent events
        
        Returns:
            Dict with the final response and search results
        """
        print(f"---- Start process_query: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----")
        
        if sse_handler:
            sse_handler({
                "type": "status_update",
                "data": "Starting to process your query: " + query
            })
        
        try:
            # Create processing graph
            builder = StateGraph(MessagesState)
            builder.add_edge(START, "supervisor")
            builder.add_node("supervisor", self._supervisor_node)
            builder.add_node("web_researcher", self._web_research_node)
            graph = builder.compile()
            
            if sse_handler:
                sse_handler({
                    "type": "status_update",
                    "data": "Searching for relevant information..."
                })
            
            # Collect search results and processing outputs
            search_results = []
            final_analysis = ""
            
            # Execute graph flow and send updates incrementally
            step_counter = 0
            try:
                # Get iterator for streaming
                stream_iterator = graph.stream(
                    {"messages": [("user", query)]},
                    {"recursion_limit": 5},
                    subgraphs=True,
                )
                
                # Process stream data
                for s in stream_iterator:
                    print(s)
                    
                    # Extract meaningful information from the step
                    if isinstance(s, tuple) and len(s) >= 2:
                        # Track which agent is processing
                        if s[0] and isinstance(s[0], str) and "web_researcher" in s[0]:
                            step_description = "Researching relevant information..."
                            if sse_handler:
                                sse_handler({
                                    "type": "processing_step",
                                    "data": step_description
                                })
                        
                        # Extract search results if available
                        if isinstance(s[1], dict):
                            # Extract tool responses (search results)
                            if 'tools' in s[1] and 'messages' in s[1]['tools']:
                                for msg in s[1]['tools']['messages']:
                                    if hasattr(msg, 'content') and msg.content and msg.name == 'tavily_search_results_json':
                                        try:
                                            # Parse search results
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
                                                if sse_handler:
                                                    sse_handler({
                                                        "type": "search_results",
                                                        "items": search_results[-3:] if len(search_results) > 3 else search_results
                                                    })
                                        except Exception as e:
                                            print(f"Error parsing search results: {str(e)}")
                            
                            # Extract AI analysis if available
                            if 'agent' in s[1] and 'messages' in s[1]['agent']:
                                for msg in s[1]['agent']['messages']:
                                    if hasattr(msg, 'content') and msg.content:
                                        # This is likely the AI's analysis
                                        final_analysis = msg.content
                                        if sse_handler:
                                            sse_handler({
                                                "type": "main_response",
                                                "data": final_analysis
                                            })
                    
                    step_counter += 1
                    if step_counter == 4:  # Limiting steps for now
                        # Try to explicitly close the stream iterator (if supported)
                        if hasattr(stream_iterator, 'close'):
                            stream_iterator.close()
                        # Try to send a cancel signal to the graph (if supported)
                        if hasattr(graph, 'cancel') and callable(graph.cancel):
                            graph.cancel()
                        break
                    
                    # Small delay to allow frontend to process
                    time.sleep(0.1)
                
            except Exception as e:
                print(f"Exception in graph execution: {str(e)}")
                if sse_handler:
                    sse_handler({
                        "type": "error",
                        "data": f"Error processing query: {str(e)}"
                    })
            
            # If we haven't received a final analysis yet, generate one from the search results
            if not final_analysis and search_results:
                try:
                    # Create a dynamic summary prompt based on the user's query
                    summary_prompt = f"Based on the following information related to the user's query: '{query}', provide a concise and helpful summary. Information:\n\n"
                    print(summary_prompt)
                    for result in search_results:
                        summary_prompt += f"- {result['content']}\n\n"
                    
                    if sse_handler:
                        sse_handler({
                            "type": "status_update",
                            "data": "Analyzing gathered information..."
                        })
                    
                    # Use the LLM to generate a summary
                    summary_response = self.llm.invoke(summary_prompt)
                    final_analysis = summary_response.content
                    
                    # Send the generated summary
                    if sse_handler:
                        sse_handler({
                            "type": "main_response",
                            "data": final_analysis
                        })
                except Exception as e:
                    print(f"Error generating summary: {str(e)}")
                    final_analysis = "Unable to generate a summary from the search results. Please try refining your query."
                    if sse_handler:
                        sse_handler({
                            "type": "main_response",
                            "data": final_analysis
                        })
            
            # Prepare final results
            result = {
                "main_response": final_analysis if final_analysis else "Analysis could not be completed. Please try again.",
                "search_results": search_results
            }
            
            if sse_handler:
                sse_handler({
                    "type": "final_response",
                    "main_response": result["main_response"],
                    "search_results": result["search_results"]
                })
            
            return result
            
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            print(error_msg)
            if sse_handler:
                sse_handler({
                    "type": "error",
                    "data": error_msg
                })
            return {"main_response": error_msg, "search_results": []}
        finally:
            # Clean up resources if necessary
            pass

# Create a singleton instance for import
qa_module = QAModule()

# For direct testing
if __name__ == "__main__":
    # Example usage
    api_key = input("Enter your Together API key: ")
    tavily_key = input("Enter your Tavily API key: ")
    
    if qa_module.initialize(api_key, tavily_key):
        query = input("Enter your question: ")
        result = qa_module.process_query(query)
        print("\nFinal Analysis:")
        print(result["main_response"])
        print("\nSources:")
        for idx, source in enumerate(result["search_results"], 1):
            print(f"{idx}. {source['source']}")