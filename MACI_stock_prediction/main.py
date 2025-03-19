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
from model_manager import configure_model
from model_manager import litellm_completion

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
    api_key: str | None = None

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
    CURRENT_AGENT_CONFIG = config.model_dump()
    print("save_agent_config:", CURRENT_AGENT_CONFIG)

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
        # 构造代理配置文件路径
        filepath = os.path.join("saved_agents", f"{agent_id}.json")
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # 读取配置文件
        with open(filepath, "r") as f:
            loaded_config = json.load(f)
        
        # 更新全局变量
        global CURRENT_AGENT_CONFIG
        CURRENT_AGENT_CONFIG = loaded_config
        
        # 获取模型和 API 密钥
        model_source = loaded_config.get("model_source")
        api_key = loaded_config.get("api_key")
        
        # 配置模型（独立到 model_manager 中）
        if model_source and api_key:
            success = configure_model(model_source, api_key)
            if not success:
                print("模型配置失败")
        else:
            print("配置文件中缺少 model_source 或 api_key")
        
        # 返回结果
        print("已加载代理配置:", CURRENT_AGENT_CONFIG)
        return {"success": True, "agent": loaded_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载代理失败: {str(e)}")

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

# 添加一个使用LiteLLM的替代函数
def analyze_data_litellm(question: str, collected_data: str) -> str:
    """使用LiteLLM分析数据并回答问题"""
    # 获取当前配置的模型
    model = CURRENT_AGENT_CONFIG.get("model_source", "openai/gpt-3.5-turbo")
    
    messages = [
        {"role": "system", "content": "You are an investment research assistant. Only use retrieved data for your analysis."},
        {"role": "user", "content": f"You need to answer this question: {question}\nAnalyze the following data: {collected_data}"}
    ]
    
    try:
        response = litellm_completion(messages=messages, model=model)
        return response.choices[0].message.content
    except Exception as e:
        return f"分析数据时出错: {str(e)}"


def format_collected_data(collected_data: dict[str, Any]) -> str:
    formatted_data = []
    for function_name, data in collected_data.items():
        formatted_data.append(f"### {function_name} Data:\n{data}\n")
    return "\n".join(formatted_data)


# 添加一个使用LiteLLM的替代函数
def analyze_data_litellm(question: str, collected_data: str) -> str:
    """使用LiteLLM分析数据并回答问题"""
    # 获取当前配置的模型
    model = CURRENT_AGENT_CONFIG.get("model_source", "openai/gpt-3.5-turbo")
    
    messages = [
        {"role": "system", "content": "You are an investment research assistant. Only use retrieved data for your analysis."},
        {"role": "user", "content": f"You need to answer this question: {question}\nAnalyze the following data: {collected_data}"}
    ]
    
    try:
        response = litellm_completion(messages=messages, model=model)
        return response.choices[0].message.content
    except Exception as e:
        return f"分析数据时出错: {str(e)}"

# 修改query函数
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
    
    # 检查是否使用LiteLLM
    use_litellm = False
    if CURRENT_AGENT_CONFIG and "model_source" in CURRENT_AGENT_CONFIG:
        model_source = CURRENT_AGENT_CONFIG.get("model_source", "")
        if "/" in model_source or model_source == "deepseek":  # 如果是LiteLLM格式或deepseek
            use_litellm = True
            yield f"\n**使用LiteLLM与模型 {model_source} 通信**\n"

    while iteration < max_iterations:
        iteration += 1
        yield f"\n**Iteration {iteration}...**\n"

        # 使用magentic的原始函数或自定义litellm调用
        if not use_litellm:
            function_call = iterative_search(question, called_functions, chat_history)
        else:
            # 这里需要实现一个litellm版本的iterative_search
            # 简化示例，实际可能需要更复杂的实现
            messages = [
                {"role": "system", "content": "You are an investment research assistant. Retrieve data iteratively."},
                {"role": "user", "content": f"You need to answer the user's question: {question}\nWhat data do you need? Called functions: {called_functions}"}
            ]
            model = CURRENT_AGENT_CONFIG.get("model_source", "openai/gpt-3.5-turbo")
            
            try:
                response = litellm_completion(messages=messages, model=model)
                content = response.choices[0].message.content.lower()
                
                # 简单解析，查找需要调用的函数
                if "daily_price" in content and "get_daily_price" not in called_functions:
                    function_name = "get_daily_price"
                    # 提取ticker (简化实现)
                    ticker = "TSLA" if "tsla" in question.lower() else "AAPL"
                    function_call = type('obj', (object,), {
                        '_function': globals()[function_name],
                        'arguments': {"ticker": ticker}
                    })
                elif "company_overview" in content and "get_company_overview" not in called_functions:
                    function_name = "get_company_overview"
                    ticker = "TSLA" if "tsla" in question.lower() else "AAPL"
                    function_call = type('obj', (object,), {
                        '_function': globals()[function_name],
                        'arguments': {"ticker": ticker}
                    })
                elif "sector_performance" in content and "get_sector_performance" not in called_functions:
                    function_name = "get_sector_performance"
                    function_call = type('obj', (object,), {
                        '_function': globals()[function_name],
                        'arguments': {}
                    })
                else:
                    function_call = None
            except Exception as e:
                yield f"\n**LiteLLM调用错误: {str(e)}**\n"
                function_call = None

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

        if not use_litellm:
            chat_history.append(UserMessage(f"Retrieved {function_name} data: {result}"))
            chat_history.append(AssistantMessage(f"Storing data from {function_name}."))

    formatted_data = format_collected_data(collected_data)
    
    # 根据使用的模型选择分析方法
    if not use_litellm:
        final_analysis = analyze_data(question, formatted_data)
    else:
        final_analysis = analyze_data_litellm(question, formatted_data)
        
    yield f"\n**Investment Insight:**\n{final_analysis}\n"

from fastapi.responses import JSONResponse

@app.get("/investment_research")
async def investment_research(question: str):
    return StreamingResponse(query(question), media_type="text/event-stream")

@app.get("/get_agent_config")
async def get_agent_config():
    print("get_agent_config:", CURRENT_AGENT_CONFIG)
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