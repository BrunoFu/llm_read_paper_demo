#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
论文处理流水线使用示例

这个文件展示了如何使用封装好的四阶段流水线服务。

作者: Claude 4.0 Opus
创建时间: 2025-01-27
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.paper_processing_service import process_paper_pipeline
from tools.pipeline_models import PipelineConfig, ProgressInfo, ProcessingStage


def simple_progress_callback(progress_info: ProgressInfo):
    """简单的进度显示"""
    print(f"进度: {progress_info.overall_progress:.1%} - {progress_info.message}")


async def basic_usage_example():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    # 最简单的使用方式
    pdf_path = "example_pdfs/sample.pdf"  # 替换为你的PDF路径
    
    if not Path(pdf_path).exists():
        print(f"PDF文件不存在: {pdf_path}")
        return
    
    try:
        result = await process_paper_pipeline(pdf_path)
        
        if result.success:
            print(f"✅ 处理成功！")
            print(f"📄 最终报告: {result.final_report_path}")
        else:
            print(f"❌ 处理失败: {result.pipeline_error}")
            
    except Exception as e:
        print(f"处理过程中发生错误: {e}")


async def advanced_usage_example():
    """高级使用示例"""
    print("\n=== 高级使用示例 ===")
    
    # 自定义配置
    config = PipelineConfig(
        output_dir="my_custom_output",
        api_name="deepseek",  # 指定API
        llm_config={
            "temperature": 0.1,  # 更低的温度，更确定的输出
            "max_tokens": 6000   # 更多的token
        },
        keep_intermediate_files=True,  # 保留中间文件
        max_retry_attempts=2  # 重试次数
    )
    
    pdf_path = "example_pdfs/sample.pdf"  # 替换为你的PDF路径
    
    if not Path(pdf_path).exists():
        print(f"PDF文件不存在: {pdf_path}")
        return
    
    try:
        result = await process_paper_pipeline(
            pdf_path=pdf_path,
            config=config,
            progress_callback=simple_progress_callback
        )
        
        print(f"\n处理结果:")
        print(f"状态: {result.overall_status.value}")
        print(f"耗时: {result.total_processing_time:.2f}秒")
        
        # 检查各阶段结果
        for stage, stage_result in result.stages.items():
            print(f"{stage.value}: {'成功' if stage_result.success else '失败'}")
            
    except Exception as e:
        print(f"处理过程中发生错误: {e}")


async def batch_processing_example():
    """批量处理示例"""
    print("\n=== 批量处理示例 ===")
    
    pdf_files = [
        "example_pdfs/paper1.pdf",
        "example_pdfs/paper2.pdf",
        "example_pdfs/paper3.pdf"
    ]
    
    config = PipelineConfig(
        output_dir="batch_output",
        api_name="deepseek"
    )
    
    results = []
    
    for pdf_path in pdf_files:
        if not Path(pdf_path).exists():
            print(f"跳过不存在的文件: {pdf_path}")
            continue
            
        print(f"\n处理文件: {pdf_path}")
        
        try:
            result = await process_paper_pipeline(
                pdf_path=pdf_path,
                config=config,
                progress_callback=simple_progress_callback
            )
            results.append(result)
            
            if result.success:
                print(f"✅ {Path(pdf_path).name} 处理成功")
            else:
                print(f"❌ {Path(pdf_path).name} 处理失败")
                
        except Exception as e:
            print(f"❌ {Path(pdf_path).name} 处理异常: {e}")
    
    # 汇总结果
    successful = sum(1 for r in results if r.success)
    total = len(results)
    print(f"\n批量处理完成: {successful}/{total} 成功")


async def error_handling_example():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    def error_callback(stage: ProcessingStage, error: Exception):
        print(f"阶段 {stage.value} 发生错误: {error}")
        # 这里可以添加错误日志记录、通知等逻辑
    
    pdf_path = "nonexistent.pdf"  # 故意使用不存在的文件
    
    try:
        result = await process_paper_pipeline(
            pdf_path=pdf_path,
            error_callback=error_callback
        )
        
        if not result.success:
            print(f"处理失败，错误信息: {result.pipeline_error}")
            
            # 检查具体哪个阶段失败了
            failed_stages = result.get_failed_stages()
            if failed_stages:
                print(f"失败的阶段: {[s.value for s in failed_stages]}")
                
    except Exception as e:
        print(f"捕获到异常: {e}")


async def main():
    """主函数"""
    print("论文处理流水线使用示例")
    print("=" * 50)
    
    # 运行各种示例
    await basic_usage_example()
    await advanced_usage_example()
    await batch_processing_example()
    await error_handling_example()
    
    print("\n🎉 所有示例运行完成！")


if __name__ == "__main__":
    asyncio.run(main())
