import csv
import os
import json
import time
import requests
from typing import Any, AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from magentic import (
    AssistantMessage,
    SystemMessage,
    prompt,
    chatprompt,
    FunctionCall,
    UserMessage,
)
from pydantic import BaseModel

# 初始化 FastAPI 应用
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Alpha Vantage API Key
AV_API_KEY = os.getenv("AV_API_KEY") or "your_api_key_here"

# Agent 配置模型
class AgentConfig(BaseModel):
    data_source: str
    model_source: str
    framework_source: str
    features: list[str] | None = None
    constraints: str | None = None
    agent_name: str

# 静态路由
@app.get("/")
async def serve_home():
    return FileResponse("static/index.html")

@app.get("/generate_agent")
async def serve_generate_agent():
    return FileResponse("static/generate_agent.html")

session_config = {}  # 简单的临时全局存储

@app.post("/save_agent_config")
async def save_agent_config(config: AgentConfig):
    global CURRENT_AGENT_CONFIG
    CURRENT_AGENT_CONFIG = config.dict()
    return {"success": True, "message": "Agent config saved for session"}

# 保存 Agent 配置以供重用
@app.post("/save_agent_for_reuse")
async def save_agent_for_reuse(config: AgentConfig):
    try:
        save_dir = "saved_agents"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 使用时间戳和代理名称生成唯一 ID
        agent_id = f"{config.agent_name}_{int(time.time())}"
        filepath = os.path.join(save_dir, f"{agent_id}.json")
        
        # 保存配置
        agent_data = config.dict()
        agent_data["id"] = agent_id
        agent_data["created_at"] = time.time()
        
        with open(filepath, "w") as f:
            json.dump(agent_data, f, indent=4)
        
        return {"success": True, "agent_id": agent_id, "message": f"Agent saved as {agent_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save agent: {str(e)}")

