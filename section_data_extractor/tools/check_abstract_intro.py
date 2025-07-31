#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查结构中是否包含abstract和introduction，如果缺少则调用大模型提取
"""

import os
import sys
import json
import re
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

# 尝试导入相关模块
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from utils.llm_client import LLMClient
except ImportError:
    print(f"{Fore.RED}无法导入必要的模块，请确保相关文件存在")
    sys.exit(1)

def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Fore.RED}加载JSON文件时出错: {e}")
        return None

def load_markdown_file(file_path):
    """加载Markdown文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"{Fore.RED}读取Markdown文件时出错: {e}")
        return None

def check_section_exists(structure_data, section_name):
    """
    检查结构中是否包含指定的部分（模糊匹配）
    
    Args:
        structure_data: 结构数据
        section_name: 部分名称（如"abstract"或"introduction"）
    
    Returns:
        bool: 是否存在该部分
        dict: 如果存在，返回该部分的数据
    """
    # 将section_name转换为小写以进行不区分大小写的匹配
    section_name_lower = section_name.lower()
    
    # 定义模糊匹配的正则表达式模式
    if section_name_lower == "abstract":
        patterns = [
            r'^abstract$',
            r'^abstract\s*[:\.\-]',
        ]
    elif section_name_lower == "introduction":
        patterns = [
            r'^introduction$',
            r'^introduction\s*[:\.\-]',
            r'^1\.?\s*introduction',
            r'^i\.?\s*introduction',
        ]
    else:
        patterns = [f"^{re.escape(section_name_lower)}$"]
    
    # 遍历结构数据查找匹配项
    for item in structure_data:
        title = item.get("title", "").lower()
        
        # 检查是否匹配任何模式
        for pattern in patterns:
            if re.search(pattern, title):
                return True, item
    
    return False, None

def find_level0_content(structure_data):
    """查找level 0的内容"""
    for item in structure_data:
        if item.get("level") == 0:
            return item.get("text_content", "")
    return ""

async def extract_abstract_intro(markdown_content, prompt_template_path):
    """
    使用大模型从Markdown内容中提取abstract和introduction
    
    Args:
        markdown_content: Markdown文本内容
        prompt_template_path: 提示模板文件路径
    
    Returns:
        dict: 包含abstract和introduction的字典
    """
    try:
        # 读取提示模板
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # 替换模板中的{{document}}占位符
        prompt = prompt_template.replace("{{document}}", markdown_content)
        
        # 创建LLM客户端
        client = LLMClient()
        
        print(f"{Fore.CYAN}正在使用大模型提取abstract和introduction...")
        
        # 调用LLM API获取JSON格式的响应
        response_json = await client.get_json_completion(prompt)
        
        return response_json
    except Exception as e:
        print(f"{Fore.RED}提取abstract和introduction时出错: {e}")
        return {
            "abstract": {"start": None, "end": None},
            "introduction": {"start": None, "end": None}
        }

async def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # 设置文件路径
    structure_path = os.path.join(script_dir, "structure_with_content.json")
    prompt_template_path = os.path.join(parent_dir, "resources/extract_abstract_intro.md")
    output_path = os.path.join(script_dir, "abstract_intro.json")
    
    # 加载结构数据
    structure_data = load_json_file(structure_path)
    if not structure_data:
        print(f"{Fore.RED}无法加载结构数据，请先运行 add_text_content.py")
        return False
    
    # 检查是否存在abstract和introduction
    has_abstract, abstract_data = check_section_exists(structure_data, "abstract")
    has_intro, intro_data = check_section_exists(structure_data, "introduction")
    
    print(f"{Fore.CYAN}检查结果:")
    print(f"  Abstract: {'存在' if has_abstract else '不存在'}")
    print(f"  Introduction: {'存在' if has_intro else '不存在'}")
    
    # 如果两者都存在，返回True
    if has_abstract and has_intro:
        result = {
            "has_both_sections": True,
            "abstract": abstract_data,
            "introduction": intro_data
        }
        
        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"{Fore.GREEN}已找到abstract和introduction，结果已保存到 {output_path}")
        return True
    
    # 如果缺少任一部分，从level 0的内容中提取
    print(f"{Fore.YELLOW}缺少{'abstract' if not has_abstract else ''}{' 和 ' if not has_abstract and not has_intro else ''}{' introduction' if not has_intro else ''}，将从文本内容中提取")
    
    # 获取level 0的内容
    level0_content = find_level0_content(structure_data)
    
    if not level0_content:
        print(f"{Fore.RED}无法找到level 0的内容")
        return False
    
    # 使用大模型提取abstract和introduction
    extracted_data = await extract_abstract_intro(level0_content, prompt_template_path)
    
    # 构建结果
    result = {
        "has_both_sections": False,
        "missing_sections": [],
        "extracted_data": extracted_data
    }
    
    if not has_abstract:
        result["missing_sections"].append("abstract")
    else:
        result["abstract"] = abstract_data
    
    if not has_intro:
        result["missing_sections"].append("introduction")
    else:
        result["introduction"] = intro_data
    
    # 保存结果
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"{Fore.GREEN}已使用大模型提取缺失部分，结果已保存到 {output_path}")
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="检查结构中是否包含abstract和introduction，如果缺少则调用大模型提取")
    parser.add_argument("--structure", help="结构化JSON文件路径", default="structure_with_content.json")
    parser.add_argument("--output", help="输出文件路径", default="abstract_intro.json")
    parser.add_argument("--prompt", help="提示模板文件路径", default="../resources/extract_abstract_intro.md")
    
    args = parser.parse_args()
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置文件路径
    structure_path = os.path.join(script_dir, args.structure) if not os.path.isabs(args.structure) else args.structure
    output_path = os.path.join(script_dir, args.output) if not os.path.isabs(args.output) else args.output
    prompt_path = args.prompt if os.path.isabs(args.prompt) else os.path.join(os.path.dirname(script_dir), args.prompt)
    
    # 修改全局变量
    globals()["structure_path"] = structure_path
    globals()["output_path"] = output_path
    globals()["prompt_template_path"] = prompt_path
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 