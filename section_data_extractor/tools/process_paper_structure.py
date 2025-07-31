#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
处理论文结构的完整流程

该脚本集成了从提取标题行号到生成节内容的完整流程。

用法:
    python process_paper_structure.py input.json paper_content.md --output-dir ./output
"""

import os
import sys
import subprocess
import argparse
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

def run_script(script_path, args=None):
    """运行Python脚本"""
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    print(f"{Fore.CYAN}运行脚本: {os.path.basename(script_path)}")
    if args:
        print(f"  参数: {' '.join(args)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0:
        print(f"{Fore.RED}脚本执行失败，错误码: {result.returncode}")
        if result.stderr:
            print(f"{Fore.RED}错误信息: {result.stderr}")
        return False
    
    return True

def process_paper_structure(input_json_path, md_file_path, output_dir=None):
    """处理论文结构，从提取标题行号到生成节内容"""
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置输出目录
    if output_dir is None:
        output_dir = os.path.join(script_dir, "output")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 如果input_json_path不存在，则先提取论文结构
    if not os.path.exists(input_json_path):
        print(f"{Fore.YELLOW}未找到输入JSON文件: {input_json_path}")
        print(f"{Fore.YELLOW}将从Markdown文件中提取论文结构...")
        
        # 运行extract_paper_structure.py脚本
        extract_script_path = os.path.join(script_dir, "extract_paper_structure.py")
        extract_args = [
            "--markdown", md_file_path,
            "--output", input_json_path
        ]
        
        if not run_script(extract_script_path, extract_args):
            print(f"{Fore.RED}提取论文结构失败，无法继续处理")
            return False
    
    # 提取标题行号
    extract_title_lines_script = os.path.join(script_dir, "extract_title_lines.py")
    extract_title_args = [
        "--input", input_json_path,
        "--markdown", md_file_path,
        "--output", os.path.join(script_dir, "input_with_row_num.json")
    ]
    
    if not run_script(extract_title_lines_script, extract_title_args):
        print(f"{Fore.RED}提取标题行号失败，无法继续处理")
        return False
    
    # 验证标题行号
    verify_title_lines_script = os.path.join(script_dir, "verify_title_lines.py")
    verify_title_args = [
        "--input", os.path.join(script_dir, "input_with_row_num.json"),
        "--markdown", md_file_path
    ]
    
    if not run_script(verify_title_lines_script, verify_title_args):
        print(f"{Fore.YELLOW}验证标题行号有警告，但将继续处理")
    
    # 展平结构
    flatten_structure_script = os.path.join(script_dir, "flatten_structure.py")
    flatten_structure_args = [
        "--input", os.path.join(script_dir, "input_with_row_num.json"),
        "--output", os.path.join(script_dir, "flattened_structure.json")
    ]
    
    if not run_script(flatten_structure_script, flatten_structure_args):
        print(f"{Fore.RED}展平结构失败，无法继续处理")
        return False
    
    # 添加文本内容
    add_text_content_script = os.path.join(script_dir, "add_text_content.py")
    add_text_content_args = [
        "--input", os.path.join(script_dir, "flattened_structure.json"),
        "--markdown", md_file_path,
        "--output", os.path.join(script_dir, "structure_with_content.json")
    ]
    
    if not run_script(add_text_content_script, add_text_content_args):
        print(f"{Fore.RED}添加文本内容失败，无法继续处理")
        return False
    
    # 检查并提取Abstract和Introduction
    check_abstract_intro_script = os.path.join(script_dir, "check_abstract_intro.py")
    
    if not run_script(check_abstract_intro_script):
        print(f"{Fore.RED}检查Abstract和Introduction失败，无法继续处理")
        return False
    
    # 插入缺失的Abstract和Introduction
    insert_abstract_intro_script = os.path.join(script_dir, "insert_abstract_intro.py")
    
    if not run_script(insert_abstract_intro_script):
        print(f"{Fore.RED}插入Abstract和Introduction失败，无法继续处理")
        return False
    
    # 提取数学公式
    extract_formulas_script = os.path.join(script_dir, "extract_formulas.py")
    extract_formulas_args = [
        "--input", os.path.join(script_dir, "structure_with_content_updated.json"),
        "--output", os.path.join(script_dir, "structure_with_content_updated.json")
    ]
    
    if not run_script(extract_formulas_script, extract_formulas_args):
        print(f"{Fore.RED}提取数学公式失败，但将继续处理")
    
    # 提取各节内容
    extract_section_content_script = os.path.join(script_dir, "extract_section_content.py")
    extract_section_content_args = [
        "--input", os.path.join(script_dir, "structure_with_content_updated.json"),
        "--output-dir", output_dir
    ]
    
    if not run_script(extract_section_content_script, extract_section_content_args):
        print(f"{Fore.RED}提取各节内容失败")
        return False
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="处理论文结构的完整流程")
    parser.add_argument("input_json", help="包含论文结构的JSON文件路径")
    parser.add_argument("markdown_file", help="论文的Markdown内容文件路径")
    parser.add_argument("--output-dir", help="输出目录路径")
    
    args = parser.parse_args()
    
    success = process_paper_structure(args.input_json, args.markdown_file, args.output_dir)
    
    if success:
        print(f"{Fore.GREEN}处理完成！")
        return 0
    else:
        print(f"{Fore.RED}处理失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 