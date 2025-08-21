#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复完整PDF处理问题

解决第一阶段和第二阶段都生成complete.md文件导致的冲突问题

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


def fix_stage1_complete_md_issue():
    """修复第一阶段生成complete.md文件的问题"""
    print("🔧 修复第一阶段complete.md文件冲突问题")
    print("=" * 60)
    
    # 修改第一阶段的process_pdf.py文件
    stage1_file = Path("crop_pdf_first_three_page/process_pdf.py")
    
    if not stage1_file.exists():
        print(f"❌ 文件不存在: {stage1_file}")
        return False
    
    # 读取文件内容
    with open(stage1_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否需要修复
    if 'complete.md' not in content:
        print("✅ 文件已经修复过了")
        return True
    
    # 替换complete.md为first_three_pages_complete.md
    old_line = '    complete_path = os.path.join(output_dir, "complete.md")'
    new_line = '    complete_path = os.path.join(output_dir, "first_three_pages_complete.md")'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        # 也更新打印信息
        content = content.replace(
            'print(f"已保存完整文档到 complete.md")',
            'print(f"已保存前三页文档到 first_three_pages_complete.md")'
        )
        
        # 写回文件
        with open(stage1_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 已修复第一阶段文件命名冲突")
        return True
    else:
        print("⚠️ 未找到需要修复的代码行")
        return False


async def test_fixed_processing():
    """测试修复后的处理流程"""
    print("\n🧪 测试修复后的完整PDF处理")
    print("=" * 60)
    
    from tools.paper_processing_service import process_paper_pipeline
    from tools.pipeline_models import PipelineConfig, ProgressInfo, ProcessingStage
    
    def progress_callback(progress_info: ProgressInfo):
        """进度显示回调"""
        stage_name = progress_info.current_stage.value if progress_info.current_stage else "未知阶段"
        print(f"📊 进度: {progress_info.overall_progress:.1%} | {stage_name} | {progress_info.message}")

    def error_callback(stage: ProcessingStage, error: Exception):
        """错误处理回调"""
        print(f"❌ 阶段 {stage.value} 发生错误: {error}")
    
    # 用户提供的PDF文件路径
    pdf_path = r"C:\Users\Bru\Desktop\Paper\attention_paper.pdf"
    
    # 检查文件是否存在
    if not Path(pdf_path).exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return False
    
    print(f"📄 使用PDF文件: {pdf_path}")
    
    # 确保输出目录是全新的
    output_dir = "output_fixed"
    if Path(output_dir).exists():
        import shutil
        shutil.rmtree(output_dir)
        print(f"🗑️ 已清理输出目录: {output_dir}")
    
    # 配置处理参数
    config = PipelineConfig(
        output_dir=output_dir,
        api_name="wd_gemini2",
        llm_config={
            "temperature": 0.3,
            "max_tokens": 8000
        },
        keep_intermediate_files=True,
        max_retry_attempts=3
    )
    
    print(f"📋 处理配置:")
    print(f"   输出目录: {config.output_dir}")
    print(f"   API名称: {config.api_name}")
    print()
    
    try:
        print("🚀 开始修复后的完整PDF处理...")
        
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
            # 检查生成的文件
            attention_dir = Path(config.output_dir) / "attention_paper"
            
            # 检查第一阶段文件
            first_three_complete = attention_dir / "first_three_pages_complete.md"
            if first_three_complete.exists():
                with open(first_three_complete, 'r', encoding='utf-8') as f:
                    first_lines = len(f.readlines())
                print(f"   📄 第一阶段文件: first_three_pages_complete.md ({first_lines} 行)")
            
            # 检查第二阶段文件
            complete_md = attention_dir / "complete.md"
            if complete_md.exists():
                with open(complete_md, 'r', encoding='utf-8') as f:
                    complete_lines = len(f.readlines())
                print(f"   📄 第二阶段文件: complete.md ({complete_lines} 行)")
                
                if complete_lines > first_lines:
                    print(f"   ✅ 第二阶段成功处理了更多内容！")
                else:
                    print(f"   ⚠️ 第二阶段可能仍有问题")
            else:
                print(f"   ❌ 第二阶段文件不存在")
            
            print(f"\n📈 各阶段详情:")
            for stage, stage_result in result.stages.items():
                status = "✅" if stage_result.success else "❌"
                print(f"   {status} {stage.value}: {stage_result.processing_time:.2f}秒")
        
        return result.success
        
    except Exception as e:
        print(f"❌ 处理过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("🛠️ 修复完整PDF处理问题")
    print("=" * 80)
    print("🎯 目标: 解决第一阶段和第二阶段文件命名冲突")
    print("=" * 80)
    
    # 步骤1: 修复第一阶段文件命名问题
    fix_success = fix_stage1_complete_md_issue()
    
    if fix_success:
        # 步骤2: 测试修复后的处理流程
        test_success = await test_fixed_processing()
        
        print("\n" + "="*80)
        print("📊 修复结果")
        print("="*80)
        
        if test_success:
            print("🎉 修复成功！现在可以正确处理完整PDF了")
            print("✅ 第一阶段生成: first_three_pages_complete.md")
            print("✅ 第二阶段生成: complete.md (完整内容)")
            print("✅ 避免了文件命名冲突")
        else:
            print("⚠️ 修复后测试失败，可能还有其他问题")
    else:
        print("\n❌ 修复失败，无法继续测试")
    
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
