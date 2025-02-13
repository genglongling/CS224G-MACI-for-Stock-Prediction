
import os
from langchain_together import ChatTogether
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.utilities import PythonREPL
from langgraph.types import Command
from typing import Literal
from typing_extensions import TypedDict

# Set your Together AI API key as an environment variable or directly in the code
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("TAVILY_API_KEY")
_set_env("TOGETHER_API_KEY")

from langchain_together import ChatTogether

llm = ChatTogether(model_name="meta-llama/Llama-3.3-70B-Instruct-Turbo")

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

# class ToolNode:
#     def __init__(self, tools):
#         self.tools = tools
#
#     def invoke(self, state):
#         # Define logic for invoking tools here
#         return {"messages": ["Some result from tool invocation"]}

# Define the condition for using tools

from langchain_community.tools.tavily_search import TavilySearchResults

# Define a web search tool (using Tavily for web search)
web_search_tool = TavilySearchResults(max_results=5, api_key=os.getenv("TAVILY_API_KEY"))


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

websearch_agent = create_agent(llm, [web_search_tool])

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
#
# rag_agent = create_agent(llm, [retriever_tool])
#
# def rag_node(state: MessagesState) -> Command[Literal["supervisor"]]:
#     result = rag_agent.invoke(state)
#     return Command(
#         update={
#             "messages": [
#                 HumanMessage(content=result["messages"][-1].content, name="rag")
#             ]
#         },
#         goto="supervisor",
#     )
#
#
# nl2sql_agent = create_agent(llm, [nl2sql_tool])
#
# def nl2sql_node(state: MessagesState) -> Command[Literal["supervisor"]]:
#     result = nl2sql_agent.invoke(state)
#     return Command(
#         update={
#             "messages": [
#                 HumanMessage(content=result["messages"][-1].content, name="nl2sql")
#             ]
#         },
#         goto="supervisor",
#     )


from flask import Flask, request, jsonify, render_template

app = Flask(__name__)


# Function to process the query
def process_query(query: str):
    # Simulating AI processing (replace this with your actual logic)
    #response = f"Processed response for (top 5): {query}"
    response = "this is a testing"
    return response


@app.route('/')
def index():
    return render_template('index.html')  # Serve the HTML page


@app.route('/query', methods=['POST'])
def handle_post():
    data = request.get_json()
    query = data.get("query", "")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    response = process_query(query)  # Process the query
    return jsonify({"response": response})  # Send JSON response


if __name__ == '__main__':
    app.run(debug=True, port=8000)  # Runs on http://localhost:8000
