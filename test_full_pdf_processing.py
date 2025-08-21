#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
完整PDF处理测试

确保处理完整的PDF文件，而不是只处理前3页

作者: Claude 4.0 Opus
创建时间: 2025-08-05
"""

import asyncio
import sys
import os
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


async def test_complete_pdf_processing():
    """测试完整PDF处理"""
    print("🧪 测试: 完整PDF处理（确保处理所有页面）")
    print("=" * 80)
    
    # 用户提供的PDF文件路径
    pdf_path = r"C:\Users\Bru\Desktop\Paper\attention_paper.pdf"
    
    # 检查文件是否存在
    if not Path(pdf_path).exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return False
    
    print(f"📄 使用PDF文件: {pdf_path}")
    print(f"📁 文件大小: {Path(pdf_path).stat().st_size / 1024 / 1024:.2f} MB")
    
    # 确保输出目录是全新的
    output_dir = "output_complete"
    if Path(output_dir).exists():
        import shutil
        shutil.rmtree(output_dir)
        print(f"🗑️ 已清理旧的输出目录: {output_dir}")
    
    # 配置处理参数
    config = PipelineConfig(
        output_dir=output_dir,
        api_name="wd_gemini2",  # 使用稳定的API
        llm_config={
            "temperature": 0.3,
            "max_tokens": 8000
        },
        keep_intermediate_files=True,  # 保留中间文件便于调试
        max_retry_attempts=3
    )
    
    print(f"📋 处理配置:")
    print(f"   输出目录: {config.output_dir}")
    print(f"   API名称: {config.api_name}")
    print(f"   保留中间文件: {config.keep_intermediate_files}")
    print()
    
    try:
        print("🚀 开始完整PDF处理...")
        print("⚠️  注意：这次将处理完整的PDF，而不是只处理前3页")
        print()
        
        result = await process_paper_pipeline(
            pdf_path=pdf_path,
            config=config,
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
            
            # 检查完整文档的长度
            complete_md_path = Path(config.output_dir) / "attention_paper" / "complete.md"
            if complete_md_path.exists():
                with open(complete_md_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                print(f"\n📏 完整文档统计:")
                print(f"   总行数: {len(lines)}")
                print(f"   文件大小: {complete_md_path.stat().st_size / 1024:.2f} KB")
                
                # 检查是否包含更多内容
                content = ''.join(lines)
                if len(content) > 10000:  # 如果内容超过10KB，说明处理了更多内容
                    print(f"   ✅ 文档内容丰富，似乎处理了完整PDF")
                else:
                    print(f"   ⚠️ 文档内容较少，可能只处理了部分内容")
                
                # 显示文档的最后几行来验证
                print(f"\n📖 文档末尾内容预览:")
                for i, line in enumerate(lines[-5:], len(lines)-4):
                    print(f"   {i:3d}: {line.rstrip()}")
            
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


async def verify_processing_quality():
    """验证处理质量"""
    print("\n🔍 验证处理质量")
    print("=" * 80)
    
    output_dir = Path("output_complete/attention_paper")
    
    if not output_dir.exists():
        print("❌ 输出目录不存在，无法验证")
        return False
    
    # 检查关键文件
    key_files = [
        ("complete.md", "完整文档"),
        ("report_output.md", "分析报告"),
        ("metadata_attention_paper.json", "元数据"),
        ("structure_attention_paper.json", "结构数据")
    ]
    
    print("📋 文件检查:")
    all_files_exist = True
    
    for filename, description in key_files:
        file_path = output_dir / filename
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"   ✅ {description}: {filename} ({size_kb:.2f} KB)")
        else:
            print(f"   ❌ {description}: {filename} (缺失)")
            all_files_exist = False
    
    # 特别检查完整文档的质量
    complete_md_path = output_dir / "complete.md"
    if complete_md_path.exists():
        with open(complete_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n📊 完整文档质量分析:")
        print(f"   字符总数: {len(content):,}")
        print(f"   行数: {content.count(chr(10)) + 1:,}")
        
        # 检查是否包含论文的关键部分
        key_sections = [
            "Abstract",
            "Introduction", 
            "Model Architecture",
            "Attention",
            "Experiments",
            "Results",
            "Conclusion"
        ]
        
        found_sections = []
        for section in key_sections:
            if section.lower() in content.lower():
                found_sections.append(section)
        
        print(f"   找到的关键章节: {len(found_sections)}/{len(key_sections)}")
        for section in found_sections:
            print(f"     ✅ {section}")
        
        missing_sections = [s for s in key_sections if s not in found_sections]
        if missing_sections:
            print(f"   缺失的章节:")
            for section in missing_sections:
                print(f"     ❌ {section}")
        
        # 估算是否为完整论文
        if len(content) > 50000 and len(found_sections) >= 4:
            print(f"   🎉 看起来是完整的论文内容！")
            return True
        else:
            print(f"   ⚠️ 内容可能不完整")
            return False
    
    return all_files_exist


async def main():
    """主测试函数"""
    print("🚀 开始完整PDF处理测试")
    print("=" * 100)
    print("🎯 目标: 确保处理完整的PDF文件，而不是只处理前3页")
    print("📄 测试文件: attention_paper.pdf")
    print("=" * 100)
    
    # 测试完整处理
    success = await test_complete_pdf_processing()
    
    if success:
        # 验证处理质量
        quality_ok = await verify_processing_quality()
        
        print("\n" + "="*100)
        print("📊 最终结果")
        print("="*100)
        
        if quality_ok:
            print("🎉 完整PDF处理测试成功！")
            print("✅ 生成了完整的论文内容")
            print("✅ 包含了论文的主要章节")
            print("✅ 文档质量良好")
            print("\n💡 您现在可以:")
            print("   1. 查看 output_complete/attention_paper/complete.md 获取完整文本")
            print("   2. 查看 output_complete/attention_paper/report_output.md 获取详细分析")
            print("   3. 使用这个配置处理其他PDF文件")
        else:
            print("⚠️ 处理完成但质量可能有问题")
            print("   请检查生成的文件内容")
    else:
        print("\n" + "="*100)
        print("❌ 完整PDF处理测试失败")
        print("="*100)
        print("请检查错误信息并重试")
    
    print("="*100)


if __name__ == "__main__":
    asyncio.run(main())
