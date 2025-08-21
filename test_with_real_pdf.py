#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用真实PDF文件测试项目功能

这个脚本使用用户提供的PDF文件来测试完整的论文处理流水线

作者: Claude 4.0 Opus
创建时间: 2025-08-05
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.paper_processing_service import process_paper_pipeline
from tools.pipeline_models import PipelineConfig, ProgressInfo, ProcessingStage


def progress_callback(progress_info: ProgressInfo):
    """进度显示回调"""
    stage_name = progress_info.current_stage.value if progress_info.current_stage else "未知阶段"
    print(f"📊 进度: {progress_info.overall_progress:.1%} | {stage_name} | {progress_info.message}")


def error_callback(stage: ProcessingStage, error: Exception):
    """错误处理回调"""
    print(f"❌ 阶段 {stage.value} 发生错误: {error}")


async def test_basic_processing():
    """测试基础处理功能"""
    print("🧪 测试: 基础论文处理")
    print("=" * 60)
    
    # 用户提供的PDF文件路径
    pdf_path = r"C:\Users\Bru\Desktop\Paper\attention_paper.pdf"
    
    # 检查文件是否存在
    if not Path(pdf_path).exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return False
    
    print(f"📄 使用PDF文件: {pdf_path}")
    print(f"📁 文件大小: {Path(pdf_path).stat().st_size / 1024 / 1024:.2f} MB")

    # 🔧 修复：清理旧的输出目录以避免断点续传问题
    output_dir = "output"
    attention_paper_dir = Path(output_dir) / "attention_paper"
    if attention_paper_dir.exists():
        import shutil
        shutil.rmtree(attention_paper_dir)
        print(f"🗑️ 已清理旧的输出目录以确保完整处理")

    try:
        # 使用默认配置进行处理
        print("\n🚀 开始处理...")
        print("⚠️  注意：已清理旧文件，将处理完整PDF")
        result = await process_paper_pipeline(
            pdf_path=pdf_path,
            progress_callback=progress_callback,
            error_callback=error_callback
        )
        
        print(f"\n📋 处理结果:")
        print(f"   状态: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"   总耗时: {result.total_processing_time:.2f}秒")
        
        if result.success:
            print(f"\n📄 生成的文件:")
            if result.final_report_path:
                print(f"   📊 最终报告: {result.final_report_path}")
            if result.metadata_path:
                print(f"   📋 元数据文件: {result.metadata_path}")
            if result.structure_path:
                print(f"   🏗️ 结构文件: {result.structure_path}")
            
            print(f"\n📈 各阶段详情:")
            for stage, stage_result in result.stages.items():
                status = "✅" if stage_result.success else "❌"
                print(f"   {status} {stage.value}: {stage_result.processing_time:.2f}秒")
                if stage_result.output_files:
                    for file_path in stage_result.output_files:
                        print(f"      📁 {file_path}")
        else:
            print(f"   ❌ 错误信息: {result.pipeline_error}")
            
            # 检查失败的阶段
            failed_stages = result.get_failed_stages()
            if failed_stages:
                print(f"   💥 失败的阶段: {[s.value for s in failed_stages]}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ 处理过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_custom_config():
    """测试自定义配置"""
    print("\n🧪 测试: 自定义配置处理")
    print("=" * 60)
    
    pdf_path = r"C:\Users\Bru\Desktop\Paper\attention_paper.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return False
    
    # 自定义配置 - 使用更快的API和保留中间文件
    config = PipelineConfig(
        output_dir="attention_paper_output",
        api_name="wd_gemini2",  # 使用Gemini API
        llm_config={
            "temperature": 0.3,  # 更低的温度，更确定的输出
            "max_tokens": 8000   # 更多的token
        },
        keep_intermediate_files=True,  # 保留中间文件便于调试
        max_retry_attempts=3
    )
    
    print(f"📋 使用自定义配置:")
    print(f"   输出目录: {config.output_dir}")
    print(f"   API名称: {config.api_name}")
    print(f"   温度: {config.llm_config.get('temperature', 'default')}")
    print(f"   最大tokens: {config.llm_config.get('max_tokens', 'default')}")
    print(f"   保留中间文件: {config.keep_intermediate_files}")
    
    try:
        print("\n🚀 开始自定义配置处理...")
        result = await process_paper_pipeline(
            pdf_path=pdf_path,
            config=config,
            progress_callback=progress_callback,
            error_callback=error_callback
        )
        
        print(f"\n📋 自定义配置处理结果:")
        print(f"   状态: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"   总耗时: {result.total_processing_time:.2f}秒")
        
        if result.success:
            print(f"   📁 输出目录: {config.output_dir}")
            
            # 检查输出目录中的文件
            output_path = Path(config.output_dir)
            if output_path.exists():
                files = list(output_path.rglob("*"))
                print(f"   📄 生成了 {len(files)} 个文件")
                for file_path in files[:5]:  # 只显示前5个文件
                    print(f"      📁 {file_path.relative_to(output_path)}")
                if len(files) > 5:
                    print(f"      ... 还有 {len(files) - 5} 个文件")
        
        return result.success
        
    except Exception as e:
        print(f"❌ 自定义配置处理失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 开始使用真实PDF文件测试项目")
    print("=" * 80)
    print("📄 测试文件: attention_paper.pdf")
    print("🎯 目标: 验证完整的论文处理流水线")
    print("=" * 80)
    
    # 运行测试
    test_results = []
    
    # 测试1: 基础处理
    print("\n" + "🔥" * 20 + " 开始基础处理测试 " + "🔥" * 20)
    result1 = await test_basic_processing()
    test_results.append(("基础处理", result1))
    
    # 如果基础处理成功，再进行自定义配置测试
    if result1:
        print("\n" + "🔥" * 20 + " 开始自定义配置测试 " + "🔥" * 20)
        result2 = await test_custom_config()
        test_results.append(("自定义配置", result2))
    else:
        print("\n⏭️  跳过自定义配置测试（基础处理失败）")
        test_results.append(("自定义配置", False))
    
    # 汇总结果
    print("\n" + "="*80)
    print("📊 最终测试结果")
    print("="*80)
    
    for test_name, success in test_results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {status} {test_name}")
    
    successful_tests = sum(1 for _, success in test_results if success)
    total_tests = len(test_results)
    
    print(f"\n🎯 总体结果: {successful_tests}/{total_tests} 测试成功")
    
    if successful_tests > 0:
        print("🎉 项目可以正常处理PDF文件！")
        print("\n💡 生成的文件位置:")
        print("   - 默认输出: output/ 目录")
        print("   - 自定义输出: attention_paper_output/ 目录")
        print("\n📖 您可以查看生成的报告了解处理结果")
    else:
        print("⚠️  所有测试都失败了，请检查:")
        print("   1. PDF文件是否可以正常访问")
        print("   2. API配置是否正确")
        print("   3. 网络连接是否正常")
    
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
