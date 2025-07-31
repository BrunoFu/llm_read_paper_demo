#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单的断点续传测试

测试断点续传功能是否正常工作

作者: Claude 4.0 Opus
创建时间: 2025-01-29
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def test_stage_check():
    """测试阶段检查功能"""
    print("=" * 60)
    print("测试阶段检查功能")
    print("=" * 60)
    
    try:
        from tools.paper_processing_service import PaperProcessingService
        from tools.pipeline_models import PipelineConfig, ProcessingStage
        
        # 创建服务实例
        config = PipelineConfig()
        service = PaperProcessingService(config)
        
        # 测试已完成阶段1和2的论文
        output_dir = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/fsz_ra_papers/Fleck - 1999 - The Marginal Effect of New Deal Relief Work on County-Level Unemployment Statistics"
        paper_name = "Fleck - 1999 - The Marginal Effect of New Deal Relief Work on County-Level Unemployment Statistics"
        
        if not Path(output_dir).exists():
            print(f"❌ 测试目录不存在: {output_dir}")
            return False
        
        # 测试各阶段检查
        stages_to_test = [
            ProcessingStage.METADATA_EXTRACTION,
            ProcessingStage.FULL_OCR,
            ProcessingStage.STRUCTURE_PARSING,
            ProcessingStage.REPORT_GENERATION
        ]
        
        print(f"测试论文: {paper_name}")
        print(f"输出目录: {output_dir}")
        print()
        
        for stage in stages_to_test:
            completed = service._check_stage_completed(stage, output_dir, paper_name)
            status = "✅ 已完成" if completed else "❌ 未完成"
            print(f"{stage.value}: {status}")
            
            # 显示检查的文件
            if stage == ProcessingStage.METADATA_EXTRACTION:
                files = [
                    f"{paper_name}_metadata.json",
                    f"{paper_name}_first_three_pages.md"
                ]
            elif stage == ProcessingStage.FULL_OCR:
                files = ["complete.md"]
            elif stage == ProcessingStage.STRUCTURE_PARSING:
                files = [
                    "paper_structure.json",
                    f"{paper_name}_attribute_tree.json"
                ]
            elif stage == ProcessingStage.REPORT_GENERATION:
                files = [
                    "final_report.md",
                    "report.md", 
                    f"{paper_name}_report.md"
                ]
            
            for file in files:
                file_path = os.path.join(output_dir, file)
                exists = os.path.exists(file_path)
                file_status = "✓" if exists else "✗"
                print(f"  {file_status} {file}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("简单断点续传测试")
    
    success = test_stage_check()
    
    if success:
        print("✅ 阶段检查功能正常工作")
    else:
        print("❌ 阶段检查功能有问题")

if __name__ == "__main__":
    main()
