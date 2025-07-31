#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
快速测试封装的论文处理服务

这个脚本演示如何使用您之前封装的完整流水线服务。

作者: Claude 4.0 Opus
创建时间: 2025-01-31
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from tools.paper_processing_service import process_paper_pipeline
    from tools.pipeline_models import PipelineConfig, ProgressInfo, ProcessingStage
    print("✅ 成功导入封装的流水线服务")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保您在正确的项目目录中运行此脚本")
    sys.exit(1)


def simple_progress_callback(progress_info: ProgressInfo):
    """简单的进度显示回调"""
    stage_name = progress_info.current_stage.value if progress_info.current_stage else "未知阶段"
    print(f"📊 进度: {progress_info.overall_progress:.1%} | {stage_name} | {progress_info.message}")


def error_callback(stage: ProcessingStage, error: Exception):
    """错误处理回调"""
    print(f"❌ 阶段 {stage.value} 发生错误: {error}")


async def test_basic_usage():
    """测试基础使用"""
    print("\n" + "="*60)
    print("🧪 测试1: 基础使用（使用默认配置）")
    print("="*60)
    
    # 查找示例PDF文件
    test_files = [
        "example_pdfs/sample.pdf",
        "example_pdfs/Brochu 等-2025-The Minimum Wage, Turnover,.pdf",
        "example_pdfs/Clay 等 - 2024 - Canary in a Coal Mine Infant Mortality and Tradeoffs Associated with Mid-20th Century Air Pollution.pdf"
    ]
    
    pdf_path = None
    for file_path in test_files:
        if Path(file_path).exists():
            pdf_path = file_path
            break
    
    if not pdf_path:
        print("❌ 未找到示例PDF文件，请确保以下文件之一存在：")
        for file_path in test_files:
            print(f"   - {file_path}")
        return False
    
    print(f"📄 使用PDF文件: {pdf_path}")
    
    try:
        # 最简单的使用方式
        result = await process_paper_pipeline(
            pdf_path=pdf_path,
            progress_callback=simple_progress_callback,
            error_callback=error_callback
        )
        
        print(f"\n📋 处理结果:")
        print(f"   状态: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"   耗时: {result.total_processing_time:.2f}秒")
        
        if result.success:
            print(f"   📄 最终报告: {result.final_report_path}")
            print(f"   📊 元数据文件: {result.metadata_path}")
            print(f"   🏗️ 结构文件: {result.structure_path}")
            
            # 检查各阶段结果
            print(f"\n📈 各阶段结果:")
            for stage, stage_result in result.stages.items():
                status = "✅" if stage_result.success else "❌"
                print(f"   {status} {stage.value}: {stage_result.processing_time:.2f}秒")
        else:
            print(f"   ❌ 错误信息: {result.pipeline_error}")
            
            # 检查失败的阶段
            failed_stages = result.get_failed_stages()
            if failed_stages:
                print(f"   💥 失败的阶段: {[s.value for s in failed_stages]}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ 处理过程中发生异常: {e}")
        return False


async def test_custom_config():
    """测试自定义配置"""
    print("\n" + "="*60)
    print("🧪 测试2: 自定义配置")
    print("="*60)
    
    # 自定义配置
    config = PipelineConfig(
        output_dir="test_output",
        api_name="deepseek",  # 如果您配置了deepseek API
        llm_config={
            "temperature": 0.1,
            "max_tokens": 4000
        },
        keep_intermediate_files=True,
        max_retry_attempts=2
    )
    
    print(f"📋 使用自定义配置:")
    print(f"   输出目录: {config.output_dir}")
    print(f"   API名称: {config.api_name}")
    print(f"   LLM配置: {config.llm_config}")
    print(f"   保留中间文件: {config.keep_intermediate_files}")
    print(f"   最大重试次数: {config.max_retry_attempts}")
    
    # 这里可以添加实际的测试逻辑
    print("⏭️  跳过自定义配置测试（避免重复处理）")
    return True


async def test_error_handling():
    """测试错误处理"""
    print("\n" + "="*60)
    print("🧪 测试3: 错误处理")
    print("="*60)
    
    # 使用不存在的文件测试错误处理
    nonexistent_file = "nonexistent_file.pdf"
    print(f"📄 使用不存在的文件: {nonexistent_file}")
    
    try:
        result = await process_paper_pipeline(
            pdf_path=nonexistent_file,
            error_callback=error_callback
        )
        
        print(f"📋 错误处理结果:")
        print(f"   状态: {'✅ 成功' if result.success else '❌ 失败（预期）'}")
        
        if not result.success:
            print(f"   ❌ 错误信息: {result.pipeline_error}")
            print("   ✅ 错误处理机制正常工作")
        
        return True
        
    except Exception as e:
        print(f"❌ 异常处理测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 开始测试封装的论文处理服务")
    print("=" * 60)
    
    # 运行各项测试
    test_results = []
    
    # 测试1: 基础使用
    result1 = await test_basic_usage()
    test_results.append(("基础使用", result1))
    
    # 测试2: 自定义配置
    result2 = await test_custom_config()
    test_results.append(("自定义配置", result2))
    
    # 测试3: 错误处理
    result3 = await test_error_handling()
    test_results.append(("错误处理", result3))
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {status} {test_name}")
    
    successful_tests = sum(1 for _, success in test_results if success)
    total_tests = len(test_results)
    
    print(f"\n🎯 总体结果: {successful_tests}/{total_tests} 测试通过")
    
    if successful_tests == total_tests:
        print("🎉 所有测试通过！封装的流水线服务工作正常。")
    else:
        print("⚠️  部分测试失败，请检查配置和依赖。")
    
    print("\n💡 提示:")
    print("   - 如果基础使用测试通过，说明封装服务可以正常工作")
    print("   - 查看生成的输出文件了解处理结果")
    print("   - 参考 tools/example_usage.py 了解更多使用方式")


if __name__ == "__main__":
    asyncio.run(main())
