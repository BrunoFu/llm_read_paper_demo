#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
论文处理工具包

这个包包含了四阶段论文处理流水线的封装服务和相关工具。

主要模块：
- pipeline_models: 数据模型定义
- paper_processing_service: 核心服务类
- test_pipeline_service: 测试脚本
- example_usage: 使用示例

作者: Claude 4.0 Opus
"""

# 导入流水线封装模块
try:
    from .pipeline_models import (
        PipelineConfig,
        PipelineResult,
        StageResult,
        ProgressInfo,
        ProcessingStage,
        ProcessingStatus,
        ProgressCallback,
        ErrorCallback
    )

    from .paper_processing_service import (
        PaperProcessingService,
        process_paper_pipeline
    )

    # 流水线相关导出
    pipeline_exports = [
        "PipelineConfig",
        "PipelineResult",
        "StageResult",
        "ProgressInfo",
        "ProcessingStage",
        "ProcessingStatus",
        "ProgressCallback",
        "ErrorCallback",
        "PaperProcessingService",
        "process_paper_pipeline"
    ]
except ImportError as e:
    print(f"警告: 流水线模块导入失败: {e}")
    pipeline_exports = []

# 导入原有工具函数
try:
    from .metadata_extractor import (
        extract_metadata_from_filename,
        calculate_file_hash,
        process_pdf_file,
        process_directory
    )

    legacy_exports = [
        'extract_metadata_from_filename',
        'calculate_file_hash',
        'process_pdf_file',
        'process_directory'
    ]
except ImportError:
    legacy_exports = []

# 合并所有导出
__all__ = pipeline_exports + legacy_exports

__version__ = "1.0.0"
__author__ = "Claude 4.0 Opus"