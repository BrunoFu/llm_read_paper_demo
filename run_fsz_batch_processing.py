#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
罗斯福新政文献批量处理启动脚本

这个脚本是批量处理的简化启动入口，会自动运行完整的四阶段流程。

使用方法:
python run_fsz_batch_processing.py

作者: Claude 4.0 Opus
创建时间: 2025-01-29
"""

import os
import sys
import asyncio
from pathlib import Path

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    print("=" * 80)
    print("罗斯福新政相关文献批量处理系统")
    print("=" * 80)
    print("系统将运行完整的四阶段处理流程：")
    print("1. 阶段1：元数据提取")
    print("2. 阶段2：全文OCR") 
    print("3. 阶段3：结构化解析")
    print("4. 阶段4：报告生成")
    print("=" * 80)
    
    # 配置路径
    input_dir = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/fszRA/policy_paper_extract/罗斯福新政影响相关文献"
    output_dir = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/fsz_ra_papers"
    
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print()
    
    # 检查输入目录是否存在
    if not Path(input_dir).exists():
        print(f"❌ 错误: 输入目录不存在: {input_dir}")
        print("请检查路径是否正确")
        return
    
    # 确认开始处理
    try:
        response = input("是否开始批量处理？(y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("取消处理")
            return
    except KeyboardInterrupt:
        print("\n取消处理")
        return
    
    print("\n开始批量处理...")
    
    try:
        # 导入并运行批量处理器
        from tools.batch_process_fsz_papers import FSZPaperBatchProcessor
        
        async def run_processing():
            processor = FSZPaperBatchProcessor(input_dir, output_dir)
            await processor.process_all_papers()
        
        # 运行异步处理
        asyncio.run(run_processing())
        
    except KeyboardInterrupt:
        print("\n\n用户中断处理")
    except Exception as e:
        print(f"\n❌ 处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n处理完成！")


if __name__ == "__main__":
    main()
