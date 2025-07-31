#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库模型定义

定义论文元数据和OCR结果的数据模型
"""

import os
import json
import sqlite3
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

class Paper:
    """论文元数据模型"""
    
    def __init__(self, 
                 id: Optional[int] = None,
                 title: str = "",
                 authors: Union[str, List[Dict[str, str]]] = "",
                 journal_name: Optional[str] = None,
                 publication_date: Optional[str] = None,
                 doi: Optional[str] = None,
                 abstract: Optional[str] = None,
                 jel_classification: Union[str, List[str]] = "",
                 acknowledgements: Union[str, List[str]] = "",
                 research_assistants: Union[str, List[str]] = "",
                 conferences_and_seminars: Union[str, List[str]] = "",
                 funding_sources: Union[str, List[str]] = "",
                 file_hash: Optional[str] = None,
                 created_at: Optional[str] = None,
                 updated_at: Optional[str] = None):
        """
        初始化论文元数据对象
        
        Args:
            id: 论文ID
            title: 论文标题
            authors: 作者列表，可以是字符串或包含name和institution的字典列表
            journal_name: 期刊名称
            publication_date: 出版日期，如"2023年1月"
            doi: DOI标识符
            abstract: 摘要
            jel_classification: JEL分类代码列表
            acknowledgements: 致谢人员列表
            research_assistants: 研究助理列表
            conferences_and_seminars: 会议或研讨会列表
            funding_sources: 资金来源列表
            file_hash: 文件哈希值
            created_at: 创建时间
            updated_at: 更新时间
        """
        self.id = id
        self.title = title
        
        # 处理作者列表
        if isinstance(authors, list):
            self.authors = json.dumps(authors, ensure_ascii=False)
        else:
            self.authors = authors
        
        self.journal_name = journal_name
        self.publication_date = publication_date
        self.doi = doi
        self.abstract = abstract
        
        # 处理JEL分类代码列表
        if isinstance(jel_classification, list):
            self.jel_classification = json.dumps(jel_classification, ensure_ascii=False)
        else:
            self.jel_classification = jel_classification
        
        # 处理致谢人员列表
        if isinstance(acknowledgements, list):
            self.acknowledgements = json.dumps(acknowledgements, ensure_ascii=False)
        else:
            self.acknowledgements = acknowledgements
        
        # 处理研究助理列表
        if isinstance(research_assistants, list):
            self.research_assistants = json.dumps(research_assistants, ensure_ascii=False)
        else:
            self.research_assistants = research_assistants
        
        # 处理会议或研讨会列表
        if isinstance(conferences_and_seminars, list):
            self.conferences_and_seminars = json.dumps(conferences_and_seminars, ensure_ascii=False)
        else:
            self.conferences_and_seminars = conferences_and_seminars
        
        # 处理资金来源列表
        if isinstance(funding_sources, list):
            self.funding_sources = json.dumps(funding_sources, ensure_ascii=False)
        else:
            self.funding_sources = funding_sources
        
        self.file_hash = file_hash
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Paper':
        """
        从字典创建论文对象
        
        Args:
            data: 包含论文元数据的字典
            
        Returns:
            Paper对象
        """
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            authors=data.get('authors', []),
            journal_name=data.get('journal_name'),
            publication_date=data.get('publication_date'),
            doi=data.get('doi'),
            abstract=data.get('abstract'),
            jel_classification=data.get('jel_classification', []),
            acknowledgements=data.get('acknowledgements', []),
            research_assistants=data.get('research_assistants', []),
            conferences_and_seminars=data.get('conferences_and_seminars', []),
            funding_sources=data.get('funding_sources', []),
            file_hash=data.get('file_hash'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将论文对象转换为字典
        
        Returns:
            包含论文元数据的字典
        """
        result = {
            'id': self.id,
            'title': self.title,
            'journal_name': self.journal_name,
            'publication_date': self.publication_date,
            'doi': self.doi,
            'abstract': self.abstract,
            'file_hash': self.file_hash,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        # 处理作者列表
        if self.authors:
            try:
                result['authors'] = json.loads(self.authors)
            except json.JSONDecodeError:
                result['authors'] = self.authors
        else:
            result['authors'] = []
        
        # 处理JEL分类代码列表
        if self.jel_classification:
            try:
                result['jel_classification'] = json.loads(self.jel_classification)
            except json.JSONDecodeError:
                result['jel_classification'] = self.jel_classification
        else:
            result['jel_classification'] = []
        
        # 处理致谢人员列表
        if self.acknowledgements:
            try:
                result['acknowledgements'] = json.loads(self.acknowledgements)
            except json.JSONDecodeError:
                result['acknowledgements'] = self.acknowledgements
        else:
            result['acknowledgements'] = []
        
        # 处理研究助理列表
        if self.research_assistants:
            try:
                result['research_assistants'] = json.loads(self.research_assistants)
            except json.JSONDecodeError:
                result['research_assistants'] = self.research_assistants
        else:
            result['research_assistants'] = []
        
        # 处理会议或研讨会列表
        if self.conferences_and_seminars:
            try:
                result['conferences_and_seminars'] = json.loads(self.conferences_and_seminars)
            except json.JSONDecodeError:
                result['conferences_and_seminars'] = self.conferences_and_seminars
        else:
            result['conferences_and_seminars'] = []
        
        # 处理资金来源列表
        if self.funding_sources:
            try:
                result['funding_sources'] = json.loads(self.funding_sources)
            except json.JSONDecodeError:
                result['funding_sources'] = self.funding_sources
        else:
            result['funding_sources'] = []
        
        return result

class OCRResult:
    """OCR结果模型"""
    
    def __init__(self,
                 id: Optional[int] = None,
                 paper_id: int = 0,
                 ocr_path: str = "",
                 markdown_path: str = "",
                 content_list_path: Optional[str] = None,
                 processed_at: Optional[str] = None):
        """
        初始化OCR结果对象
        
        Args:
            id: OCR结果ID
            paper_id: 关联的论文ID
            ocr_path: OCR结果路径
            markdown_path: Markdown文件路径
            content_list_path: 内容列表路径
            processed_at: 处理时间
        """
        self.id = id
        self.paper_id = paper_id
        self.ocr_path = ocr_path
        self.markdown_path = markdown_path
        self.content_list_path = content_list_path
        self.processed_at = processed_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OCRResult':
        """
        从字典创建OCR结果对象
        
        Args:
            data: 包含OCR结果的字典
            
        Returns:
            OCRResult对象
        """
        return cls(
            id=data.get('id'),
            paper_id=data.get('paper_id', 0),
            ocr_path=data.get('ocr_path', ''),
            markdown_path=data.get('markdown_path', ''),
            content_list_path=data.get('content_list_path'),
            processed_at=data.get('processed_at')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将OCR结果对象转换为字典
        
        Returns:
            包含OCR结果的字典
        """
        return {
            'id': self.id,
            'paper_id': self.paper_id,
            'ocr_path': self.ocr_path,
            'markdown_path': self.markdown_path,
            'content_list_path': self.content_list_path,
            'processed_at': self.processed_at
        }

def calculate_file_hash(file_path: str) -> str:
    """
    计算文件的SHA-256哈希值
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件的哈希值
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # 读取文件的前10MB进行哈希计算
        # 这样可以加快处理速度，同时保持足够的唯一性
        chunk = f.read(10 * 1024 * 1024)
        sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest() 