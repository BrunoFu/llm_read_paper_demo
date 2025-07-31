#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PDF处理器 - 集成工具

该脚本集成了section_data_extractor/tools目录下的各个工具函数，
实现从Markdown文本中提取论文结构、添加内容并输出到指定目录的完整工作流。

用法:
    python integrated_processor.py --input input.md --output-dir ./output [--resources-dir ./resources]

参数:
    --input: 输入的Markdown文件路径
    --output-dir: 输出目录路径
    --resources-dir: 资源目录路径(可选，默认为./resources)
"""

import os
import sys
import json
import argparse
import shutil
import asyncio
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

# 添加tools目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.join(current_dir, "tools")
sys.path.insert(0, tools_dir)
sys.path.insert(0, current_dir)

# 导入工具函数
from extract_paper_structure import extract_paper_structure, load_markdown_file
from extract_title_lines import extract_title_line_numbers
from flatten_structure import merge_and_flatten_structure
from add_text_content import add_text_content
from check_abstract_intro import check_section_exists, extract_abstract_intro
from insert_abstract_intro import insert_sections, update_level0_content
from extract_section_content import extract_section_contents, save_individual_sections
from extract_formulas import add_formulas_to_structure

def ensure_dir_exists(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"{Fore.CYAN}创建目录: {directory}")

async def process_markdown(input_md_path, output_dir, resources_dir):
    """处理Markdown文件的完整工作流"""
    print(f"{Fore.CYAN}开始处理文件: {input_md_path}")
    print(f"{Fore.CYAN}输出目录: {output_dir}")
    
    # 确保输出目录存在
    ensure_dir_exists(output_dir)
    
    # 创建临时JSON文件目录
    json_output_dir = os.path.join(output_dir, "json")
    ensure_dir_exists(json_output_dir)
    
    # 创建章节输出目录
    sections_dir = os.path.join(output_dir, "sections")
    ensure_dir_exists(sections_dir)
    
    # 设置JSON文件路径
    input_json_path = os.path.join(json_output_dir, "input.json")
    input_with_row_num_path = os.path.join(json_output_dir, "input_with_row_num.json")
    flattened_structure_path = os.path.join(json_output_dir, "flattened_structure.json")
    structure_with_content_path = os.path.join(json_output_dir, "structure_with_content.json")
    abstract_intro_path = os.path.join(json_output_dir, "abstract_intro.json")
    structure_with_content_updated_path = os.path.join(json_output_dir, "structure_with_content_updated.json")
    
    # 设置提示模板路径
    extract_frame_template_path = os.path.join(resources_dir, "extract_frame_and_tabs_figs.md")
    extract_abstract_intro_template_path = os.path.join(resources_dir, "extract_abstract_intro.md")
    
    # 步骤1: 加载Markdown文件
    print(f"{Fore.CYAN}步骤1: 加载Markdown文件...")
    markdown_content = load_markdown_file(input_md_path)
    if not markdown_content:
        print(f"{Fore.RED}无法加载Markdown文件，请确保文件存在")
        return False
    
    markdown_lines = markdown_content.splitlines(keepends=True)
    
    # 步骤2: 提取论文结构
    print(f"{Fore.CYAN}步骤2: 提取论文结构...")
    if not os.path.exists(extract_frame_template_path):
        print(f"{Fore.RED}提示模板文件不存在: {extract_frame_template_path}")
        return False
        
    structure = await extract_paper_structure(markdown_content, extract_frame_template_path)
    if not structure:
        print(f"{Fore.RED}提取论文结构失败")
        return False
    
    # 保存提取的结构
    with open(input_json_path, 'w', encoding='utf-8') as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)
    print(f"{Fore.GREEN}已保存论文结构到: {input_json_path}")
    
    # 步骤3: 提取标题行号
    print(f"{Fore.CYAN}步骤3: 提取标题行号...")
    structure_with_lines = extract_title_line_numbers(structure, markdown_lines)
    
    # 保存带行号的结构
    with open(input_with_row_num_path, 'w', encoding='utf-8') as f:
        json.dump(structure_with_lines, f, ensure_ascii=False, indent=2)
    print(f"{Fore.GREEN}已保存带行号的结构到: {input_with_row_num_path}")
    
    # 步骤4: 展平结构
    print(f"{Fore.CYAN}步骤4: 展平结构...")
    flattened_structure = merge_and_flatten_structure(structure, structure_with_lines)
    
    # 保存展平的结构
    with open(flattened_structure_path, 'w', encoding='utf-8') as f:
        json.dump(flattened_structure, f, ensure_ascii=False, indent=2)
    print(f"{Fore.GREEN}已保存展平的结构到: {flattened_structure_path}")
    
    # 步骤5: 添加文本内容
    print(f"{Fore.CYAN}步骤5: 添加文本内容...")
    structure_with_content = add_text_content(flattened_structure, markdown_lines)
    
    # 保存带内容的结构
    with open(structure_with_content_path, 'w', encoding='utf-8') as f:
        json.dump(structure_with_content, f, ensure_ascii=False, indent=2)
    print(f"{Fore.GREEN}已保存带内容的结构到: {structure_with_content_path}")
    
    # 步骤6: 检查Abstract和Introduction
    print(f"{Fore.CYAN}步骤6: 检查Abstract和Introduction...")
    has_abstract, abstract_data = check_section_exists(structure_with_content, "abstract")
    has_intro, intro_data = check_section_exists(structure_with_content, "introduction")
    
    print(f"  Abstract: {'存在' if has_abstract else '不存在'}")
    print(f"  Introduction: {'存在' if has_intro else '不存在'}")
    
    # 构建结果
    abstract_intro_result = {
        "has_both_sections": has_abstract and has_intro,
        "missing_sections": []
    }
    
    if not has_abstract:
        abstract_intro_result["missing_sections"].append("abstract")
    else:
        abstract_intro_result["abstract"] = abstract_data
    
    if not has_intro:
        abstract_intro_result["missing_sections"].append("introduction")
    else:
        abstract_intro_result["introduction"] = intro_data
    
    # 如果缺少任一部分，从文本中提取
    if not has_abstract or not has_intro:
        print(f"{Fore.YELLOW}缺少{'abstract' if not has_abstract else ''}{' 和 ' if not has_abstract and not has_intro else ''}{' introduction' if not has_intro else ''}，将从文本内容中提取")
        
        if not os.path.exists(extract_abstract_intro_template_path):
            print(f"{Fore.RED}提示模板文件不存在: {extract_abstract_intro_template_path}")
            return False
            
        extracted_data = await extract_abstract_intro(markdown_content, extract_abstract_intro_template_path)
        abstract_intro_result["extracted_data"] = extracted_data
    
    # 保存Abstract和Introduction检查结果
    with open(abstract_intro_path, 'w', encoding='utf-8') as f:
        json.dump(abstract_intro_result, f, ensure_ascii=False, indent=2)
    print(f"{Fore.GREEN}已保存Abstract和Introduction检查结果到: {abstract_intro_path}")
    
    # 步骤7: 插入缺失的Abstract和Introduction
    print(f"{Fore.CYAN}步骤7: 插入缺失的Abstract和Introduction...")
    updated_structure = insert_sections(structure_with_content, abstract_intro_result, markdown_lines)
    
    # 步骤8: 更新level=0的text_content为全文内容
    print(f"{Fore.CYAN}步骤8: 更新level=0的text_content为全文内容...")
    updated_structure = update_level0_content(updated_structure, markdown_content)
    
    # 步骤9: 提取数学公式
    print(f"{Fore.CYAN}步骤9: 提取数学公式...")
    updated_structure, total_formulas, items_with_formulas = add_formulas_to_structure(updated_structure)
    print(f"  提取到 {total_formulas} 个公式，分布在 {items_with_formulas} 个节点中")
    
    # 保存更新后的结构
    with open(structure_with_content_updated_path, 'w', encoding='utf-8') as f:
        json.dump(updated_structure, f, ensure_ascii=False, indent=2)
    print(f"{Fore.GREEN}已保存更新后的结构到: {structure_with_content_updated_path}")
    
    # 步骤10: 提取各节内容
    print(f"{Fore.CYAN}步骤10: 提取各节内容...")
    section_contents = extract_section_contents(updated_structure, markdown_lines)
    
    # 保存各节为单独文件
    save_individual_sections(section_contents, sections_dir)
    
    # 步骤11: 将结构化数据复制到根目录，方便前端访问
    print(f"{Fore.CYAN}步骤11: 复制结构化数据到根目录...")
    paper_structure_path = os.path.join(output_dir, "paper_structure.json")
    shutil.copy(structure_with_content_updated_path, paper_structure_path)
    print(f"{Fore.GREEN}已复制结构化数据到: {paper_structure_path}")
    
    print(f"{Fore.GREEN}处理完成！")
    return True

async def process_paper_structure(input_md_path: str, output_dir: str, resources_dir: str = None) -> bool:
    """
    处理论文结构的主函数，供外部调用

    Args:
        input_md_path: 输入的Markdown文件路径
        output_dir: 输出目录路径
        resources_dir: 资源目录路径(可选)

    Returns:
        bool: 处理是否成功
    """
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)

    # 检查输入文件是否存在
    if not os.path.exists(input_md_path):
        print(f"{Fore.RED}错误: 输入文件不存在: {input_md_path}")
        return False

    # 检查工具目录是否存在
    if not os.path.exists(tools_dir):
        print(f"{Fore.RED}错误: 工具目录不存在: {tools_dir}")
        return False

    # 设置资源目录，优先使用项目根目录下的resources
    if not resources_dir:
        # 首先检查项目根目录下是否有resources
        resources_dir = os.path.join(parent_dir, "resources")
        if not os.path.exists(resources_dir):
            # 然后检查当前目录下是否有resources
            resources_dir = os.path.join(current_dir, "resources")

    if not os.path.exists(resources_dir):
        print(f"{Fore.RED}错误: 资源目录不存在: {resources_dir}")
        return False

    # 调用处理流程
    success = await process_markdown(input_md_path, output_dir, resources_dir)

    return success

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="处理OCR PDF转换后的Markdown文件")
    parser.add_argument("--input", required=True, help="输入的Markdown文件路径")
    parser.add_argument("--output-dir", required=True, help="输出目录路径")
    parser.add_argument("--resources-dir", default=None, help="资源目录路径")

    args = parser.parse_args()

    # 创建带有时间戳的输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_filename = os.path.splitext(os.path.basename(args.input))[0]
    output_dir = os.path.join(args.output_dir, f"{input_filename}_{timestamp}")

    # 运行处理流程
    success = await process_paper_structure(args.input, output_dir, args.resources_dir)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 