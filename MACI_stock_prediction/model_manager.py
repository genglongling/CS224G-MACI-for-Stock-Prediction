import os

def configure_model(model_source: str, api_key: str) -> bool:
    """
    根据模型名称配置 API 密钥并设置环境变量。

    :param model_source: 模型名称（例如 "openai", "gpt-4o"）
    :param api_key: API 密钥
    :return: 配置是否成功
    """
    # 定义模型与环境变量的映射
    model_env_map = {
        "openai": "OPENAI_API_KEY",
        "gpt-4o": "OPENAI_API_KEY",
        # 未来可以添加更多模型，例如：
        # "other_model": "OTHER_MODEL_API_KEY"
    }

    if model_source in model_env_map:
        env_var = model_env_map[model_source]
        os.environ[env_var] = api_key
        print(f"已为 {model_source} 设置环境变量 {env_var}", api_key)
        return True
    else:
        print(f"不支持的模型: {model_source}")
        return False