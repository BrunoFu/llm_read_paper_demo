#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具函数包

包含各种工具函数和模块
"""

# 导入可能会用到的工具函数
try:
    from utils.prompt_utils import fill_prompt_with_document
    from utils.llm_client import LLMClient, get_metadata_from_text
    
    __all__ = [
        'fill_prompt_with_document',
        'LLMClient',
        'get_metadata_from_text'
    ]
except ImportError:
    # 如果模块还未创建，则忽略导入错误
    __all__ = [] 