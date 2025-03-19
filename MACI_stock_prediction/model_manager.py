import os
from typing import Optional, Any

try:
    import litellm
except ImportError:
    raise ImportError("请先安装litellm: pip install litellm")

def configure_model(model_source: str, api_key: str) -> bool:
    """
    根据模型名称配置 API 密钥并设置环境变量。
    支持通过litellm调用各种模型。

    :param model_source: 模型名称或provider/model格式
    :param api_key: API 密钥
    :return: 配置是否成功
    """
    try:
        # 检查是否是provider/model格式 (litellm格式)
        if "/" in model_source:
            provider, model_name = model_source.split("/", 1)
            
            # 根据provider设置相应的环境变量
            if provider.lower() == "openai":
                os.environ["OPENAI_API_KEY"] = api_key
            elif provider.lower() == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = api_key
            elif provider.lower() == "deepseek":
                os.environ["DEEPSEEK_API_KEY"] = api_key
            elif provider.lower() in ["together", "togetherai"]: 
                os.environ["TOGETHERAI_API_KEY"] = api_key 
                print(f"已为 Together.ai 设置API密钥")
            else:
                # 通用处理，使用全大写的provider名称作为环境变量前缀
                os.environ[f"{provider.upper()}_API_KEY"] = api_key
                
            print(f"已通过LiteLLM为 {provider}/{model_name} 配置API密钥")
            return True
            
        # 原有的模型配置逻辑
        model_env_map = {
            "openai": "OPENAI_API_KEY",
            "gpt-4o": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "llama-v3": "TOGETHERAI_API_KEY"  # 为llama-v3添加TogetherAI支持
        }

        if model_source in model_env_map:
            env_var = model_env_map[model_source]
            os.environ[env_var] = api_key
            print(f"已为 {model_source} 设置环境变量 {env_var} {api_key}")
            
            # 如果是llama-v3，添加全局变量标记使用together
            if model_source == "llama-v3":
                global LLAMA_MODEL
                LLAMA_MODEL = "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
                print(f"Llama模型将通过Together.ai调用: {LLAMA_MODEL}")
                
            return True
        else:
            print(f"不支持的模型: {model_source}")
            return False
            
    except Exception as e:
        print(f"配置模型时出错: {str(e)}")
        return False

def litellm_completion(
    messages: list[dict[str, str]], 
    model: str, 
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> Any:
    """
    使用LiteLLM调用模型生成完成响应
    
    :param messages: 聊天消息列表
    :param model: 模型名称，格式为"provider/model_name"或单独的模型名
    :param stream: 是否流式返回
    :param temperature: 温度参数
    :param max_tokens: 最大生成token数
    :return: LiteLLM响应
    """
    try:
        # 如果没有provider前缀，尝试添加
        if "/" not in model:
            if model.startswith("gpt") or model == "openai":
                model = f"openai/{model if not model == 'openai' else 'gpt-3.5-turbo'}"
            elif "deepseek" in model:
                model = f"deepseek/{model if not model == 'deepseek' else 'deepseek-chat'}"
            elif "llama" in model or model == "llama-v3":
                # 使用Together.ai的指定Llama模型
                model = "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
                
                # 检查是否设置了全局模型
                if 'LLAMA_MODEL' in globals():
                    model = LLAMA_MODEL
        
        print(f"LiteLLM调用模型: {model}")
        
        # 调用LiteLLM的completion函数
        response = litellm.completion(
            model=model,
            messages=messages,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response
    except Exception as e:
        print(f"LiteLLM调用出错: {str(e)}")
        raise