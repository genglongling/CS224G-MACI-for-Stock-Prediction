import os
from typing import Optional, Any

try:
    import litellm
except ImportError:
    raise ImportError("Please install litellm first: pip install litellm")

def configure_model(model_source: str, api_key: str) -> bool:
    """
    Configure API key and set environment variables based on model name.
    Supports calling various models through litellm.

    :param model_source: Model name or provider/model format
    :param api_key: API key
    :return: Whether configuration was successful
    """
    try:
        # Check if it's in provider/model format (litellm format)
        if "/" in model_source:
            provider, model_name = model_source.split("/", 1)
            
            # Set corresponding environment variable based on provider
            if provider.lower() == "openai":
                os.environ["OPENAI_API_KEY"] = api_key
            elif provider.lower() == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = api_key
            elif provider.lower() == "deepseek":
                os.environ["DEEPSEEK_API_KEY"] = api_key
            elif provider.lower() in ["together", "togetherai"]: 
                os.environ["TOGETHERAI_API_KEY"] = api_key 
                print(f"API key set for Together.ai")
            else:
                # Generic handling, use uppercase provider name as environment variable prefix
                os.environ[f"{provider.upper()}_API_KEY"] = api_key
                
            print(f"API key configured via LiteLLM for {provider}/{model_name}")
            return True
            
        # Original model configuration logic
        model_env_map = {
            "openai": "OPENAI_API_KEY",
            "gpt-4o": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "llama-v3": "TOGETHERAI_API_KEY"  # Add TogetherAI support for llama-v3
        }

        if model_source in model_env_map:
            env_var = model_env_map[model_source]
            os.environ[env_var] = api_key
            print(f"Environment variable {env_var} {api_key} set for {model_source}")
            
            # If it's llama-v3, add global variable flag to use together
            if model_source == "llama-v3":
                global LLAMA_MODEL
                LLAMA_MODEL = "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
                print(f"Llama model will be called via Together.ai: {LLAMA_MODEL}")
                
            return True
        else:
            print(f"Unsupported model: {model_source}")
            return False
            
    except Exception as e:
        print(f"Error configuring model: {str(e)}")
        return False

def litellm_completion(
    messages: list[dict[str, str]], 
    model: str, 
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> Any:
    """
    Use LiteLLM to call model and generate completion response
    
    :param messages: List of chat messages
    :param model: Model name, format as "provider/model_name" or standalone model name
    :param stream: Whether to return as stream
    :param temperature: Temperature parameter
    :param max_tokens: Maximum number of tokens to generate
    :return: LiteLLM response
    """
    try:
        # If there's no provider prefix, try to add one
        if "/" not in model:
            if model.startswith("gpt") or model == "openai":
                model = f"openai/{model if not model == 'openai' else 'gpt-3.5-turbo'}"
            elif "deepseek" in model:
                model = f"deepseek/{model if not model == 'deepseek' else 'deepseek-chat'}"
            elif "llama" in model or model == "llama-v3":
                # Use specified Llama model from Together.ai
                model = "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
                
                # Check if global model is set
                if 'LLAMA_MODEL' in globals():
                    model = LLAMA_MODEL
        
        print(f"LiteLLM calling model: {model}")
        
        # Call LiteLLM's completion function
        response = litellm.completion(
            model=model,
            messages=messages,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response
    except Exception as e:
        print(f"LiteLLM call error: {str(e)}")
        raise