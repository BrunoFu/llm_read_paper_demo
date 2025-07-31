#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
罗斯福新政相关文献批量处理脚本

这个脚本将对指定文件夹中的所有PDF文献运行完整的四阶段处理流程：
1. 阶段1：元数据提取 (crop_pdf_first_three_page)
2. 阶段2：全文OCR (pdf_content_extractor) 
3. 阶段3：结构化解析 (section_data_extractor + attribute_tree_extractor)
4. 阶段4：报告生成 (report_generator)

作者: Claude 4.0 Opus
创建时间: 2025-01-29
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入流水线处理服务
try:
    from tools.paper_processing_service import PaperProcessingService, process_paper_pipeline
    from tools.pipeline_models import PipelineConfig, ProcessingStage, ProcessingStatus
except ImportError as e:
    print(f"导入流水线模块失败: {e}")
    print("请确保所有必要的模块都已正确安装")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/batch_process_fsz.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FSZPaperBatchProcessor:
    """罗斯福新政文献批量处理器"""
    
    def __init__(self, input_dir: str, output_dir: str):
        """
        初始化批量处理器
        
        Args:
            input_dir: 输入文献文件夹路径
            output_dir: 输出结果文件夹路径
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建日志目录
        Path("logs").mkdir(exist_ok=True)
        
        # 处理统计
        self.total_papers = 0
        self.processed_papers = 0
        self.successful_papers = 0
        self.failed_papers = 0
        self.processing_results = []
        
        logger.info(f"初始化FSZ文献批量处理器")
        logger.info(f"输入目录: {self.input_dir}")
        logger.info(f"输出目录: {self.output_dir}")
    
    def find_pdf_files(self) -> List[Path]:
        """查找所有PDF文件"""
        pdf_files = []
        
        if not self.input_dir.exists():
            logger.error(f"输入目录不存在: {self.input_dir}")
            return pdf_files
        
        # 递归查找所有PDF文件
        for pdf_file in self.input_dir.rglob("*.pdf"):
            if pdf_file.is_file():
                pdf_files.append(pdf_file)
        
        # 也查找PDF大写扩展名
        for pdf_file in self.input_dir.rglob("*.PDF"):
            if pdf_file.is_file():
                pdf_files.append(pdf_file)
        
        logger.info(f"找到 {len(pdf_files)} 个PDF文件")
        for pdf_file in pdf_files:
            logger.info(f"  - {pdf_file.name}")
        
        return pdf_files
    
    def progress_callback(self, progress_info):
        """进度回调函数"""
        stage_name = progress_info.current_stage.value
        stage_progress = progress_info.stage_progress * 100
        overall_progress = progress_info.overall_progress * 100
        
        print(f"[{stage_name}] {stage_progress:.1f}% | 总体进度: {overall_progress:.1f}% | {progress_info.message}")
    
    def error_callback(self, stage: ProcessingStage, error: Exception):
        """错误回调函数"""
        logger.error(f"阶段 {stage.value} 发生错误: {error}")
    
    async def process_single_paper(self, pdf_path: Path) -> Dict[str, Any]:
        """处理单个论文"""
        paper_name = pdf_path.stem
        logger.info(f"\n{'='*60}")
        logger.info(f"开始处理论文: {paper_name}")
        logger.info(f"文件路径: {pdf_path}")
        logger.info(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # 创建流水线配置
            config = PipelineConfig(
                output_dir=str(self.output_dir),
                template_paths={
                    "metadata": "resources/extract_metadata_from_face_page.md",
                    "paper_type_classify": "resources/paper_type_classify.md", 
                    "extract_attribute_tree_empirical": "resources/extract_attribute_tree_empirical.md",
                    "extract_attribute_tree_structural": "resources/extract_attribute_tree_structural.md"
                }
            )
            
            # 处理论文
            result = await process_paper_pipeline(
                pdf_path=str(pdf_path),
                config=config,
                progress_callback=self.progress_callback,
                error_callback=self.error_callback
            )
            
            processing_time = time.time() - start_time
            
            # 记录结果
            paper_result = {
                "paper_name": paper_name,
                "pdf_path": str(pdf_path),
                "output_dir": result.output_dir,
                "status": result.overall_status.value,
                "processing_time": processing_time,
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "stages": {}
            }
            
            # 记录各阶段结果
            for stage_result in result.stages.values():
                paper_result["stages"][stage_result.stage.value] = {
                    "status": stage_result.status.value,
                    "processing_time": stage_result.processing_time,
                    "output_path": stage_result.output_path,
                    "error_message": stage_result.error_message
                }
            
            if result.overall_status == ProcessingStatus.COMPLETED:
                self.successful_papers += 1
                logger.info(f"✅ 论文 {paper_name} 处理成功，耗时 {processing_time:.2f}秒")
                paper_result["final_report_path"] = result.final_report_path
                paper_result["metadata_path"] = result.metadata_path
                paper_result["structure_path"] = result.structure_path
            else:
                self.failed_papers += 1
                logger.error(f"❌ 论文 {paper_name} 处理失败: {result.pipeline_error}")
                paper_result["error"] = result.pipeline_error
            
            return paper_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.failed_papers += 1
            logger.error(f"❌ 论文 {paper_name} 处理异常: {str(e)}")
            
            return {
                "paper_name": paper_name,
                "pdf_path": str(pdf_path),
                "status": "FAILED",
                "processing_time": processing_time,
                "error": str(e),
                "start_time": datetime.fromtimestamp(start_time).isoformat()
            }
    
    async def process_all_papers(self):
        """批量处理所有论文"""
        # 查找所有PDF文件
        pdf_files = self.find_pdf_files()
        
        if not pdf_files:
            logger.warning("未找到任何PDF文件")
            return
        
        self.total_papers = len(pdf_files)
        logger.info(f"开始批量处理 {self.total_papers} 个PDF文件")
        
        batch_start_time = time.time()
        
        # 逐个处理PDF文件
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"\n进度: {i}/{self.total_papers}")
            
            # 处理单个论文
            result = await self.process_single_paper(pdf_file)
            self.processing_results.append(result)
            self.processed_papers += 1
            
            # 显示当前统计
            logger.info(f"当前统计: 已处理 {self.processed_papers}/{self.total_papers}, 成功 {self.successful_papers}, 失败 {self.failed_papers}")
        
        batch_processing_time = time.time() - batch_start_time
        
        # 保存批量处理结果
        self.save_batch_results(batch_processing_time)
        
        # 显示最终统计
        self.print_final_statistics(batch_processing_time)
    
    def save_batch_results(self, total_time: float):
        """保存批量处理结果"""
        batch_result = {
            "batch_info": {
                "input_dir": str(self.input_dir),
                "output_dir": str(self.output_dir),
                "total_papers": self.total_papers,
                "processed_papers": self.processed_papers,
                "successful_papers": self.successful_papers,
                "failed_papers": self.failed_papers,
                "total_processing_time": total_time,
                "average_time_per_paper": total_time / max(self.processed_papers, 1),
                "timestamp": datetime.now().isoformat()
            },
            "paper_results": self.processing_results
        }
        
        # 保存到JSON文件
        result_file = self.output_dir / "batch_processing_results.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(batch_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"批量处理结果已保存到: {result_file}")
    
    def print_final_statistics(self, total_time: float):
        """打印最终统计信息"""
        logger.info(f"\n{'='*80}")
        logger.info(f"批量处理完成！")
        logger.info(f"{'='*80}")
        logger.info(f"总论文数量: {self.total_papers}")
        logger.info(f"已处理数量: {self.processed_papers}")
        logger.info(f"成功处理: {self.successful_papers}")
        logger.info(f"处理失败: {self.failed_papers}")
        logger.info(f"成功率: {(self.successful_papers/max(self.processed_papers,1)*100):.1f}%")
        logger.info(f"总处理时间: {total_time:.2f}秒")
        logger.info(f"平均每篇论文: {total_time/max(self.processed_papers,1):.2f}秒")
        logger.info(f"结果保存目录: {self.output_dir}")
        logger.info(f"{'='*80}")


async def main():
    """主函数"""
    # 配置路径
    input_dir = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/fszRA/policy_paper_extract/罗斯福新政影响相关文献"
    output_dir = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/fsz_ra_papers"
    
    # 创建批量处理器
    processor = FSZPaperBatchProcessor(input_dir, output_dir)
    
    # 开始批量处理
    await processor.process_all_papers()


if __name__ == "__main__":
    # 运行批量处理
    asyncio.run(main())
