#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
论文处理流水线数据模型定义

这个模块定义了四阶段流水线处理过程中使用的所有数据结构，
包括配置、结果和状态管理等核心数据模型。

作者: Claude 4.0 Opus
创建时间: 2025-01-27
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Union
from pathlib import Path
import json
from enum import Enum

# 导入统一的LLM配置
try:
    from utils.llm_config import get_api_config, CURRENT_API
    llm_config_available = True
except ImportError:
    print("警告: 无法导入utils.llm_config，将使用默认配置")
    llm_config_available = False
    CURRENT_API = "default"


class ProcessingStage(Enum):
    """处理阶段枚举"""
    METADATA_EXTRACTION = "metadata_extraction"  # 第一阶段：元数据提取
    FULL_OCR = "full_ocr"                        # 第二阶段：全文OCR
    STRUCTURE_PARSING = "structure_parsing"      # 第三阶段：结构化解析
    REPORT_GENERATION = "report_generation"      # 第四阶段：报告生成
    POST_PROCESSING = "post_processing"          # 第五阶段：后处理


class ProcessingStatus(Enum):
    """处理状态枚举"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineConfig:
    """流水线配置类"""
    # 基础配置
    output_dir: str = "output"
    api_name: Optional[str] = None
    
    # 模板路径配置
    template_paths: Dict[str, str] = field(default_factory=lambda: {
        "metadata": "resources/extract_metadata_from_face_page.md",
        "structure": "resources/extract_frame_and_tabs_figs.md",
        "abstract_intro": "resources/extract_abstract_intro.md"
    })
    
    # LLM配置
    llm_config: Dict[str, Any] = field(default_factory=lambda: {
        "temperature": 0.2,
        "max_tokens": 100000  # 这个配置不知道有没有影响
    })
    
    # PDF裁剪参数
    crop_params: Optional[Dict[str, float]] = None
    
    # 处理选项
    keep_intermediate_files: bool = False
    enable_progress_callback: bool = True
    max_retry_attempts: int = 3
    
    def __post_init__(self):
        """后初始化处理"""
        # 如果没有指定API名称，使用默认配置
        if self.api_name is None and llm_config_available:
            self.api_name = CURRENT_API
            print(f"使用默认API配置: {self.api_name}")

        # 确保输出目录存在
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # 验证模板文件存在
        for template_name, template_path in self.template_paths.items():
            if not Path(template_path).exists():
                print(f"警告: 模板文件不存在: {template_path}")

        # 如果有LLM配置可用，更新LLM配置
        if llm_config_available and self.api_name:
            try:
                api_config = get_api_config(self.api_name)
                # 合并API配置到LLM配置中
                self.llm_config.update({
                    "api_url": api_config.get("api_url"),
                    "api_key": api_config.get("api_key"),
                    "default_model": api_config.get("default_model"),
                    "temperature": api_config.get("temperature", self.llm_config.get("temperature", 0.2)),
                    "max_retries": api_config.get("max_retries", 3),
                    "retry_base_delay": api_config.get("retry_base_delay", 1),
                    "reasoner": api_config.get("reasoner", False)
                })
                print(f"已加载API配置: {self.api_name} -> {api_config.get('api_url')}")
            except Exception as e:
                print(f"警告: 加载API配置失败: {e}")


@dataclass
class StageResult:
    """单阶段处理结果"""
    stage: ProcessingStage
    status: ProcessingStatus
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    processing_time: float = 0.0
    
    # 输出文件路径
    output_path: Optional[str] = None
    
    # 结果数据
    metadata: Optional[Dict[str, Any]] = None
    
    # 错误信息
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # 中间文件路径（用于清理）
    intermediate_files: List[str] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        """是否成功"""
        return self.status == ProcessingStatus.COMPLETED
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "processing_time": self.processing_time,
            "output_path": str(self.output_path) if self.output_path else None,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "success": self.success
        }


@dataclass
class PipelineResult:
    """完整流水线处理结果"""
    # 基本信息
    input_pdf: str
    output_dir: str
    pdf_name: str
    
    # 处理状态
    overall_status: ProcessingStatus = ProcessingStatus.NOT_STARTED
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    total_processing_time: float = 0.0
    
    # 各阶段结果
    stages: Dict[ProcessingStage, StageResult] = field(default_factory=dict)
    
    # 最终输出
    final_report_path: Optional[str] = None
    metadata_path: Optional[str] = None
    structure_path: Optional[str] = None
    
    # 错误信息
    pipeline_error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """整体是否成功"""
        return self.overall_status == ProcessingStatus.COMPLETED
    
    def get_stage_result(self, stage: ProcessingStage) -> Optional[StageResult]:
        """获取指定阶段的结果"""
        return self.stages.get(stage)
    
    def add_stage_result(self, result: StageResult):
        """添加阶段结果"""
        self.stages[result.stage] = result
    
    def get_completed_stages(self) -> List[ProcessingStage]:
        """获取已完成的阶段"""
        return [stage for stage, result in self.stages.items() 
                if result.status == ProcessingStatus.COMPLETED]
    
    def get_failed_stages(self) -> List[ProcessingStage]:
        """获取失败的阶段"""
        return [stage for stage, result in self.stages.items() 
                if result.status == ProcessingStatus.FAILED]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "input_pdf": str(self.input_pdf) if self.input_pdf else None,
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "pdf_name": str(self.pdf_name) if self.pdf_name else None,
            "overall_status": self.overall_status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_processing_time": self.total_processing_time,
            "stages": {stage.value: result.to_dict() for stage, result in self.stages.items()},
            "final_report_path": str(self.final_report_path) if self.final_report_path else None,
            "metadata_path": str(self.metadata_path) if self.metadata_path else None,
            "structure_path": str(self.structure_path) if self.structure_path else None,
            "success": self.success,
            "pipeline_error": self.pipeline_error
        }
    
    def save_to_file(self, file_path: str):
        """保存结果到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


@dataclass
class ProgressInfo:
    """进度信息"""
    current_stage: ProcessingStage
    stage_progress: float  # 当前阶段进度 0.0-1.0
    overall_progress: float  # 整体进度 0.0-1.0
    message: str
    estimated_remaining_time: Optional[float] = None


# 类型别名
ProgressCallback = Callable[[ProgressInfo], None]
ErrorCallback = Callable[[ProcessingStage, Exception], None]