# 列出所有保存的 Agent
@app.get("/list_saved_agents")
async def list_saved_agents():
    try:
        save_dir = "saved_agents"
        if not os.path.exists(save_dir):
            return {"success": True, "agents": []}
        
        agents = []
        for filename in os.listdir(save_dir):
            if filename.endswith(".json"):
                with open(os.path.join(save_dir, filename), "r") as f:
                    agent = json.load(f)
                    agents.append({
                        "id": agent["id"],
                        "name": agent["agent_name"],
                        "model": agent["model_source"],
                        "features": agent["features"],
                        "created_at": agent["created_at"]
                    })
        
        return {"success": True, "agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

# 加载特定 Agent
@app.get("/load_agent/{agent_id}")
async def load_agent(agent_id: str):
    try:
        filepath = os.path.join("saved_agents", f"{agent_id}.json")
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Agent not found")
        
        with open(filepath, "r") as f:
            agent = json.load(f)
        
        return {"success": True, "agent": agent}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load agent: {str(e)}")

# 删除特定 Agent
@app.delete("/delete_agent/{agent_id}")
async def delete_agent(agent_id: str):
    try:
        filepath = os.path.join("saved_agents", f"{agent_id}.json")
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Agent not found")
        
        os.remove(filepath)
        return {"success": True, "message": f"Agent {agent_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

# 投资研究路由（已有）
async def get_earnings_calendar(ticker: str, api_key: str = AV_API_KEY) -> dict:
    url = f"https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&symbol={ticker}&horizon=12month&apikey={api_key}"
    response = requests.get(url, timeout=30)
    decoded_content = response.content.decode("utf-8")
    cr = csv.reader(decoded_content.splitlines(), delimiter=",")
    data = list(cr)
    return {"data": data}


@app.get("/investment_research")
async def investment_research(question: str):
    return StreamingResponse(query(question), media_type="text/event-stream")

async def get_earnings_calendar(ticker: str, api_key: str = AV_API_KEY) -> dict:
    """Fetches upcoming earnings dates for a given ticker."""
    url = f"https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&symbol={ticker}&horizon=12month&apikey={api_key}"
    response = requests.get(url, timeout=30)
    decoded_content = response.content.decode("utf-8")
    cr = csv.reader(decoded_content.splitlines(), delimiter=",")
    data = list(cr)
    return {"data": data}


async def get_news_sentiment(
    ticker: str, limit: int = 5, api_key: str = AV_API_KEY
) -> list[dict]:
    """Fetches sentiment analysis on financial news related to the ticker."""
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={api_key}"
    response = requests.get(url, timeout=30).json().get("feed", [])[:limit]
    fields = [
        "time_published",
        "title",
        "summary",
        "topics",
        "overall_sentiment_score",
        "overall_sentiment_label",
    ]
    return [{field: article[field] for field in fields} for article in response]


async def get_daily_price(ticker: str, api_key: str = AV_API_KEY) -> dict[str, Any]:
    """Fetches daily price data for a given stock ticker."""
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={api_key}"
    response = requests.get(url, timeout=30).json()
    return response.get("Time Series (Daily)", {})


async def get_company_overview(
    ticker: str, api_key: str = AV_API_KEY
) -> dict[str, Any]:
    """Fetches fundamental company data like market cap, P/E ratio, and sector."""
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
    return requests.get(url, timeout=30).json()


async def get_sector_performance(api_key: str = AV_API_KEY) -> dict[str, Any]:
    """Fetches market-wide sector performance data."""
    url = f"https://www.alphavantage.co/query?function=SECTOR&apikey={api_key}"
    return requests.get(url, timeout=30).json()


@prompt(
    """
    You are an investment research assistant. 
    You need to answer the user's question: {question}
    Use available functions to retrieve the data you need.
    DO NOT request data from functions that have already been used!
    If all necessary data has been retrieved, return `None`.
    Here is what has already been retrieved: {called_functions}
    """,
    functions=[
        get_daily_price,
        get_company_overview,
        get_sector_performance,
        get_news_sentiment,
        get_earnings_calendar,
    ],
)
def iterative_search(
    question: str, called_functions: set[str], chat_history: list[Any]
) -> FunctionCall[str] | None: ...


@chatprompt(
    SystemMessage(
        """
        You are an investment research assistant. 
        Only use retrieved data for your analysis.
        """
    ),
    UserMessage(
        "You need to answer this question: {question}\nAnalyze the following data: {collected_data}"
    ),
)
def analyze_data(question: str, collected_data: dict[str, Any]) -> str: ...


def format_collected_data(collected_data: dict[str, Any]) -> str:
    formatted_data = []
    for function_name, data in collected_data.items():
        formatted_data.append(f"### {function_name} Data:\n{data}\n")
    return "\n".join(formatted_data)


async def query(question: str, max_iterations: int = 10) -> AsyncGenerator[str, None]:
    """
    Runs iterative retrieval and streams LLM analysis.
    """
    iteration = 0
    collected_data = {}
    called_functions = set()
    chat_history = [
        SystemMessage(
            """
            You are an investment research assistant. 
            Retrieve data iteratively and update insights.
            """
        )
    ]

    while iteration < max_iterations:
        iteration += 1
        yield f"\n**Iteration {iteration}...**\n"

        function_call = iterative_search(question, called_functions, chat_history)

        if function_call is None:
            yield "\n**LLM is satisfied with the data. Analyzing now...**\n"
            break

        function_name = function_call._function.__name__

        if function_name in called_functions:
            yield f"\n**Early stop: {function_name} was already called.**\n"
            break

        called_functions.add(function_name)
        function_args = function_call.arguments

        match function_name:
            case "get_daily_price":
                result = await get_daily_price(**function_args)
            case "get_company_overview":
                result = await get_company_overview(**function_args)
            case "get_sector_performance":
                result = await get_sector_performance()
            case "get_news_sentiment":
                result = await get_news_sentiment(**function_args)
            case "get_earnings_calendar":
                result = await get_earnings_calendar(**function_args)
            case _:
                yield f"\nUnknown function requested: {function_name}\n"
                continue

        if not result:
            yield f"\n**No new data found for {function_name}, stopping iteration.**\n"
            break

        collected_data[function_name] = result
        yield f"\n**Retrieved data from {function_name}** ✅\n"

        chat_history.append(UserMessage(f"Retrieved {function_name} data: {result}"))
        chat_history.append(AssistantMessage(f"Storing data from {function_name}."))

    formatted_data = format_collected_data(collected_data)
    final_analysis = analyze_data(question, formatted_data)
    yield f"\n**Investment Insight:**\n{final_analysis}\n"

from fastapi.responses import JSONResponse

@app.get("/investment_research")
async def investment_research(question: str):
    return StreamingResponse(query(question), media_type="text/event-stream")

@app.get("/get_agent_config")
async def get_agent_config():
    return JSONResponse(content=CURRENT_AGENT_CONFIG)

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
# 定义一个全局变量，暂时存储配置信息（更好的是session管理或数据库持久化）
CURRENT_AGENT_CONFIG = {
    "agent_name": "Investment Research Assistant",
    "features": ["simple-complex-calculation", "planning"],
    "model_source": "gpt-4o",
    "constraints": "Additional constraints if any"
}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)