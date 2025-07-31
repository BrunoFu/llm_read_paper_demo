#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
论文处理流水线服务层

这是四阶段论文处理流水线的核心门面类，提供统一的函数式接口，
避免命令行调用，便于调试和集成。

核心工作流程：研究 → 架构 → 计划 → 执行 → 测评

作者: Claude 4.0 Opus
创建时间: 2025-01-27
"""

import os
import time
import asyncio
import traceback
from typing import Optional, Dict, Any
from pathlib import Path
import logging

from .pipeline_models import (
    PipelineConfig, PipelineResult, StageResult, ProgressInfo,
    ProcessingStage, ProcessingStatus, ProgressCallback, ErrorCallback
)

# 导入统一的LLM配置
try:
    from utils.llm_config import get_api_config, get_default_model, CURRENT_API
except ImportError:
    print("警告: 无法导入utils.llm_config，将使用默认配置")
    def get_api_config(api_name=None):
        return {"api_key": "default", "api_url": "default"}
    def get_default_model(api_name=None):
        return "default-model"
    CURRENT_API = "default"

# 配置日志
logger = logging.getLogger(__name__)


class PaperProcessingService:
    """论文处理服务门面类
    
    这个类封装了四阶段流水线的完整处理逻辑：
    1. 元数据提取 (crop_pdf_first_three_page)
    2. 全文OCR (pdf_content_extractor) 
    3. 结构化解析 (section_data_extractor)
    4. 报告生成 (report_generator)
    """
    
    def __init__(self, config: PipelineConfig):
        """初始化服务
        
        Args:
            config: 流水线配置
        """
        self.config = config
        self.progress_callback: Optional[ProgressCallback] = None
        self.error_callback: Optional[ErrorCallback] = None
        
        # 阶段权重（用于计算整体进度）
        self.stage_weights = {
            ProcessingStage.METADATA_EXTRACTION: 0.15,
            ProcessingStage.FULL_OCR: 0.30,
            ProcessingStage.STRUCTURE_PARSING: 0.25,
            ProcessingStage.REPORT_GENERATION: 0.25,
            ProcessingStage.POST_PROCESSING: 0.05
        }
    
    def set_progress_callback(self, callback: ProgressCallback):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def set_error_callback(self, callback: ErrorCallback):
        """设置错误回调函数"""
        self.error_callback = callback
    
    def _notify_progress(self, stage: ProcessingStage, stage_progress: float, message: str):
        """通知进度更新"""
        if not self.progress_callback:
            return
        
        # 计算整体进度
        overall_progress = 0.0
        for s, weight in self.stage_weights.items():
            if s.value < stage.value:
                overall_progress += weight
            elif s == stage:
                overall_progress += weight * stage_progress
        
        progress_info = ProgressInfo(
            current_stage=stage,
            stage_progress=stage_progress,
            overall_progress=min(overall_progress, 1.0),
            message=message
        )
        
        try:
            self.progress_callback(progress_info)
        except Exception as e:
            logger.warning(f"进度回调函数执行失败: {e}")
        
        logger.info(f"[{stage.value}] {stage_progress:.1%}: {message}")
    
    def _notify_error(self, stage: ProcessingStage, error: Exception):
        """通知错误"""
        if self.error_callback:
            try:
                self.error_callback(stage, error)
            except Exception as e:
                logger.warning(f"错误回调函数执行失败: {e}")

        logger.error(f"[{stage.value}] 处理失败: {error}")

    def _check_stage_completed(self, stage: ProcessingStage, output_dir: str, paper_name: str) -> bool:
        """检查指定阶段是否已完成"""
        if stage == ProcessingStage.METADATA_EXTRACTION:
            metadata_file = os.path.join(output_dir, f"{paper_name}_metadata.json")
            first_pages_file = os.path.join(output_dir, f"{paper_name}_first_three_pages.md")
            return os.path.exists(metadata_file) and os.path.exists(first_pages_file)

        elif stage == ProcessingStage.FULL_OCR:
            complete_md_file = os.path.join(output_dir, "complete.md")
            return os.path.exists(complete_md_file)

        elif stage == ProcessingStage.STRUCTURE_PARSING:
            structure_file = os.path.join(output_dir, "paper_structure.json")
            attribute_tree_file = os.path.join(output_dir, f"{paper_name}_attribute_tree.json")
            return os.path.exists(structure_file) and os.path.exists(attribute_tree_file)

        elif stage == ProcessingStage.REPORT_GENERATION:
            # 查找最终报告文件
            possible_report_files = [
                os.path.join(output_dir, "final_report.md"),
                os.path.join(output_dir, "report.md"),
                os.path.join(output_dir, f"{paper_name}_report.md")
            ]
            return any(os.path.exists(f) for f in possible_report_files)

        return False
    
    async def process_paper(self, pdf_path: str) -> PipelineResult:
        """处理论文的主门面函数
        
        这是整个流水线的核心入口函数，按顺序执行四个阶段的处理。
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            PipelineResult: 完整的处理结果
        """
        start_time = time.time()
        pdf_name = Path(pdf_path).stem
        output_dir = os.path.join(self.config.output_dir, pdf_name)
        
        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 初始化结果对象
        result = PipelineResult(
            input_pdf=pdf_path,
            output_dir=output_dir,
            pdf_name=pdf_name,
            overall_status=ProcessingStatus.IN_PROGRESS,
            start_time=start_time
        )
        
        try:
            logger.info(f"开始处理论文: {pdf_path}")

            # 检查断点续传 - 第一阶段：元数据提取
            if self._check_stage_completed(ProcessingStage.METADATA_EXTRACTION, output_dir, pdf_name):
                logger.info("第一阶段已完成，跳过元数据提取")
                self._notify_progress(ProcessingStage.METADATA_EXTRACTION, 1.0, "第一阶段已完成（断点续传）")
                # 创建一个成功的阶段结果
                stage1_result = StageResult(
                    stage=ProcessingStage.METADATA_EXTRACTION,
                    status=ProcessingStatus.COMPLETED,
                    start_time=time.time(),
                    end_time=time.time(),
                    processing_time=0.0,
                    output_path=os.path.join(output_dir, f"{pdf_name}_metadata.json")
                )
            else:
                stage1_result = await self._run_stage1(pdf_path, output_dir)

            result.add_stage_result(stage1_result)

            if not stage1_result.success:
                result.overall_status = ProcessingStatus.FAILED
                result.pipeline_error = f"第一阶段失败: {stage1_result.error_message}"
                return result
            
            # 检查断点续传 - 第二阶段：全文OCR
            if self._check_stage_completed(ProcessingStage.FULL_OCR, output_dir, pdf_name):
                logger.info("第二阶段已完成，跳过全文OCR")
                self._notify_progress(ProcessingStage.FULL_OCR, 1.0, "第二阶段已完成（断点续传）")
                stage2_result = StageResult(
                    stage=ProcessingStage.FULL_OCR,
                    status=ProcessingStatus.COMPLETED,
                    start_time=time.time(),
                    end_time=time.time(),
                    processing_time=0.0,
                    output_path=os.path.join(output_dir, "complete.md")
                )
            else:
                stage2_result = await self._run_stage2(pdf_path, output_dir)

            result.add_stage_result(stage2_result)

            if not stage2_result.success:
                result.overall_status = ProcessingStatus.FAILED
                result.pipeline_error = f"第二阶段失败: {stage2_result.error_message}"
                return result
            
            # 检查断点续传 - 第三阶段：结构化解析
            if self._check_stage_completed(ProcessingStage.STRUCTURE_PARSING, output_dir, pdf_name):
                logger.info("第三阶段已完成，跳过结构化解析")
                self._notify_progress(ProcessingStage.STRUCTURE_PARSING, 1.0, "第三阶段已完成（断点续传）")
                stage3_result = StageResult(
                    stage=ProcessingStage.STRUCTURE_PARSING,
                    status=ProcessingStatus.COMPLETED,
                    start_time=time.time(),
                    end_time=time.time(),
                    processing_time=0.0,
                    output_path=os.path.join(output_dir, f"{pdf_name}_attribute_tree.json")
                )
            else:
                stage3_result = await self._run_stage3(stage2_result.output_path, output_dir)

            result.add_stage_result(stage3_result)

            if not stage3_result.success:
                result.overall_status = ProcessingStatus.FAILED
                result.pipeline_error = f"第三阶段失败: {stage3_result.error_message}"
                return result
            
            # 检查断点续传 - 第四阶段：报告生成
            if self._check_stage_completed(ProcessingStage.REPORT_GENERATION, output_dir, pdf_name):
                logger.info("第四阶段已完成，跳过报告生成")
                self._notify_progress(ProcessingStage.REPORT_GENERATION, 1.0, "第四阶段已完成（断点续传）")
                # 查找最终报告文件
                possible_report_files = [
                    os.path.join(output_dir, "final_report.md"),
                    os.path.join(output_dir, "report.md"),
                    os.path.join(output_dir, f"{pdf_name}_report.md")
                ]
                final_report_path = next((f for f in possible_report_files if os.path.exists(f)), possible_report_files[0])

                stage4_result = StageResult(
                    stage=ProcessingStage.REPORT_GENERATION,
                    status=ProcessingStatus.COMPLETED,
                    start_time=time.time(),
                    end_time=time.time(),
                    processing_time=0.0,
                    output_path=final_report_path
                )
            else:
                stage4_result = await self._run_stage4(stage3_result.output_path, output_dir)

            result.add_stage_result(stage4_result)

            if not stage4_result.success:
                result.overall_status = ProcessingStatus.FAILED
                result.pipeline_error = f"第四阶段失败: {stage4_result.error_message}"
                return result

            # 第五阶段：后处理
            stage5_result = await self._run_stage5(output_dir)
            result.add_stage_result(stage5_result)

            # 设置最终结果
            if stage5_result.success:
                result.overall_status = ProcessingStatus.COMPLETED
                result.final_report_path = stage4_result.output_path
                result.metadata_path = stage1_result.output_path
                result.structure_path = stage3_result.output_path
            else:
                result.overall_status = ProcessingStatus.FAILED
                result.pipeline_error = f"第五阶段失败: {stage5_result.error_message}"
            
        except Exception as e:
            logger.error(f"流水线处理发生未预期错误: {str(e)}")
            result.overall_status = ProcessingStatus.FAILED
            result.pipeline_error = f"流水线异常: {str(e)}"
            
            # 添加异常阶段结果
            error_result = StageResult(
                stage=ProcessingStage.METADATA_EXTRACTION,  # 默认阶段
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                error_traceback=traceback.format_exc()
            )
            result.add_stage_result(error_result)
        
        finally:
            result.end_time = time.time()
            result.total_processing_time = result.end_time - result.start_time
            
            # 保存处理结果
            result_file = os.path.join(output_dir, "pipeline_result.json")
            result.save_to_file(result_file)
            
            logger.info(f"处理完成，总耗时: {result.total_processing_time:.2f}秒")
        
        return result
    
    async def _run_stage1(self, pdf_path: str, output_dir: str) -> StageResult:
        """第一阶段：元数据提取"""
        stage = ProcessingStage.METADATA_EXTRACTION
        self._notify_progress(stage, 0.0, "开始元数据提取...")
        
        result = StageResult(
            stage=stage,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=time.time()
        )
        
        try:
            # 动态导入第一阶段模块
            from crop_pdf_first_three_page.process_pdf import process_pdf as stage1_process

            self._notify_progress(stage, 0.3, "调用MinerU OCR服务...")

            # 添加重试机制
            max_retries = 3
            retry_count = 0
            metadata = None

            while retry_count < max_retries:
                try:
                    metadata = await stage1_process(
                        input_pdf=pdf_path,
                        output_dir=output_dir,
                        template_path=self.config.template_paths["metadata"],
                        api_name=self.config.api_name,
                        crop_params=self.config.crop_params
                    )
                    break  # 成功则跳出重试循环
                except Exception as e:
                    retry_count += 1
                    error_msg = str(e)
                    if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                        if retry_count < max_retries:
                            self._notify_progress(stage, 0.3, f"网络超时，正在重试 ({retry_count}/{max_retries})...")
                            continue
                    raise e  # 非超时错误或重试次数用完，直接抛出异常

            if metadata is None:
                raise RuntimeError("第一阶段处理失败：重试次数已用完")
            
            # 设置输出路径
            metadata_file = os.path.join(output_dir, f"{Path(pdf_path).stem}_metadata.json")
            
            result.status = ProcessingStatus.COMPLETED
            result.output_path = metadata_file
            result.metadata = metadata
            
            self._notify_progress(stage, 1.0, "元数据提取完成")
            
        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.error_message = str(e)
            result.error_traceback = traceback.format_exc()
            self._notify_error(stage, e)
        
        finally:
            result.end_time = time.time()
            result.processing_time = result.end_time - result.start_time
        
        return result

    async def _run_stage2(self, pdf_path: str, output_dir: str) -> StageResult:
        """第二阶段：全文OCR"""
        stage = ProcessingStage.FULL_OCR
        self._notify_progress(stage, 0.0, "开始全文OCR处理...")

        result = StageResult(
            stage=stage,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=time.time()
        )

        try:
            # 动态导入第二阶段模块
            from pdf_content_extractor.pdf_ocr import process_pdf as stage2_process

            self._notify_progress(stage, 0.2, "调用Mistral OCR服务...")

            # 调用第二阶段处理
            stage2_process(pdf_path=pdf_path, output_dir_arg=output_dir)

            # 设置输出路径
            complete_md_path = os.path.join(output_dir, "complete.md")

            if not os.path.exists(complete_md_path):
                raise FileNotFoundError(f"全文OCR输出文件不存在: {complete_md_path}")

            result.status = ProcessingStatus.COMPLETED
            result.output_path = complete_md_path

            self._notify_progress(stage, 1.0, "全文OCR处理完成")

        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.error_message = str(e)
            result.error_traceback = traceback.format_exc()
            self._notify_error(stage, e)

        finally:
            result.end_time = time.time()
            result.processing_time = result.end_time - result.start_time

        return result

    async def _run_stage3(self, complete_md_path: str, output_dir: str) -> StageResult:
        """第三阶段：结构化解析"""
        stage = ProcessingStage.STRUCTURE_PARSING
        self._notify_progress(stage, 0.0, "开始结构化解析...")

        result = StageResult(
            stage=stage,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=time.time()
        )

        try:
            # 首先进行结构化解析
            from section_data_extractor.integrated_processor import process_paper_structure

            self._notify_progress(stage, 0.2, "提取论文框架结构...")

            # 调用结构化解析
            structure_success = await process_paper_structure(
                input_md_path=complete_md_path,
                output_dir=output_dir
            )

            if not structure_success:
                raise RuntimeError("结构化解析处理失败")

            # 然后进行论文类型分类和属性树提取
            self._notify_progress(stage, 0.5, "进行论文类型分类...")

            # 动态导入属性树提取模块
            from attribute_tree_extractor import PaperTypeClassifier, AttributeTreeExtractor

            # 获取论文名称（从路径中提取）
            paper_name = Path(complete_md_path).stem.replace("_full", "")

            # 初始化分类器和提取器
            classifier = PaperTypeClassifier(api_name=CURRENT_API)
            extractor = AttributeTreeExtractor(api_name=CURRENT_API)

            # 进行论文分类
            classification_result = await classifier.classify_paper(
                paper_name=paper_name,
                output_dir=output_dir,
                template_path=self.config.template_paths.get("paper_type_classify", "resources/paper_type_classify.md")
            )

            self._notify_progress(stage, 0.7, "提取论文属性树...")

            # 确定论文类型
            paper_type = PaperTypeClassifier.determine_paper_type(classification_result)

            # 提取属性树
            attribute_tree = await extractor.extract_attribute_tree(
                paper_name=paper_name,
                output_dir=output_dir,
                paper_type=paper_type,
                empirical_template_path=self.config.template_paths.get("extract_attribute_tree_empirical", "resources/extract_attribute_tree_empirical.md"),
                structural_template_path=self.config.template_paths.get("extract_attribute_tree_structural", "resources/extract_attribute_tree_structural.md")
            )

            # 查找输出的属性树文件
            attribute_tree_path = os.path.join(output_dir, f"{paper_name}_attribute_tree.json")

            result.status = ProcessingStatus.COMPLETED
            result.output_path = attribute_tree_path

            self._notify_progress(stage, 1.0, "论文内容分析完成")

        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.error_message = str(e)
            result.error_traceback = traceback.format_exc()
            self._notify_error(stage, e)

        finally:
            result.end_time = time.time()
            result.processing_time = result.end_time - result.start_time

        return result

    async def _run_stage4(self, structure_json_path: str, output_dir: str) -> StageResult:
        """第四阶段：报告生成"""
        stage = ProcessingStage.REPORT_GENERATION
        self._notify_progress(stage, 0.0, "开始生成报告...")

        result = StageResult(
            stage=stage,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=time.time()
        )

        try:
            self._notify_progress(stage, 0.2, "准备报告生成...")

            # 获取论文名称（从路径中提取）
            paper_name = Path(structure_json_path).stem.replace("_attribute_tree", "")

            # 查找结构化JSON文件（用于报告生成）
            structure_files = list(Path(output_dir).glob("*_paper_structure.json"))
            if not structure_files:
                structure_files = list(Path(output_dir).glob("paper_structure.json"))

            if not structure_files:
                raise FileNotFoundError("未找到结构化解析文件，无法生成报告")

            structure_json_file = str(structure_files[0])

            self._notify_progress(stage, 0.5, "调用报告生成模块...")

            # 动态导入报告生成模块
            from report_generator.LLM_for_paper_reading_updated import process_paper_report

            # 生成逐节深度分析报告
            final_report_path = await process_paper_report(
                json_path=structure_json_file,
                output_path=output_dir,
                reasoner=True
            )

            result.status = ProcessingStatus.COMPLETED
            result.output_path = final_report_path

            self._notify_progress(stage, 1.0, "深度分析报告生成完成")

        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.error_message = str(e)
            result.error_traceback = traceback.format_exc()
            self._notify_error(stage, e)

        finally:
            result.end_time = time.time()
            result.processing_time = result.end_time - result.start_time

        return result

    async def _run_stage5(self, output_dir: str) -> StageResult:
        """第五阶段：后处理"""
        stage = ProcessingStage.POST_PROCESSING
        self._notify_progress(stage, 0.0, "开始后处理...")

        result = StageResult(
            stage=stage,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=time.time()
        )

        try:
            self._notify_progress(stage, 0.3, "清理中间文件...")

            # 动态导入第五阶段模块
            from tools.stage5_post_processor import Stage5PostProcessor

            # 创建后处理器
            processor = Stage5PostProcessor()

            # 处理单个论文文件夹
            paper_folder = Path(output_dir)
            post_result = processor.process_paper_folder(paper_folder)

            if post_result["success"]:
                result.status = ProcessingStatus.COMPLETED
                result.output_path = str(output_dir)
                self._notify_progress(stage, 1.0, "后处理完成")
            else:
                result.status = ProcessingStatus.FAILED
                result.error_message = "; ".join(post_result["errors"])

        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.error_message = str(e)
            result.error_traceback = traceback.format_exc()
            self._notify_error(stage, e)

        finally:
            result.end_time = time.time()
            result.processing_time = result.end_time - result.start_time

        return result




# 便捷函数
async def process_paper_pipeline(
    pdf_path: str,
    config: Optional[PipelineConfig] = None,
    progress_callback: Optional[ProgressCallback] = None,
    error_callback: Optional[ErrorCallback] = None
) -> PipelineResult:
    """
    处理论文的便捷函数

    Args:
        pdf_path: PDF文件路径
        config: 流水线配置，如果为None则使用默认配置
        progress_callback: 进度回调函数
        error_callback: 错误回调函数

    Returns:
        PipelineResult: 处理结果
    """
    if config is None:
        config = PipelineConfig()

    service = PaperProcessingService(config)

    if progress_callback:
        service.set_progress_callback(progress_callback)

    if error_callback:
        service.set_error_callback(error_callback)

    return await service.process_paper(pdf_path)
