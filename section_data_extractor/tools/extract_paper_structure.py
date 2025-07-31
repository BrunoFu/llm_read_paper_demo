#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
从论文Markdown中提取结构和图表引用，生成初始的input.json
使用extract_frame_and_tabs_figs.md作为提示模板
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

# 尝试导入相关模块
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from utils.llm_client import LLMClient
except ImportError:
    # 如果无法直接导入，尝试从当前目录导入
    try:
        from tools.llm_client import LLMClient
    except ImportError:
        print(f"{Fore.RED}无法导入必要的模块LLMClient，请确保相关文件存在")
        sys.exit(1)

def load_markdown_file(file_path):
    """加载Markdown文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"{Fore.RED}读取Markdown文件时出错: {e}")
        return None

async def extract_paper_structure(markdown_content, prompt_template_path):
    """
    使用大模型从Markdown内容中提取论文结构和图表引用
    
    Args:
        markdown_content: Markdown文本内容
        prompt_template_path: 提示模板文件路径
    
    Returns:
        dict: 包含论文结构和图表引用的JSON数据
    """
    try:
        # 读取提示模板
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # 替换模板中的{{document}}占位符
        prompt = prompt_template.replace("{{document}}", markdown_content)
        
        # 创建LLM客户端
        client = LLMClient()
        
        print(f"{Fore.CYAN}正在使用大模型提取论文结构和图表引用...")
        print(f"{Fore.YELLOW}这可能需要一些时间，请耐心等待...")
        
        # 调用LLM API获取JSON格式的响应
        response_json = await client.get_json_completion(prompt)
        
        # 验证返回的JSON是否为列表
        if not isinstance(response_json, list):
            print(f"{Fore.RED}大模型返回的结果不是有效的JSON数组")
            return None
        
        return response_json
    except Exception as e:
        print(f"{Fore.RED}提取论文结构和图表引用时出错: {e}")
        return None

async def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # 设置文件路径
    markdown_path = os.path.join(parent_dir, "AER202501_8_gruber-et-al-2025-dying-or-lying-for-profit-hospices-and-end-of-life-care_full.md")
    prompt_template_path = os.path.join(parent_dir, "resources/extract_frame_and_tabs_figs.md")
    output_path = os.path.join(script_dir, "input.json")
    
    # 加载Markdown文件
    markdown_content = load_markdown_file(markdown_path)
    if not markdown_content:
        print(f"{Fore.RED}无法加载Markdown文件，请确保文件存在")
        return False
    
    # 使用大模型提取论文结构和图表引用
    print(f"{Fore.CYAN}开始从Markdown中提取论文结构和图表引用...")
    result = await extract_paper_structure(markdown_content, prompt_template_path)
    
    if not result:
        print(f"{Fore.RED}提取失败，未能获取有效结果")
        return False
    
    # 保存结果到JSON文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"{Fore.GREEN}提取成功，结果已保存到 {output_path}")
        return True
    except Exception as e:
        print(f"{Fore.RED}保存结果时出错: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="从论文Markdown中提取结构和图表引用，生成初始的input.json")
    parser.add_argument("--markdown", help="Markdown文件路径", default="../AER202501_8_gruber-et-al-2025-dying-or-lying-for-profit-hospices-and-end-of-life-care_full.md")
    parser.add_argument("--prompt", help="提示模板文件路径", default="../resources/extract_frame_and_tabs_figs.md")
    parser.add_argument("--output", help="输出文件路径", default="input.json")
    
    args = parser.parse_args()
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # 设置文件路径
    markdown_path = args.markdown if os.path.isabs(args.markdown) else os.path.join(parent_dir, os.path.basename(args.markdown))
    prompt_path = args.prompt if os.path.isabs(args.prompt) else os.path.join(parent_dir, args.prompt)
    output_path = args.output if os.path.isabs(args.output) else os.path.join(script_dir, args.output)
    
    # 修改全局变量
    globals()["markdown_path"] = markdown_path
    globals()["prompt_template_path"] = prompt_path
    globals()["output_path"] = output_path
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 