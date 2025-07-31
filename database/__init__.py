#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库模块

提供论文元数据和OCR结果的数据库操作
"""

from database.models import Paper, OCRResult, calculate_file_hash
from database.db_manager import DatabaseManager 