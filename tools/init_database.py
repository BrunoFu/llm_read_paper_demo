#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
初始化数据库

从example_pdfs目录中提取元数据并存入数据库
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Paper, OCRResult
from database.db_manager import DatabaseManager
from tools.metadata_extractor import process_directory

# 尝试导入增强版元数据提取工具
try:
    from tools.enhanced_metadata_extractor import process_directory_with_enhanced_extraction
    enhanced_extractor_available = True
except ImportError:
    enhanced_extractor_available = False
    print("警告: 增强版元数据提取工具不可用，将使用基本版元数据提取工具")

def init_database(
    pdf_directory: str = "example_pdfs", 
    db_path: str = None, 
    first_pages_dir: str = None, 
    template_path: str = "resources/extract_metadata_from_face_page.md",
    use_enhanced_extractor: bool = True,
    api_name: str = None
) -> None:
    """
    初始化数据库，从PDF目录中提取元数据并存入数据库
    
    Args:
        pdf_directory: PDF文件目录
        db_path: 数据库文件路径，如果为None则使用默认路径
        first_pages_dir: PDF首页内容目录，如果为None则只使用文件名提取
        template_path: prompt模板文件路径
        use_enhanced_extractor: 是否使用增强版元数据提取工具
        api_name: API名称，如果为None则使用当前API
    """
    print(f"正在从 {pdf_directory} 目录中提取元数据...")
    
    # 确保目录存在
    if not os.path.exists(pdf_directory):
        print(f"错误: 目录 {pdf_directory} 不存在")
        return
    
    # 提取元数据
    if use_enhanced_extractor and enhanced_extractor_available and first_pages_dir:
        print(f"使用增强版元数据提取工具...")
        metadata_list = process_directory_with_enhanced_extraction(
            directory_path=pdf_directory,
            first_pages_dir=first_pages_dir,
            template_path=template_path,
            api_name=api_name
        )
    else:
        print(f"使用基本版元数据提取工具...")
        metadata_list = process_directory(pdf_directory)
    
    print(f"共提取到 {len(metadata_list)} 篇论文的元数据")
    
    # 初始化数据库管理器
    db_manager = DatabaseManager(db_path) if db_path else DatabaseManager()
    
    # 将元数据存入数据库
    for metadata in metadata_list:
        # 创建Paper对象
        paper = Paper(
            title=metadata['title'],
            authors=metadata['authors'],
            publication_year=metadata.get('publication_year'),
            journal=metadata.get('journal'),
            doi=metadata.get('doi'),
            abstract=metadata.get('abstract'),
            keywords=metadata.get('keywords', []),
            file_hash=metadata['file_hash']
        )
        
        # 添加到数据库
        paper_id = db_manager.add_paper(paper)
        print(f"已添加论文: {paper.title} (ID: {paper_id})")
        
        # 构建OCR结果路径（假设OCR结果存放在output/[paper_id]目录下）
        ocr_dir = os.path.join("output", str(paper_id))
        os.makedirs(ocr_dir, exist_ok=True)
        
        # 创建OCR结果占位符
        ocr_result = OCRResult(
            paper_id=paper_id,
            ocr_path=os.path.join(ocr_dir, "ocr_result.json"),
            markdown_path=os.path.join(ocr_dir, "report.md"),
            content_list_path=os.path.join(ocr_dir, "content_list.json")
        )
        
        # 添加OCR结果到数据库
        ocr_id = db_manager.add_ocr_result(ocr_result)
        print(f"已添加OCR结果占位符 (ID: {ocr_id})")
    
    print("数据库初始化完成")

def list_all_papers() -> None:
    """
    列出数据库中的所有论文
    """
    db_manager = DatabaseManager()
    papers = db_manager.get_all_papers()
    
    print(f"数据库中共有 {len(papers)} 篇论文:")
    for paper in papers:
        paper_dict = paper.to_dict()
        authors = paper_dict['authors']
        authors_str = ", ".join(authors) if isinstance(authors, list) else authors
        print(f"ID: {paper.id}, 标题: {paper.title}, 作者: {authors_str}, 年份: {paper.publication_year}")

if __name__ == "__main__":
    # 解析命令行参数
    import argparse
    
    parser = argparse.ArgumentParser(description="初始化数据库")
    parser.add_argument("--pdf_dir", default="example_pdfs", help="PDF文件目录")
    parser.add_argument("--db_path", help="数据库文件路径")
    parser.add_argument("--first_pages_dir", help="PDF首页内容目录")
    parser.add_argument("--template", default="resources/extract_metadata_from_face_page.md", help="prompt模板文件路径")
    parser.add_argument("--basic", action="store_true", help="使用基本版元数据提取工具")
    parser.add_argument("--api", help="API名称")
    parser.add_argument("--list", action="store_true", help="列出数据库中的所有论文")
    
    args = parser.parse_args()
    
    if args.list:
        list_all_papers()
    else:
        init_database(
            pdf_directory=args.pdf_dir,
            db_path=args.db_path,
            first_pages_dir=args.first_pages_dir,
            template_path=args.template,
            use_enhanced_extractor=not args.basic,
            api_name=args.api
        ) 