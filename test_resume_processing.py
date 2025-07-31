#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试断点续传功能

这个脚本用于测试修复后的系统是否能正常工作，特别是断点续传功能

作者: Claude 4.0 Opus
创建时间: 2025-01-29
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def test_single_paper():
    """测试单个论文的处理"""
    print("=" * 60)
    print("测试单个论文处理（带断点续传）")
    print("=" * 60)
    
    # 选择一个已经部分处理的论文（已完成阶段1和2）
    test_pdf = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/fszRA/policy_paper_extract/罗斯福新政影响相关文献/Fleck - 1999 - The Marginal Effect of New Deal Relief Work on County-Level Unemployment Statistics.pdf"
    output_dir = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/fsz_ra_papers"
    
    if not Path(test_pdf).exists():
        print(f"❌ 测试PDF文件不存在: {test_pdf}")
        return False
    
    try:
        from tools.paper_processing_service import process_paper_pipeline
        from tools.pipeline_models import PipelineConfig
        
        # 创建配置
        config = PipelineConfig(
            output_dir=output_dir,
            template_paths={
                "metadata": "resources/extract_metadata_from_face_page.md",
                "paper_type_classify": "resources/paper_type_classify.md", 
                "extract_attribute_tree_empirical": "resources/extract_attribute_tree_empirical.md",
                "extract_attribute_tree_structural": "resources/extract_attribute_tree_structural.md"
            }
        )
        
        def progress_callback(progress_info):
            stage_name = progress_info.current_stage.value
            stage_progress = progress_info.stage_progress * 100
            overall_progress = progress_info.overall_progress * 100
            print(f"[{stage_name}] {stage_progress:.1f}% | 总体: {overall_progress:.1f}% | {progress_info.message}")
        
        def error_callback(stage, error):
            print(f"❌ 阶段 {stage.value} 错误: {error}")
        
        async def run_test():
            result = await process_paper_pipeline(
                pdf_path=test_pdf,
                config=config,
                progress_callback=progress_callback,
                error_callback=error_callback
            )
            
            print(f"\n处理结果:")
            print(f"状态: {result.overall_status.value}")
            print(f"处理时间: {result.total_processing_time:.2f}秒")
            
            if result.success:
                print("✅ 处理成功!")
                print(f"输出目录: {result.output_dir}")
                if result.final_report_path:
                    print(f"最终报告: {result.final_report_path}")
            else:
                print("❌ 处理失败!")
                if result.pipeline_error:
                    print(f"错误: {result.pipeline_error}")
            
            return result.success
        
        return asyncio.run(run_test())
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_resume_capability():
    """检查断点续传能力"""
    print("\n" + "=" * 60)
    print("检查断点续传能力")
    print("=" * 60)
    
    # 检查已处理的论文文件夹
    output_base = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/fsz_ra_papers"
    
    if not Path(output_base).exists():
        print("❌ 输出目录不存在")
        return False
    
    paper_dirs = [d for d in Path(output_base).iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    print(f"找到 {len(paper_dirs)} 个论文处理目录:")
    
    for paper_dir in paper_dirs:
        print(f"\n📁 {paper_dir.name}")
        
        # 检查各阶段文件
        stages_status = {
            "阶段1-元数据": False,
            "阶段2-全文OCR": False, 
            "阶段3-结构解析": False,
            "阶段4-报告生成": False
        }
        
        # 阶段1检查
        metadata_file = paper_dir / f"{paper_dir.name}_metadata.json"
        first_pages_file = paper_dir / f"{paper_dir.name}_first_three_pages.md"
        if metadata_file.exists() and first_pages_file.exists():
            stages_status["阶段1-元数据"] = True
        
        # 阶段2检查
        complete_md = paper_dir / "complete.md"
        if complete_md.exists():
            stages_status["阶段2-全文OCR"] = True
        
        # 阶段3检查
        structure_file = paper_dir / "paper_structure.json"
        attribute_tree_file = paper_dir / f"{paper_dir.name}_attribute_tree.json"
        if structure_file.exists() and attribute_tree_file.exists():
            stages_status["阶段3-结构解析"] = True
        
        # 阶段4检查
        possible_reports = [
            paper_dir / "final_report.md",
            paper_dir / "report.md",
            paper_dir / f"{paper_dir.name}_report.md"
        ]
        if any(f.exists() for f in possible_reports):
            stages_status["阶段4-报告生成"] = True
        
        # 显示状态
        for stage, completed in stages_status.items():
            status = "✅" if completed else "❌"
            print(f"   {status} {stage}")
    
    return True

def main():
    """主函数"""
    print("断点续传功能测试")
    
    # 检查断点续传能力
    check_resume_capability()
    
    # 测试单个论文处理
    print("\n自动测试单个论文处理...")
    success = test_single_paper()
    if success:
        print("\n✅ 测试成功！系统可以正常工作")
    else:
        print("\n❌ 测试失败！请检查错误信息")

if __name__ == "__main__":
    main()
