#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM配置管理

提供LLM API配置管理功能
"""

import os

# 针对不同API的配置
LLM_CONFIG = {
    "wd_gemini": {
        "api_url": "https://wendavid-gem-bal.hf.space/gemini/v1beta",
        "api_key": "sk-ZyMZWXm8ASAlDTM0ViX0oHi3VyoRHmQ3RJy7rZn1KK20KmAm",
        "default_model": "gemini-2.5-flash",
        "temperature": 0.7,
        "max_retries": 5,
        "retry_base_delay": 1,
        "reasoner": False
    },
    "deepseek": {
        "api_url": "https://api.deepseek.com/v1",
        "api_key": "sk-48da5a4591914942bc849e526feb0e67",
        "default_model": "deepseek-chat",
        "temperature": 0.7,
        "max_retries": 5,
        "retry_base_delay": 1,
        "reasoner": False
    },
    "deepseek_r1": {
        "api_url": "https://api.deepseek.com/v1",
        "api_key": "sk-5e5f19d1b3764243b1dcb4dcb3fa4f27",
        "default_model": "deepseek-reasoner",
        "temperature": 0.7,
        "max_retries": 5,
        "retry_base_delay": 1,
        "reasoner": True
    },
    "yunwu_dpsk": {
        "api_url": "https://yunwu.ai/v1",
        "api_key": "sk-PGDOGTw7CMcDaJzHCdoAkEW75LhM3lpqY9ZjBGWsMa4ElbL6",
        "default_model": "deepseek-r1",
        "temperature": 0.7,
        "max_retries": 5,
        "retry_base_delay": 1,
        "reasoner": True
    },
    "yunwu_gemini": {
        "api_url": "https://yunwu.ai/v1",
        "api_key": "sk-cnjKVFRFEuuRFbv9RlS7gEhSUStMjBAUe8c57FtymwXEzly7",
        "default_model": "gemini-2.5-flash",
        "temperature": 0.7,
        "max_retries": 5,
        "retry_base_delay": 1,
        "reasoner": False
    },
    "yunwu_openai": {
        "api_url": "https://yunwu.ai/v1",
        "api_key": "sk-0DjLs55hVZLxaV4YlQW11WISudSuUgCaBexvw9f9xgXl41C1",
        "default_model": "gpt-4o-2024-08-06",
        "temperature": 0.7,
        "max_retries": 5,
        "retry_base_delay": 1,
        "reasoner": False
    },
    "siliconflow": {
        "api_url": "https://api.siliconflow.cn/v1",
        "api_key": "sk-yxgmeeixikvrhnusaayeosdjattajecvkkuuqwvoyxbjpngc",
        "default_model": "Pro/deepseek-ai/DeepSeek-R1",
        "temperature": 0.7,
        "max_retries": 5,
        "retry_base_delay": 1,
        "reasoner": True
    },
    "wd_gemini2": {
        "api_url": "https://tbai.xin/v1",
        "api_key": "sk-n3bh8L5Y6lJBvAqshHjwwMrnc4P8zDLT2RNy4BjLOqAdwIGc",
        "default_model": "gemini-2.5-pro",
        "temperature": 0.7,
        "max_retries": 5,
        "retry_base_delay": 1,
        "reasoner": False
    }
}

# 默认API配置
CURRENT_API = "wd_gemini2"

# 其他全局配置参数
MAX_RETRIES = 5
SAVE_INTERVAL = 1000
BATCH_SIZE = 200

def get_default_model(api_name=None):
    """
    获取当前配置的默认模型
    
    Args:
        api_name: API名称，如果为None则使用当前API
        
    Returns:
        默认模型名称
    """
    api = api_name or CURRENT_API
    model = LLM_CONFIG[api]["default_model"]
    print(f"使用 {api} 的默认模型: {model}")
    return model

def get_api_config(api_name=None):
    """
    获取API配置
    
    Args:
        api_name: API名称，如果为None则使用当前API
        
    Returns:
        API配置字典
    """
    api = api_name or CURRENT_API
    return LLM_CONFIG[api]

def set_current_api(api_name):
    """
    更新当前API设置
    
    Args:
        api_name: 要设置的API名称
        
    Returns:
        设置后的当前API名称
    """
    global CURRENT_API
    if api_name not in LLM_CONFIG:
        raise ValueError(f"未知的API: {api_name}。可用选项: {', '.join(LLM_CONFIG.keys())}")
    CURRENT_API = api_name
    return CURRENT_API

def list_available_apis():
    """
    列出所有可用的API
    
    Returns:
        可用API名称列表
    """
    return list(LLM_CONFIG.keys()) 