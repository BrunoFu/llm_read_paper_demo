#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库管理器

管理论文元数据和OCR结果的数据库操作
"""

import os
import sqlite3
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

from database.models import Paper, OCRResult, calculate_file_hash

# 数据库文件路径
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'papers.db')

class DatabaseManager:
    """数据库管理器类"""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.initialize_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接
        
        Returns:
            数据库连接对象
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        return conn
    
    def initialize_db(self) -> None:
        """
        初始化数据库，创建必要的表（如果不存在）
        """
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='papers'")
        papers_table_exists = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ocr_results'")
        ocr_results_table_exists = cursor.fetchone() is not None
        
        # 如果表不存在，则创建表
        if not papers_table_exists:
            # 创建论文表（使用新的字段结构）
            cursor.execute('''
            CREATE TABLE papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                journal_name TEXT,
                publication_date TEXT,
                doi TEXT,
                abstract TEXT,
                jel_classification TEXT,
                acknowledgements TEXT,
                research_assistants TEXT,
                conferences_and_seminars TEXT,
                funding_sources TEXT,
                file_hash TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
        
        if not ocr_results_table_exists:
            # 创建OCR结果表
            cursor.execute('''
            CREATE TABLE ocr_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                ocr_path TEXT NOT NULL,
                markdown_path TEXT NOT NULL,
                content_list_path TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
            ''')
        
        conn.commit()
        conn.close()
    
    def add_paper(self, paper: Paper) -> int:
        """
        添加论文到数据库
        
        Args:
            paper: 论文对象
            
        Returns:
            新添加论文的ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查是否已存在相同哈希值的论文
        cursor.execute('SELECT id FROM papers WHERE file_hash = ?', (paper.file_hash,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return existing['id']
        
        # 添加新论文
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO papers (
            title, authors, journal_name, publication_date, doi, abstract, 
            jel_classification, acknowledgements, research_assistants, 
            conferences_and_seminars, funding_sources, file_hash, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            paper.title,
            paper.authors,
            paper.journal_name,
            paper.publication_date,
            paper.doi,
            paper.abstract,
            paper.jel_classification,
            paper.acknowledgements,
            paper.research_assistants,
            paper.conferences_and_seminars,
            paper.funding_sources,
            paper.file_hash,
            now,
            now
        ))
        
        paper_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return paper_id
    
    def update_paper(self, paper: Paper) -> bool:
        """
        更新论文信息
        
        Args:
            paper: 论文对象
            
        Returns:
            是否更新成功
        """
        if not paper.id:
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        UPDATE papers SET
            title = ?,
            authors = ?,
            journal_name = ?,
            publication_date = ?,
            doi = ?,
            abstract = ?,
            jel_classification = ?,
            acknowledgements = ?,
            research_assistants = ?,
            conferences_and_seminars = ?,
            funding_sources = ?,
            updated_at = ?
        WHERE id = ?
        ''', (
            paper.title,
            paper.authors,
            paper.journal_name,
            paper.publication_date,
            paper.doi,
            paper.abstract,
            paper.jel_classification,
            paper.acknowledgements,
            paper.research_assistants,
            paper.conferences_and_seminars,
            paper.funding_sources,
            now,
            paper.id
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_paper_by_id(self, paper_id: int) -> Optional[Paper]:
        """
        通过ID获取论文
        
        Args:
            paper_id: 论文ID
            
        Returns:
            论文对象，如果不存在则返回None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM papers WHERE id = ?', (paper_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return Paper(
                id=row['id'],
                title=row['title'],
                authors=row['authors'],
                journal_name=row['journal_name'],
                publication_date=row['publication_date'],
                doi=row['doi'],
                abstract=row['abstract'],
                jel_classification=row['jel_classification'],
                acknowledgements=row['acknowledgements'],
                research_assistants=row['research_assistants'],
                conferences_and_seminars=row['conferences_and_seminars'],
                funding_sources=row['funding_sources'],
                file_hash=row['file_hash'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        
        return None
    
    def get_paper_by_hash(self, file_hash: str) -> Optional[Paper]:
        """
        通过文件哈希值获取论文
        
        Args:
            file_hash: 文件哈希值
            
        Returns:
            论文对象，如果不存在则返回None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM papers WHERE file_hash = ?', (file_hash,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return Paper(
                id=row['id'],
                title=row['title'],
                authors=row['authors'],
                journal_name=row['journal_name'],
                publication_date=row['publication_date'],
                doi=row['doi'],
                abstract=row['abstract'],
                jel_classification=row['jel_classification'],
                acknowledgements=row['acknowledgements'],
                research_assistants=row['research_assistants'],
                conferences_and_seminars=row['conferences_and_seminars'],
                funding_sources=row['funding_sources'],
                file_hash=row['file_hash'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        
        return None
    
    def add_ocr_result(self, ocr_result: OCRResult) -> int:
        """
        添加OCR结果到数据库
        
        Args:
            ocr_result: OCR结果对象
            
        Returns:
            新添加OCR结果的ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查是否已存在相同paper_id的OCR结果
        cursor.execute('SELECT id FROM ocr_results WHERE paper_id = ?', (ocr_result.paper_id,))
        existing = cursor.fetchone()
        
        if existing:
            # 更新现有OCR结果
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
            UPDATE ocr_results SET
                ocr_path = ?,
                markdown_path = ?,
                content_list_path = ?,
                processed_at = ?
            WHERE id = ?
            ''', (
                ocr_result.ocr_path,
                ocr_result.markdown_path,
                ocr_result.content_list_path,
                now,
                existing['id']
            ))
            
            conn.commit()
            conn.close()
            
            return existing['id']
        
        # 添加新OCR结果
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO ocr_results (
            paper_id, ocr_path, markdown_path, content_list_path, processed_at
        ) VALUES (?, ?, ?, ?, ?)
        ''', (
            ocr_result.paper_id,
            ocr_result.ocr_path,
            ocr_result.markdown_path,
            ocr_result.content_list_path,
            now
        ))
        
        ocr_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return ocr_id
    
    def get_ocr_result_by_paper_id(self, paper_id: int) -> Optional[OCRResult]:
        """
        通过论文ID获取OCR结果
        
        Args:
            paper_id: 论文ID
            
        Returns:
            OCR结果对象，如果不存在则返回None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ocr_results WHERE paper_id = ?', (paper_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return OCRResult(
                id=row['id'],
                paper_id=row['paper_id'],
                ocr_path=row['ocr_path'],
                markdown_path=row['markdown_path'],
                content_list_path=row['content_list_path'],
                processed_at=row['processed_at']
            )
        
        return None
    
    def get_all_papers(self) -> List[Paper]:
        """
        获取所有论文
        
        Returns:
            论文对象列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM papers ORDER BY id DESC')
        rows = cursor.fetchall()
        
        conn.close()
        
        papers = []
        for row in rows:
            papers.append(Paper(
                id=row['id'],
                title=row['title'],
                authors=row['authors'],
                journal_name=row['journal_name'],
                publication_date=row['publication_date'],
                doi=row['doi'],
                abstract=row['abstract'],
                jel_classification=row['jel_classification'],
                acknowledgements=row['acknowledgements'],
                research_assistants=row['research_assistants'],
                conferences_and_seminars=row['conferences_and_seminars'],
                funding_sources=row['funding_sources'],
                file_hash=row['file_hash'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))
        
        return papers 