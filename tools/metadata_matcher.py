#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
元数据匹配工具

匹配用户输入的PDF与数据库中的记录
"""

import os
import sys
import difflib
from typing import Dict, Any, List, Optional, Tuple, Union

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Paper, calculate_file_hash
from database.db_manager import DatabaseManager
from tools.metadata_extractor import extract_metadata_from_filename

class MetadataMatcher:
    """元数据匹配器类"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化元数据匹配器
        
        Args:
            db_manager: 数据库管理器，如果为None则创建新的管理器
        """
        self.db_manager = db_manager or DatabaseManager()
    
    def match_by_hash(self, pdf_path: str) -> Optional[Paper]:
        """
        通过文件哈希值匹配论文
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            匹配的论文对象，如果不存在则返回None
        """
        # 计算文件哈希值
        file_hash = calculate_file_hash(pdf_path)
        
        # 在数据库中查找匹配的论文
        return self.db_manager.get_paper_by_hash(file_hash)
    
    def match_by_title(self, title: str, threshold: float = 0.8) -> Optional[Paper]:
        """
        通过标题匹配论文
        
        Args:
            title: 论文标题
            threshold: 相似度阈值，范围0-1，越大要求越相似
            
        Returns:
            匹配的论文对象，如果不存在则返回None
        """
        # 获取所有论文
        papers = self.db_manager.get_all_papers()
        
        # 如果没有论文，返回None
        if not papers:
            return None
        
        # 计算标题相似度
        similarities = []
        for paper in papers:
            similarity = difflib.SequenceMatcher(None, title.lower(), paper.title.lower()).ratio()
            similarities.append((paper, similarity))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 如果最高相似度大于阈值，返回匹配的论文
        if similarities[0][1] >= threshold:
            return similarities[0][0]
        
        return None
    
    def match_by_metadata(self, pdf_path: str, threshold: float = 0.8) -> Optional[Paper]:
        """
        通过元数据匹配论文
        
        Args:
            pdf_path: PDF文件路径
            threshold: 相似度阈值，范围0-1，越大要求越相似
            
        Returns:
            匹配的论文对象，如果不存在则返回None
        """
        # 首先尝试通过哈希值匹配
        paper = self.match_by_hash(pdf_path)
        if paper:
            return paper
        
        # 如果哈希值匹配失败，尝试通过标题匹配
        metadata = extract_metadata_from_filename(pdf_path)
        title = metadata.get('title', '')
        
        if title:
            return self.match_by_title(title, threshold)
        
        return None

def match_pdf_with_database(pdf_path: str) -> Tuple[bool, Optional[Paper], Optional[Dict[str, Any]]]:
    """
    将PDF与数据库中的记录进行匹配
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        匹配结果元组 (是否匹配成功, 匹配的论文对象, OCR结果)
    """
    matcher = MetadataMatcher()
    
    # 匹配论文
    paper = matcher.match_by_metadata(pdf_path)
    
    if paper:
        # 获取OCR结果
        ocr_result = matcher.db_manager.get_ocr_result_by_paper_id(paper.id)
        
        if ocr_result:
            # 检查OCR结果文件是否存在
            if (os.path.exists(ocr_result.ocr_path) and
                os.path.exists(ocr_result.markdown_path) and
                (not ocr_result.content_list_path or os.path.exists(ocr_result.content_list_path))):
                
                # 返回匹配成功的结果
                return True, paper, ocr_result.to_dict()
    
    # 匹配失败
    return False, paper, None

if __name__ == "__main__":
    # 示例用法
    import argparse
    
    parser = argparse.ArgumentParser(description="匹配PDF与数据库中的记录")
    parser.add_argument("pdf_path", help="PDF文件路径")
    
    args = parser.parse_args()
    
    matched, paper, ocr_result = match_pdf_with_database(args.pdf_path)
    
    if matched:
        print(f"匹配成功！")
        print(f"论文: {paper.title}")
        print(f"作者: {paper.to_dict()['authors']}")
        print(f"年份: {paper.publication_year}")
        print(f"OCR结果路径: {ocr_result['ocr_path']}")
        print(f"Markdown路径: {ocr_result['markdown_path']}")
        print(f"内容列表路径: {ocr_result['content_list_path']}")
    elif paper:
        print(f"找到匹配的论文，但OCR结果不存在或不完整")
        print(f"论文: {paper.title}")
        print(f"作者: {paper.to_dict()['authors']}")
        print(f"年份: {paper.publication_year}")
    else:
        print(f"未找到匹配的论文") 