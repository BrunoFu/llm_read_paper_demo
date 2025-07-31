#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
罗斯福新政文献处理系统简单测试脚本

这个脚本用于快速测试系统是否可以正常工作

作者: Claude 4.0 Opus
创建时间: 2025-01-29
"""

import os
import sys
from pathlib import Path

def test_basic_imports():
    """测试基本导入"""
    print("测试基本导入...")
    
    try:
        import asyncio
        print("✅ asyncio")
    except ImportError:
        print("❌ asyncio")
        return False
    
    try:
        import json
        print("✅ json")
    except ImportError:
        print("❌ json")
        return False
    
    try:
        from datetime import datetime
        print("✅ datetime")
    except ImportError:
        print("❌ datetime")
        return False
    
    return True

def test_directories():
    """测试目录结构"""
    print("\n测试目录结构...")
    
    required_dirs = [
        "tools",
        "utils", 
        "logs"
    ]
    
    all_good = True
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ (缺失)")
            if dir_name == "logs":
                # 创建logs目录
                Path(dir_name).mkdir(exist_ok=True)
                print(f"   已创建 {dir_name}/ 目录")
            else:
                all_good = False
    
    return all_good

def test_input_output_paths():
    """测试输入输出路径"""
    print("\n测试输入输出路径...")
    
    input_dir = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/fszRA/policy_paper_extract/罗斯福新政影响相关文献"
    output_dir = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/fsz_ra_papers"
    
    # 测试输入目录
    if Path(input_dir).exists():
        print(f"✅ 输入目录存在")
        
        # 查找PDF文件
        pdf_files = list(Path(input_dir).rglob("*.pdf")) + list(Path(input_dir).rglob("*.PDF"))
        print(f"   找到 {len(pdf_files)} 个PDF文件")
        
        if pdf_files:
            print("   PDF文件列表:")
            for i, pdf_file in enumerate(pdf_files[:3], 1):
                print(f"   {i}. {pdf_file.name}")
            if len(pdf_files) > 3:
                print(f"   ... 还有 {len(pdf_files) - 3} 个文件")
        else:
            print("   ⚠️  未找到PDF文件")
            return False
    else:
        print(f"❌ 输入目录不存在: {input_dir}")
        return False
    
    # 测试输出目录
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        print(f"✅ 输出目录可用: {output_dir}")
    except Exception as e:
        print(f"❌ 输出目录创建失败: {e}")
        return False
    
    return True

def test_key_files():
    """测试关键文件"""
    print("\n测试关键文件...")
    
    key_files = [
        "tools/batch_process_fsz_papers.py",
        "run_fsz_batch_processing.py",
        "utils/llm_config.py"
    ]
    
    all_good = True
    for file_path in key_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (缺失)")
            all_good = False
    
    return all_good

def main():
    """主测试函数"""
    print("=" * 60)
    print("罗斯福新政文献处理系统 - 快速测试")
    print("=" * 60)
    
    tests = [
        ("基本导入", test_basic_imports),
        ("目录结构", test_directories), 
        ("输入输出路径", test_input_output_paths),
        ("关键文件", test_key_files)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ 测试 {test_name} 时发生错误: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✅ 所有测试通过！")
        print("\n可以运行批量处理:")
        print("python run_fsz_batch_processing.py")
    else:
        print("❌ 部分测试失败，请检查上述问题")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
