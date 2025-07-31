#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
增强版元数据提取工具

结合文件名提取和LLM提取功能，提供更全面的元数据
"""

import os
import sys
import json
import asyncio
import re
from pathlib import Path
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入文件名提取模块
from tools.metadata_extractor import (
    extract_metadata_from_filename,
    calculate_file_hash,
    process_pdf_file
)

# 尝试导入相关模块
try:
    from utils.prompt_utils import fill_prompt_with_document
    from utils.llm_client import LLMClient, get_metadata_from_text
except ImportError:
    print("警告: 无法导入LLM相关模块，将只使用文件名提取元数据")
    get_metadata_from_text = None

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
    if get_metadata_from_text is None:
        raise ImportError("未导入LLM相关模块，无法使用LLM提取元数据")
    
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

def extract_metadata_from_pdf(
    pdf_path: str,
    first_pages_path: Optional[str] = None,
    template_path: str = "resources/extract_metadata_from_face_page.md",
    output_dir: Optional[str] = None,
    api_name: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None,
    use_llm: bool = True
) -> Dict[str, Any]:
    """
    从PDF文件中提取元数据，结合文件名提取和LLM提取
    
    Args:
        pdf_path: PDF文件路径
        first_pages_path: PDF首页内容文件路径，如果为None则只使用文件名提取
        template_path: prompt模板文件路径
        output_dir: 输出目录，如果为None则不保存结果
        api_name: API名称，如果为None则使用当前API
        llm_config: LLM配置，如果为None则使用默认配置
        use_llm: 是否使用LLM提取元数据
        
    Returns:
        提取的元数据
    """
    # 从文件名提取基本元数据
    print(f"从文件名提取基本元数据: {pdf_path}")
    filename_metadata = process_pdf_file(pdf_path)
    
    # 如果不使用LLM或未提供首页内容，则直接返回文件名提取的元数据
    if not use_llm or first_pages_path is None or not os.path.exists(first_pages_path) or get_metadata_from_text is None:
        return filename_metadata
    
    try:
        # 使用LLM提取更详细的元数据
        print(f"使用LLM从首页内容提取详细元数据...")
        
        # 构建输出路径
        metadata_path = None
        if output_dir:
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            metadata_path = os.path.join(output_dir, f"{pdf_name}_metadata.json")
        
        # 提取元数据
        llm_metadata = asyncio.run(extract_metadata_from_pdf_first_pages(
            first_pages_path=first_pages_path,
            template_path=template_path,
            output_path=metadata_path,
            api_name=api_name,
            llm_config=llm_config
        ))
        
        # 合并元数据，优先使用LLM提取的元数据
        merged_metadata = filename_metadata.copy()
        
        # 更新标题
        if llm_metadata.get('title'):
            merged_metadata['title'] = llm_metadata['title']
        
        # 更新作者
        if llm_metadata.get('authors'):
            # 提取作者姓名
            author_names = [author.get('name') for author in llm_metadata['authors'] if author.get('name')]
            if author_names:
                merged_metadata['authors'] = author_names
        
        # 更新其他字段
        if llm_metadata.get('journal_name'):
            merged_metadata['journal'] = llm_metadata['journal_name']
        
        if llm_metadata.get('publication_date'):
            # 尝试从出版日期中提取年份
            year_match = re.search(r'(\d{4})', llm_metadata['publication_date'])
            if year_match and not merged_metadata.get('publication_year'):
                merged_metadata['publication_year'] = int(year_match.group(1))
        
        if llm_metadata.get('doi'):
            merged_metadata['doi'] = llm_metadata['doi']
        
        if llm_metadata.get('abstract'):
            merged_metadata['abstract'] = llm_metadata['abstract']
        
        if llm_metadata.get('jel_classification'):
            merged_metadata['keywords'] = llm_metadata['jel_classification']
        
        # 添加额外的LLM提取的字段
        merged_metadata['acknowledgements'] = llm_metadata.get('acknowledgements', [])
        merged_metadata['research_assistants'] = llm_metadata.get('research_assistants', [])
        merged_metadata['conferences_and_seminars'] = llm_metadata.get('conferences_and_seminars', [])
        merged_metadata['funding_sources'] = llm_metadata.get('funding_sources', [])
        
        # 添加机构信息
        if llm_metadata.get('authors'):
            merged_metadata['institutions'] = [
                author.get('institution') for author in llm_metadata['authors']
                if author.get('institution')
            ]
        
        return merged_metadata
    
    except Exception as e:
        print(f"LLM提取元数据失败: {e}")
        # 如果LLM提取失败，返回文件名提取的元数据
        return filename_metadata

def process_directory_with_enhanced_extraction(
    directory_path: str,
    first_pages_dir: Optional[str] = None,
    template_path: str = "resources/extract_metadata_from_face_page.md",
    output_dir: Optional[str] = None,
    api_name: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None,
    use_llm: bool = True
) -> List[Dict[str, Any]]:
    """
    处理目录中的所有PDF文件，提取元数据
    
    Args:
        directory_path: PDF文件目录路径
        first_pages_dir: PDF首页内容目录路径，如果为None则只使用文件名提取
        template_path: prompt模板文件路径
        output_dir: 输出目录，如果为None则不保存结果
        api_name: API名称，如果为None则使用当前API
        llm_config: LLM配置，如果为None则使用默认配置
        use_llm: 是否使用LLM提取元数据
        
    Returns:
        包含所有论文元数据的列表
    """
    results = []
    
    # 遍历目录中的所有PDF文件
    for file in os.listdir(directory_path):
        if file.lower().endswith('.pdf'):
            pdf_path = os.path.join(directory_path, file)
            pdf_name = os.path.splitext(file)[0]
            
            # 构建首页内容文件路径
            first_pages_path = None
            if first_pages_dir:
                first_pages_path = os.path.join(first_pages_dir, f"{pdf_name}_first_three_pages.md")
                if not os.path.exists(first_pages_path):
                    print(f"警告: 未找到PDF首页内容文件: {first_pages_path}")
                    first_pages_path = None
            
            # 提取元数据
            metadata = extract_metadata_from_pdf(
                pdf_path=pdf_path,
                first_pages_path=first_pages_path,
                template_path=template_path,
                output_dir=output_dir,
                api_name=api_name,
                llm_config=llm_config,
                use_llm=use_llm
            )
            
            results.append(metadata)
    
    return results

if __name__ == "__main__":
    # 示例用法
    import argparse
    
    parser = argparse.ArgumentParser(description="增强版元数据提取工具")
    parser.add_argument("pdf_dir", help="PDF文件目录")
    parser.add_argument("--first-pages-dir", "-f", help="PDF首页内容目录")
    parser.add_argument("--template", "-t", default="resources/extract_metadata_from_face_page.md", help="prompt模板文件路径")
    parser.add_argument("--output-dir", "-o", help="输出目录")
    parser.add_argument("--api", "-a", help="API名称")
    parser.add_argument("--no-llm", action="store_true", help="不使用LLM提取元数据")
    
    args = parser.parse_args()
    
    # 处理目录
    results = process_directory_with_enhanced_extraction(
        directory_path=args.pdf_dir,
        first_pages_dir=args.first_pages_dir,
        template_path=args.template,
        output_dir=args.output_dir,
        api_name=args.api,
        use_llm=not args.no_llm
    )
    
    # 打印结果
    print(json.dumps(results, ensure_ascii=False, indent=2)) 