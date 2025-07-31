"""
Report Generator Module

提供论文报告生成功能，包括：
- 逐节分析报告生成
- 论文阅读报告处理
- LLM驱动的深度分析
"""

from .LLM_for_paper_reading_updated import (
    get_openai_response_conversation,
    generate_report,
    process_paper_report
)
from .report_processor import process_report

__all__ = [
    'get_openai_response_conversation',
    'generate_report',
    'process_paper_report',
    'process_report'
]
