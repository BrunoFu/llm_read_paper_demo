#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Prompt工具函数

用于处理和填充prompt模板
"""

import os
import re
from typing import Dict, Any, Optional

def read_prompt_template(template_path: str) -> str:
    """
    读取prompt模板文件
    
    Args:
        template_path: 模板文件路径
        
    Returns:
        模板内容
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"读取模板文件失败: {e}")

def fill_prompt_with_document(template_path: str, document_text: str) -> str:
    """
    使用文档内容填充prompt模板
    
    Args:
        template_path: 模板文件路径
        document_text: 文档内容
        
    Returns:
        填充后的prompt
    """
    # 读取模板
    template = read_prompt_template(template_path)
    
    # 替换{{document}}标记
    prompt = template.replace("{{document}}", document_text)
    
    return prompt

def fill_prompt_with_variables(template_path: str, variables: Dict[str, Any]) -> str:
    """
    使用变量填充prompt模板
    
    Args:
        template_path: 模板文件路径
        variables: 变量字典
        
    Returns:
        填充后的prompt
    """
    # 读取模板
    template = read_prompt_template(template_path)
    
    # 替换所有变量
    prompt = template
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        prompt = prompt.replace(placeholder, str(value))
    
    return prompt

def extract_json_from_response(response: str) -> str:
    """
    从LLM响应中提取JSON字符串
    
    Args:
        response: LLM响应文本
        
    Returns:
        提取的JSON字符串
    """
    # 尝试查找JSON代码块
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if json_match:
        return json_match.group(1).strip()
    
    # 如果没有代码块，尝试查找整个响应中的JSON
    # 查找以{开头，以}结尾的内容
    json_match = re.search(r'(\{[\s\S]*\})', response)
    if json_match:
        return json_match.group(1).strip()
    
    # 如果仍然没有找到，返回原始响应
    return response.strip()

if __name__ == "__main__":
    # 示例用法
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python prompt_utils.py <template_path> <document_path>")
        sys.exit(1)
    
    template_path = sys.argv[1]
    document_path = sys.argv[2]
    
    try:
        with open(document_path, 'r', encoding='utf-8') as f:
            document_text = f.read()
        
        prompt = fill_prompt_with_document(template_path, document_text)
        print(prompt)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1) 