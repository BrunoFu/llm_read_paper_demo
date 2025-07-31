#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
从Markdown文件中提取特定章节（如References和Introduction）

这个脚本用于从论文的Markdown文件中提取特定章节内容
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def extract_section(markdown_path: str, section_name: str, output_path: str = None) -> Tuple[bool, str]:
    """
    从Markdown文件中提取特定章节
    
    Args:
        markdown_path: Markdown文件路径
        section_name: 要提取的章节名称（如'References', 'Introduction'等）
        output_path: 输出文件路径，如果为None则不保存文件
    
    Returns:
        (成功标志, 提取的内容)
    """
    # 检查文件是否存在
    if not os.path.exists(markdown_path):
        print(f"错误: Markdown文件不存在: {markdown_path}")
        return False, ""
    
    # 读取Markdown文件
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取Markdown文件失败: {e}")
        return False, ""
    
    # 定义可能的章节标题模式
    section_patterns = [
        # 标准Markdown标题格式
        rf"#\s+{section_name}\s*\n",  # # Section
        rf"##\s+{section_name}\s*\n",  # ## Section
        rf"###\s+{section_name}\s*\n",  # ### Section
        # 数字编号格式
        rf"#\s+\d+\s+{section_name}\s*\n",  # # 1 Section
        rf"##\s+\d+\s+{section_name}\s*\n",  # ## 1 Section
        # 数字+点格式
        rf"#\s+\d+\.\s+{section_name}\s*\n",  # # 1. Section
        rf"##\s+\d+\.\s+{section_name}\s*\n",  # ## 1. Section
        # 特殊格式 - 仅数字开头
        rf"\d+\s+{section_name}\s*\n",  # 1 Section
        rf"\d+\.\s+{section_name}\s*\n",  # 1. Section
        # 大写格式
        rf"#\s+{section_name.upper()}\s*\n",  # # SECTION
        rf"##\s+{section_name.upper()}\s*\n",  # ## SECTION
        # 引用格式
        rf">\s+{section_name}\s*\n",  # > Section
        # 无标题符号但有换行的格式
        rf"\n{section_name}\n",  # 单独一行的Section
    ]
    
    # 尝试匹配章节标题
    section_content = None
    for pattern in section_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            start_pos = match.start()
            
            # 找出下一个章节的开始位置
            next_section_patterns = [
                r"#\s+\w+",  # # 任何单词
                r"##\s+\w+",  # ## 任何单词
                r"###\s+\w+",  # ### 任何单词
                r"#\s+\d+\s+\w+",  # # 1 任何单词
                r"##\s+\d+\s+\w+",  # ## 1 任何单词
                r"#\s+\d+\.\s+\w+",  # # 1. 任何单词
                r"##\s+\d+\.\s+\w+",  # ## 1. 任何单词
            ]
            
            end_pos = len(content)
            for next_pattern in next_section_patterns:
                next_matches = list(re.finditer(next_pattern, content[start_pos+1:]))
                if next_matches:
                    potential_end = start_pos + 1 + next_matches[0].start()
                    if potential_end < end_pos:
                        end_pos = potential_end
            
            section_content = content[start_pos:end_pos].strip()
            break
    
    # 如果没有找到章节，尝试更模糊的匹配
    if section_content is None:
        # 尝试查找包含章节名称的行
        fuzzy_patterns = [
            rf".*{section_name}.*\n",  # 任何包含section_name的行
            rf".*{section_name.upper()}.*\n",  # 任何包含SECTION_NAME的行
        ]
        
        for pattern in fuzzy_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                start_pos = match.start()
                
                # 找出下一个可能的章节标题
                next_matches = list(re.finditer(r"\n\n[A-Z][a-z]+", content[start_pos+1:]))
                if next_matches:
                    end_pos = start_pos + 1 + next_matches[0].start()
                    section_content = content[start_pos:end_pos].strip()
                else:
                    # 如果没有下一个章节，则提取到文件末尾
                    section_content = content[start_pos:].strip()
                
                break
    
    # 如果仍然没有找到章节
    if section_content is None:
        print(f"警告: 未找到章节 '{section_name}'")
        return False, ""
    
    # 如果指定了输出路径，保存提取的内容
    if output_path:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(section_content)
            print(f"已将 '{section_name}' 章节保存到: {output_path}")
        except Exception as e:
            print(f"保存章节内容失败: {e}")
            return False, section_content
    
    return True, section_content

