#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
元数据提取器

从PDF文件中提取元数据，使用LLM处理
"""

import os
import sys
import json
import asyncio
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union

# 尝试导入相关模块
try:
    from utils.prompt_utils import fill_prompt_with_document
    from utils.llm_client import LLMClient, get_metadata_from_text
except ImportError:
    # 尝试从上级目录导入
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from utils.prompt_utils import fill_prompt_with_document
        from utils.llm_client import LLMClient, get_metadata_from_text
    except ImportError:
        print("无法导入必要的模块，请确保相关文件存在")
        sys.exit(1)

# 尝试导入json_repair
try:
    from json_repair import repair_json
except ImportError:
    print("警告: 未安装json_repair库，请使用 'pip install json-repair' 安装")
    def repair_json(json_str):
        """简单的JSON修复函数，当json_repair库不可用时使用"""
        return json_str

async def extract_metadata_from_pdf_first_pages(
    first_pages_path: str, 
    template_path: str, 
    output_path: Optional[str] = None, 
    api_name: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    从PDF首页内容中提取元数据
    
    Args:
        first_pages_path: PDF首页内容文件路径
        template_path: prompt模板文件路径
        output_path: 输出文件路径，如果为None则不保存结果
        api_name: API名称，如果为None则使用当前API
        llm_config: LLM配置，如果为None则使用默认配置
        
    Returns:
        提取的元数据
    """
    # 读取PDF首页内容
    try:
        with open(first_pages_path, 'r', encoding='utf-8') as f:
            document_text = f.read()
    except Exception as e:
        raise ValueError(f"读取PDF首页内容失败: {e}")
    
    # 使用LLM提取元数据
    print(f"正在使用LLM提取元数据...")
    if api_name:
        print(f"使用API: {api_name}")
    
    try:
        # 使用get_metadata_from_text函数提取元数据
        metadata = await get_metadata_from_text(
            document_text=document_text,
            template_path=template_path,
            api_name=api_name,
            config=llm_config
        )
    except Exception as e:
        raise Exception(f"调用LLM API提取元数据时出错: {e}")
    
    # 如果指定了输出路径，保存结果
    if output_path:
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # 保存JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"元数据已保存到: {output_path}")
        except Exception as e:
            print(f"保存元数据失败: {e}")
    
    return metadata

def extract_metadata(
    pdf_name: str, 
    output_dir: str, 
    template_path: str, 
    api_name: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    提取PDF元数据的主函数
    
    Args:
        pdf_name: PDF文件名（不含路径和后缀）
        output_dir: 输出目录
        template_path: prompt模板文件路径
        api_name: API名称，如果为None则使用当前API
        llm_config: LLM配置，如果为None则使用默认配置
        
    Returns:
        提取的元数据
    """
    # 构建文件路径
    first_pages_path = os.path.join(output_dir, f"{pdf_name}_first_three_pages.md")
    metadata_path = os.path.join(output_dir, f"{pdf_name}_metadata.json")
    
    # 检查文件是否存在
    if not os.path.exists(first_pages_path):
        raise FileNotFoundError(f"未找到PDF首页内容文件: {first_pages_path}")
    
    # 提取元数据
    return asyncio.run(extract_metadata_from_pdf_first_pages(
        first_pages_path=first_pages_path,
        template_path=template_path,
        output_path=metadata_path,
        api_name=api_name,
        llm_config=llm_config
    ))

if __name__ == "__main__":
    # 测试代码
    import argparse
    
    parser = argparse.ArgumentParser(description="从PDF首页内容中提取元数据")
    parser.add_argument("pdf_name", help="PDF文件名（不含路径和后缀）")
    parser.add_argument("--output-dir", "-d", default=None, help="输出目录")
    parser.add_argument("--template", "-t", default="resources/LLM/extract_metadata_from_face_page.md", help="prompt模板文件路径")
    parser.add_argument("--api", "-a", default=None, help="API名称")
    
    args = parser.parse_args()
    
    # 确定输出目录
    output_dir = args.output_dir or f"outputs/{args.pdf_name}"
    
    try:
        metadata = extract_metadata(
            pdf_name=args.pdf_name, 
            output_dir=output_dir, 
            template_path=args.template,
            api_name=args.api
        )
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1) 