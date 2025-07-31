#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AER论文快速测试脚本

简化版的测试脚本，可以通过命令行参数指定文件夹路径。

使用方法:
python tools/quick_test_aer.py /path/to/AER202507

作者: Claude 4.0 Opus
创建时间: 2025-01-27
"""

import asyncio
import os
import sys
import time
from pathlib import Path
import argparse

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools import (
    PipelineConfig,
    process_paper_pipeline,
    ProgressInfo,
    ProcessingStage
)

# 导入LLM配置
try:
    from utils.llm_config import list_available_apis, CURRENT_API
    print(f"✅ 可用的API配置: {', '.join(list_available_apis())}")
    print(f"✅ 当前默认API: {CURRENT_API}")
except ImportError:
    print("⚠️ 无法导入LLM配置")


def create_progress_callback(paper_name: str):
    """创建进度回调函数"""
    def progress_callback(progress_info: ProgressInfo):
        # 创建进度条
        bar_length = 30
        filled_length = int(bar_length * progress_info.overall_progress)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # 阶段名称映射
        stage_names = {
            ProcessingStage.METADATA_EXTRACTION: "📋 元数据提取",
            ProcessingStage.FULL_OCR: "📄 全文OCR",
            ProcessingStage.STRUCTURE_PARSING: "🏗️  结构化解析",
            ProcessingStage.REPORT_GENERATION: "📊 报告生成"
        }
        
        stage_name = stage_names.get(progress_info.current_stage, "🔄 处理中")
        percentage = progress_info.overall_progress * 100
        
        print(f"\r{paper_name[:30]:<30} | {stage_name} [{bar}] {percentage:.1f}%", end='', flush=True)
    
    return progress_callback


def create_error_callback(paper_name: str):
    """创建错误回调函数"""
    def error_callback(stage: ProcessingStage, error: Exception):
        stage_names = {
            ProcessingStage.METADATA_EXTRACTION: "元数据提取",
            ProcessingStage.FULL_OCR: "全文OCR",
            ProcessingStage.STRUCTURE_PARSING: "结构化解析",
            ProcessingStage.REPORT_GENERATION: "报告生成"
        }
        
        stage_name = stage_names.get(stage, "未知阶段")
        print(f"\n❌ {paper_name} - {stage_name}阶段错误: {error}")
    
    return error_callback


async def test_single_paper(pdf_path: str, output_base_dir: str = "aer_quick_test"):
    """测试单个论文"""
    paper_name = Path(pdf_path).stem
    
    print(f"\n🚀 开始处理: {paper_name}")
    
    # 配置流水线 - 现在使用统一的LLM配置系统
    config = PipelineConfig(
        output_dir=output_base_dir,
        # api_name=None,  # 使用默认API配置，或者指定如 "deepseek", "wd_gemini2" 等
        llm_config={
            "max_tokens": 100000  # 其他配置会从llm_config.py自动加载
        },
        keep_intermediate_files=True,  # 保留文件便于检查
        max_retry_attempts=2
    )
    
    start_time = time.time()
    
    try:
        # 调用流水线
        result = await process_paper_pipeline(
            pdf_path=pdf_path,
            config=config,
            progress_callback=create_progress_callback(paper_name),
            error_callback=create_error_callback(paper_name)
        )
        
        processing_time = time.time() - start_time
        
        print(f"\n{'✅' if result.success else '❌'} 处理{'成功' if result.success else '失败'} - 耗时: {processing_time:.2f}秒")
        
        if result.success:
            print(f"📄 最终报告: {result.final_report_path}")
            print(f"📋 元数据: {result.metadata_path}")
            print(f"🏗️  结构文件: {result.structure_path}")
        else:
            print(f"❌ 错误信息: {result.pipeline_error}")
            
            # 显示失败的阶段
            failed_stages = result.get_failed_stages()
            if failed_stages:
                stage_names = {
                    ProcessingStage.METADATA_EXTRACTION: "元数据提取",
                    ProcessingStage.FULL_OCR: "全文OCR",
                    ProcessingStage.STRUCTURE_PARSING: "结构化解析",
                    ProcessingStage.REPORT_GENERATION: "报告生成"
                }
                failed_names = [stage_names.get(s, s.value) for s in failed_stages]
                print(f"💥 失败阶段: {', '.join(failed_names)}")
        
        # 显示各阶段详情
        print(f"\n📊 各阶段详情:")
        stage_names = {
            ProcessingStage.METADATA_EXTRACTION: "元数据提取",
            ProcessingStage.FULL_OCR: "全文OCR",
            ProcessingStage.STRUCTURE_PARSING: "结构化解析",
            ProcessingStage.REPORT_GENERATION: "报告生成"
        }
        
        for stage, stage_result in result.stages.items():
            status_icon = "✅" if stage_result.success else "❌"
            stage_name = stage_names.get(stage, stage.value)
            print(f"   {status_icon} {stage_name}: {stage_result.processing_time:.2f}秒")
            
            if stage_result.error_message:
                print(f"      错误: {stage_result.error_message}")
        
        return result
        
    except Exception as e:
        print(f"\n💥 处理异常: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_folder(folder_path: str, max_papers: int = 3):
    """测试文件夹中的论文"""
    print("🚀 AER论文快速测试")
    print("=" * 60)
    
    if not os.path.exists(folder_path):
        print(f"❌ 文件夹不存在: {folder_path}")
        return
    
    # 查找PDF文件
    pdf_files = []
    for file in os.listdir(folder_path):
        if file.lower().endswith('.pdf'):
            pdf_path = os.path.join(folder_path, file)
            pdf_files.append(pdf_path)
    
    if not pdf_files:
        print(f"❌ 在 {folder_path} 中未找到PDF文件")
        return
    
    # 限制测试数量
    if len(pdf_files) > max_papers:
        pdf_files = pdf_files[:max_papers]
        print(f"📋 限制测试前 {max_papers} 篇论文")
    
    print(f"📚 找到 {len(pdf_files)} 篇论文")
    print(f"📁 输出目录: aer_quick_test")
    
    results = []
    successful = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n{'='*20} 论文 {i}/{len(pdf_files)} {'='*20}")
        
        result = await test_single_paper(pdf_path)
        if result:
            results.append(result)
            if result.success:
                successful += 1
        
        # 短暂休息
        if i < len(pdf_files):
            print(f"\n⏸️  休息2秒...")
            await asyncio.sleep(2)
    
    # 汇总结果
    print(f"\n" + "=" * 60)
    print(f"📊 测试汇总")
    print(f"=" * 60)
    print(f"📚 总论文数: {len(pdf_files)}")
    print(f"✅ 成功处理: {successful}")
    print(f"❌ 处理失败: {len(pdf_files) - successful}")
    print(f"📈 成功率: {(successful/len(pdf_files)*100):.1f}%")
    
    if successful > 0:
        print(f"\n🎉 测试成功！流水线工作正常。")
        print(f"💡 你可以查看 aer_quick_test/ 目录下的输出文件。")
    else:
        print(f"\n⚠️ 所有论文处理都失败了，请检查配置和依赖。")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AER论文快速测试脚本")
    parser.add_argument("folder_path", help="AER202507文件夹路径")
    parser.add_argument("--max-papers", type=int, default=3, help="最大测试论文数量（默认3篇）")
    
    args = parser.parse_args()
    
    print("🔧 Claude 4.0 Opus AER论文快速测试")
    print("📦 四阶段流水线测试")
    print(f"📁 测试文件夹: {args.folder_path}")
    print(f"📊 最大测试数量: {args.max_papers}")
    print()
    
    # 设置日志级别
    import logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    asyncio.run(test_folder(args.folder_path, args.max_papers))


if __name__ == "__main__":
    main()