def process_paper(markdown_path: str, output_dir: str = None) -> Dict[str, str]:
    """
    处理论文Markdown文件，提取References和Introduction章节
    
    Args:
        markdown_path: Markdown文件路径
        output_dir: 输出目录，如果为None则使用Markdown文件所在目录
    
    Returns:
        包含提取结果的字典
    """
    # 确定输出目录
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(markdown_path))
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 准备输出文件路径
    base_name = Path(markdown_path).stem
    references_path = os.path.join(output_dir, f"{base_name}_references.md")
    introduction_path = os.path.join(output_dir, f"{base_name}_introduction.md")
    
    # 读取Markdown文件内容
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取Markdown文件失败: {e}")
        return {
            "references_success": False,
            "references_content": "",
            "references_path": None,
            "introduction_success": False,
            "introduction_content": "",
            "introduction_path": None
        }
    
    # 直接搜索可能的参考文献章节标记
    ref_success = False
    ref_content = ""
    
    # 尝试提取References章节
    print(f"正在从 {markdown_path} 提取References章节...")
    
    # 尝试各种可能的参考文献章节名称
    reference_patterns = [
        r"# References\b", 
        r"## References\b",
        r"### References\b",
        r"# Reference\b",
        r"## Reference\b",
        r"# Bibliography\b",
        r"## Bibliography\b",
        r"# 参考文献\b",
        r"## 参考文献\b",
        r"# REFERENCES\b",
        r"## REFERENCES\b",
        r"References:",
        r"\nReferences\n",
        r"\nREFERENCES\n",
        r"\d+\.\s*References\b",
        r"\d+\s*References\b",
        r"\d+\.\s*REFERENCES\b",
        r"\d+\s*REFERENCES\b"
    ]
    
    for pattern in reference_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            start_pos = match.start()
            
            # 找出下一个章节的开始位置或文件结尾
            next_section_patterns = [
                r"#\s+\w+",
                r"##\s+\w+",
                r"###\s+\w+",
                r"\d+\.\s+\w+",
                r"\d+\s+\w+"
            ]
            
            end_pos = len(content)
            for next_pattern in next_section_patterns:
                next_matches = list(re.finditer(next_pattern, content[start_pos+1:]))
                if next_matches:
                    potential_end = start_pos + 1 + next_matches[0].start()
                    if potential_end < end_pos:
                        end_pos = potential_end
            
            ref_content = content[start_pos:end_pos].strip()
            ref_success = True
            break
    
    # 如果找到了参考文献章节，保存到文件
    if ref_success and ref_content:
        try:
            with open(references_path, 'w', encoding='utf-8') as f:
                f.write(ref_content)
            print(f"已将References章节保存到: {references_path}")
        except Exception as e:
            print(f"保存References章节失败: {e}")
            ref_success = False
    else:
        print("未找到References章节")
    
    # 尝试提取Introduction章节
    intro_success = False
    intro_content = ""
    
    print(f"正在从 {markdown_path} 提取Introduction章节...")
    
    # 尝试各种可能的引言章节名称
    introduction_patterns = [
        r"# Introduction\b", 
        r"## Introduction\b",
        r"### Introduction\b",
        r"# INTRODUCTION\b",
        r"## INTRODUCTION\b",
        r"# Intro\b",
        r"## Intro\b",
        r"# 引言\b",
        r"## 引言\b",
        r"# 简介\b",
        r"## 简介\b",
        r"Introduction:",
        r"\nIntroduction\n",
        r"\nINTRODUCTION\n",
        r"\d+\.\s*Introduction\b",
        r"\d+\s*Introduction\b",
        r"\d+\.\s*INTRODUCTION\b",
        r"\d+\s*INTRODUCTION\b",
        r"# 1 Introduction\b",
        r"## 1 Introduction\b",
        r"# 1. Introduction\b",
        r"## 1. Introduction\b"
    ]
    
    for pattern in introduction_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            start_pos = match.start()
            
            # 找出下一个章节的开始位置或文件结尾
            next_section_patterns = [
                r"#\s+\w+",
                r"##\s+\w+",
                r"###\s+\w+",
                r"\d+\.\s+\w+",
                r"\d+\s+\w+"
            ]
            
            end_pos = len(content)
            for next_pattern in next_section_patterns:
                next_matches = list(re.finditer(next_pattern, content[start_pos+1:]))
                if next_matches:
                    potential_end = start_pos + 1 + next_matches[0].start()
                    if potential_end < end_pos:
                        end_pos = potential_end
            
            intro_content = content[start_pos:end_pos].strip()
            intro_success = True
            break
    
    # 如果找到了引言章节，保存到文件
    if intro_success and intro_content:
        try:
            with open(introduction_path, 'w', encoding='utf-8') as f:
                f.write(intro_content)
            print(f"已将Introduction章节保存到: {introduction_path}")
        except Exception as e:
            print(f"保存Introduction章节失败: {e}")
            intro_success = False
    else:
        print("未找到Introduction章节")
    
    # 返回结果
    result = {
        "references_success": ref_success,
        "references_content": ref_content,
        "references_path": references_path if ref_success else None,
        "introduction_success": intro_success,
        "introduction_content": intro_content,
        "introduction_path": introduction_path if intro_success else None
    }
    
    return result

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="从Markdown文件中提取特定章节")
    parser.add_argument("markdown_path", help="Markdown文件路径")
    parser.add_argument("--output-dir", "-d", help="输出目录")
    
    args = parser.parse_args()
    
    # 处理论文
    result = process_paper(args.markdown_path, args.output_dir)
    
    # 打印结果
    if result["references_success"]:
        print(f"References章节已保存到: {result['references_path']}")
    else:
        print("未找到References章节")
    
    if result["introduction_success"]:
        print(f"Introduction章节已保存到: {result['introduction_path']}")
    else:
        print("未找到Introduction章节")

if __name__ == "__main__":
    main() 