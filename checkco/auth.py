import json
import os
import hashlib
from typing import Tuple, Dict, Any

# 用户数据文件路径
USER_DATA_FILE = 'user_data.json'

def hash_password(password: str) -> str:
    """简单的密码哈希函数"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> Dict:
    """加载用户数据"""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        # 创建一个空的用户数据文件
        users = {"users": {}}
        save_users(users)
        return users

def save_users(users: Dict) -> None:
    """保存用户数据"""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def register_user(email: str, password: str, name: str = "", provider: str = "local") -> Tuple[bool, str]:
    """注册新用户"""
    users = load_users()
    
    # 检查用户是否已存在
    if email in users["users"]:
        return False, "User already exists"
    
    # 创建新用户
    users["users"][email] = {
        "name": name if name else email.split('@')[0],
        "password": hash_password(password) if provider == "local" else "",
        "provider": provider,
        "api_keys": {}
    }
    
    save_users(users)
    return True, "User registered successfully"

def verify_user(email: str, password: str) -> Tuple[bool, Any]:
    """验证用户登录"""
    users = load_users()
    
    if email not in users["users"]:
        return False, "User not found"
    
    user = users["users"][email]
    if user["provider"] != "local":
        return False, "Please use SSO to log in"
    
    if user["password"] != hash_password(password):
        return False, "Incorrect password"
    
    return True, user

def sso_login(provider: str, email: str) -> Tuple[bool, Any]:
    """处理SSO登录"""
    # 检查用户是否存在
    users = load_users()
    if email in users["users"]:
        user = users["users"][email]
    else:
        # 创建新的SSO用户
        name = email.split('@')[0]
        register_user(email, "", name, provider)
        users = load_users()
        user = users["users"][email]
    
    return True, {
        'name': user['name'],
        'email': email,
        'provider': provider
    }

def get_user_api_keys(email: str) -> Dict:
    """获取用户的API密钥"""
    users = load_users()
    if email in users["users"]:
        return users["users"][email].get("api_keys", {})
    return {}

def save_user_api_keys(email: str, tavily_key: str, together_key: str) -> bool:
    """保存用户的API密钥"""
    users = load_users()
    if email in users["users"]:
        users["users"][email]["api_keys"] = {
            "tavily": tavily_key,
            "together": together_key
        }
        save_users(users)
        return True
    return False