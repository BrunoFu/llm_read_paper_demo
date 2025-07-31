#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
提示词工具

提供处理提示词模板的功能
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union

# 尝试导入json_repair
try:
    from json_repair import repair_json
except ImportError:
    print("警告: 未安装json_repair库，请使用 'pip install json-repair' 安装")
    def repair_json(json_str):
        """简单的JSON修复函数，当json_repair库不可用时使用"""
        return json_str

def fill_prompt_with_document(template: Union[str, Path], document: str) -> str:
    """
    用文档内容填充提示词模板
    
    Args:
        template: 提示词模板文件路径或模板字符串
        document: 文档内容
        
    Returns:
        填充后的提示词
    """
    # 如果template是文件路径，读取模板内容
    if isinstance(template, (str, Path)) and os.path.exists(str(template)):
        try:
            with open(template, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except Exception as e:
            raise ValueError(f"读取提示词模板文件失败: {e}")
    else:
        template_content = template
    
    # 替换模板中的占位符
    filled_prompt = template_content.replace("{{document}}", document)
    
    return filled_prompt

def extract_and_repair_json(llm_response: str) -> Dict[str, Any]:
    """
    从大模型响应中提取并修复JSON
    
    Args:
        llm_response: 大模型的原始响应文本
        
    Returns:
        解析后的JSON对象
    
    Raises:
        ValueError: 如果无法解析为有效的JSON
    """
    # 尝试直接解析
    try:
        return json.loads(llm_response)
    except json.JSONDecodeError:
        # 如果直接解析失败，尝试提取JSON部分
        try:
            # 尝试匹配JSON代码块
            json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```|^\s*(\{[\s\S]*\})\s*$'
            match = re.search(json_pattern, llm_response)
            
            if match:
                # 提取匹配的JSON字符串
                json_str = match.group(1) or match.group(2)
            else:
                # 如果没有明确的代码块，尝试查找第一个{和最后一个}之间的内容
                start = llm_response.find('{')
                end = llm_response.rfind('}')
                if start >= 0 and end > start:
                    json_str = llm_response[start:end+1]
                else:
                    raise ValueError("无法从响应中提取JSON")
            
            # 使用json_repair修复JSON
            repaired_json = repair_json(json_str)
            
            # 解析修复后的JSON
            return json.loads(repaired_json)
            
        except Exception as e:
            raise ValueError(f"无法解析为有效的JSON: {str(e)}\n原始响应: {llm_response[:500]}...")

if __name__ == "__main__":
    # 测试代码
    template = """# 模板测试
    
文档内容：
{{document}}

请分析上述文档。
"""
    
    document = "这是一个测试文档。" * 10
    
    filled = fill_prompt_with_document(template, document)
    print(filled)
    
    # 测试JSON修复
    test_json = """
    {
      "name": "测试",
      "value": 123,
      "items": [1, 2, 3,]  // 这里有一个多余的逗号
    }
    """
    
    try:
        fixed = extract_and_repair_json(test_json)
        print("\nJSON修复结果:")
        print(json.dumps(fixed, ensure_ascii=False, indent=2))
    except ValueError as e:
        print(f"错误: {e}")
