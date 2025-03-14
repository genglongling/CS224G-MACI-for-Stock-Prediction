
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

# TAVILY_API_KEY: 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
# together api: 5efb8de8e762c4b798de6885afb380513339c22cb37628c76e9420fce30b5bac
_set_env("TAVILY_API_KEY")
_set_env("TOGETHER_API_KEY")
# os.environ["TOGETHER_API_KEY"] = "5efb8de8e762c4b798de6885afb380513339c22cb37628c76e9420fce30b5bac"  # Replace with your Together AI API Key

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




builder = StateGraph(MessagesState)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("web_researcher", web_research_node)
# builder.add_node("rag", rag_node)
# builder.add_node("nl2sql", nl2sql_node)
graph = builder.compile()

from IPython.display import Image, display

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    # You can put your exception handling code here
    pass

# Example: Complex Query Using Multiple Agents
# Function 1: real-time search, example: search through founder (real-time data+historical data)
input_question = "Find the founder of FutureSmart AI and then do a web research on him"
for s in graph.stream(
    {"messages": [("user", input_question)]},
    {"recursion_limit": 10},
    subgraphs=True,
):
    print(s)
    print("----")


# Function 2: Q\&A, example: what is apple stock price today? ex: stock price -> general llm
# Function 3: simple to complex calculation and induction, example: based the information of apple stock until today, predict stock price of apple tomorrow -> specialized fin-llm
# Function 4: advanced machine learning reasoning ability (e.g. LSTM), example: https://www.alphavantage.co/documentation/ -> api
# Function 5: planning ability (e.g. meta planning, first planning, second planning), example: constraints/members/tasks, generate a plan
# Function 6: decision making ability (e.g. validation, self-evaluation), example: -> example: recommendation
# Function 7: operation ability (e.g. replace some thought, generate plot, scheduling),
# example: generate plot of apple stock trend, generate financial analysis plot of apple company, scheduling
# example: recognize/generate latex, ppt, pdf, pictures of apple stock/company financial data 
# exmaple: schedule a call/flight
# before operation, human: confirm button
# verify the plan again or reversion



