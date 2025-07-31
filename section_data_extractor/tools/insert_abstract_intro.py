#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
将缺失的abstract和introduction插入到structure_with_content.json中
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Fore.RED}加载JSON文件时出错: {e}")
        return None

def load_markdown_file(file_path):
    """加载Markdown文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"{Fore.RED}加载Markdown文件时出错: {e}")
        return None

def find_line_number(markdown_lines, text_start, text_end):
    """
    使用模糊匹配算法查找文本的起始和结束行号
    """
    import difflib  # Python标准库中的模糊匹配工具
    
    start_line = -1
    end_line = -1
    
    # 清理文本
    text_start = text_start.strip()
    text_end = text_end.strip()
    
    # 提取前50个字符作为匹配模式
    start_pattern = text_start[:50].strip()
    end_pattern = text_end[:50].strip()
    
    # 设置相似度阈值
    threshold = 0.8
    
    # 查找开始行 - 使用模糊匹配
    best_ratio = 0
    best_start_line = -1
    for i, line in enumerate(markdown_lines):
        # 计算相似度比率
        ratio = difflib.SequenceMatcher(None, start_pattern, line[:min(len(line), 100)]).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_start_line = i
    
    # 如果找到足够相似的行
    if best_ratio >= threshold:
        start_line = best_start_line
        print(f"找到起始行 {start_line}，相似度: {best_ratio:.2f}")
        print(f"匹配内容: {markdown_lines[start_line][:50]}...")
    else:
        # 降低阈值再尝试
        if best_ratio > 0.5:
            start_line = best_start_line
            print(f"使用较低阈值找到起始行 {start_line}，相似度: {best_ratio:.2f}")
            print(f"匹配内容: {markdown_lines[start_line][:50]}...")
    
    # 如果找到了起始行，继续查找结束行
    if start_line != -1:
        best_ratio = 0
        best_end_line = -1
        # 从起始行开始查找
        for i, line in enumerate(markdown_lines[start_line:], start=start_line):
            ratio = difflib.SequenceMatcher(None, end_pattern, line[:min(len(line), 100)]).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_end_line = i
        
        # 如果找到足够相似的行
        if best_ratio >= threshold:
            end_line = best_end_line
            print(f"找到结束行 {end_line}，相似度: {best_ratio:.2f}")
            print(f"匹配内容: {markdown_lines[end_line][:50]}...")
        else:
            # 降低阈值再尝试
            if best_ratio > 0.5:
                end_line = best_end_line
                print(f"使用较低阈值找到结束行 {end_line}，相似度: {best_ratio:.2f}")
                print(f"匹配内容: {markdown_lines[end_line][:50]}...")
    
    return start_line, end_line

def find_line_number_improved(markdown_lines, text_start, text_end):
    """
    使用句子级模糊匹配算法查找文本的起始和结束行号
    """
    import difflib
    import re
    
    start_line = -1
    end_line = -1
    
    # 清理文本
    text_start = text_start.strip()
    text_end = text_end.strip()
    
    # 提取文本的前几个句子作为匹配模式
    def extract_sentences(text, num_sentences=2):
        # 使用正则表达式分割句子（按.!?分割）
        sentences = re.split(r'[.!?]', text)
        # 过滤空句子并限制数量
        # sentences = [s.strip() for s in sentences if s.strip()][:num_sentences]
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    start_sentences = extract_sentences(text_start)
    end_sentences = extract_sentences(text_end)
    
    # 设置相似度阈值
    threshold = 0.7  # 句子级匹配可以稍微降低阈值
    
    # 查找开始行 - 使用句子级模糊匹配
    best_overall_ratio = 0
    best_start_line = -1
    
    for i, line in enumerate(markdown_lines):
        # 将行分割成句子
        line_sentences = extract_sentences(line)
        if not line_sentences:
            continue
            
        # 计算每个句子与目标句子的最佳匹配度
        sentence_ratios = []
        for target_sent in start_sentences:
            best_sent_ratio = 0
            for line_sent in line_sentences:
                ratio = difflib.SequenceMatcher(None, target_sent, line_sent).ratio()
                best_sent_ratio = max(best_sent_ratio, ratio)
            if best_sent_ratio > 0:  # 只考虑有匹配的句子
                sentence_ratios.append(best_sent_ratio)
        
        # 计算整体匹配度（句子匹配度的平均值）
        if sentence_ratios:
            overall_ratio = sum(sentence_ratios) / len(sentence_ratios)
            if overall_ratio > best_overall_ratio:
                best_overall_ratio = overall_ratio
                best_start_line = i
    
    # 如果找到足够相似的行
    if best_overall_ratio >= threshold:
        start_line = best_start_line
        print(f"找到起始行 {start_line}，整体相似度: {best_overall_ratio:.2f}")
        print(f"匹配内容: {markdown_lines[start_line][:50]}...")
    else:
        # 降低阈值再尝试
        if best_overall_ratio > 0.4:
            start_line = best_start_line
            print(f"使用较低阈值找到起始行 {start_line}，相似度: {best_overall_ratio:.2f}")
            print(f"匹配内容: {markdown_lines[start_line][:50]}...")
    
    # 类似地实现结束行查找...
    # 从起始行开始查找结束行，使用相同的句子级匹配逻辑
    
    if start_line != -1:
        best_overall_ratio = 0
        best_end_line = -1
        
        for i, line in enumerate(markdown_lines[start_line:], start=start_line):
            line_sentences = extract_sentences(line)
            if not line_sentences:
                continue
                
            sentence_ratios = []
            for target_sent in end_sentences:
                best_sent_ratio = 0
                for line_sent in line_sentences:
                    ratio = difflib.SequenceMatcher(None, target_sent, line_sent).ratio()
                    best_sent_ratio = max(best_sent_ratio, ratio)
                if best_sent_ratio > 0:
                    sentence_ratios.append(best_sent_ratio)
            
            if sentence_ratios:
                overall_ratio = sum(sentence_ratios) / len(sentence_ratios)
                if overall_ratio > best_overall_ratio:
                    best_overall_ratio = overall_ratio
                    best_end_line = i
        
        if best_overall_ratio >= threshold:
            end_line = best_end_line
            print(f"找到结束行 {end_line}，整体相似度: {best_overall_ratio:.2f}")
            print(f"匹配内容: {markdown_lines[end_line][:50]}...")
        else:
            if best_overall_ratio > 0.4:
                end_line = best_end_line
                print(f"使用较低阈值找到结束行 {end_line}，相似度: {best_overall_ratio:.2f}")
                print(f"匹配内容: {markdown_lines[end_line][:50]}...")
    
    return start_line, end_line

def create_section_entry(title, line_number, next_line_number, text_content):
    """
    创建新的章节条目
    
    Args:
        title: 章节标题
        line_number: 开始行号
        next_line_number: 结束行号
        text_content: 文本内容
    
    Returns:
        dict: 章节条目
    """
    return {
        "title": title,
        "level": 1,
        "sub_level": None,
        "line_number": line_number,
        "next_line_number": next_line_number,
        "text_content": text_content,
        "sub_title_list": [],
        "figures": [],
        "tables": [],
        "references": []
    }

def clean_abstract_content(abstract_content, intro_content):
    """
    从abstract的text_content中删除introduction的内容
    
    Args:
        abstract_content: Abstract的文本内容
        intro_content: Introduction的文本内容
    
    Returns:
        str: 清理后的Abstract内容
    """
    if not intro_content or not abstract_content:
        return abstract_content
    
    # 尝试找到Introduction内容在Abstract中的起始位置
    intro_start = intro_content[:100].strip()  # 取Introduction内容的前100个字符作为匹配模式
    
    # 使用模糊匹配查找Introduction内容在Abstract中的位置
    import difflib
    
    # 将Abstract内容按段落分割
    paragraphs = abstract_content.split('\n\n')
    clean_paragraphs = []
    
    # 标记是否已找到Introduction内容
    found_intro = False
    
    for para in paragraphs:
        # 如果段落是Abstract标题，直接保留
        if re.search(r'#+\s*abstract', para.lower()):
            clean_paragraphs.append(para)
            continue
            
        # 计算段落与Introduction起始内容的相似度
        ratio = difflib.SequenceMatcher(None, para[:100].strip(), intro_start).ratio()
        
        # 如果相似度高于阈值，认为找到了Introduction内容的起始
        if ratio > 0.7:
            found_intro = True
            continue
        
        # 如果已找到Introduction内容，后续段落都不保留
        if found_intro:
            continue
            
        # 否则保留该段落
        clean_paragraphs.append(para)
    
    # 如果没有找到明确的Introduction起始，尝试基于段落数量进行分割
    if not found_intro and len(paragraphs) > 3:
        # 假设Abstract通常只有1-2个段落，保留前2个非空段落
        clean_paragraphs = []
        count = 0
        for para in paragraphs:
            if para.strip():
                clean_paragraphs.append(para)
                count += 1
                if count >= 2:
                    break
    
    return '\n\n'.join(clean_paragraphs)

def insert_sections(structure_data, abstract_intro_data, markdown_lines):
    """
    将缺失的abstract和introduction插入到结构中
    
    Args:
        structure_data: 结构数据
        abstract_intro_data: abstract和introduction数据
        markdown_lines: Markdown文件的行列表
    
    Returns:
        dict: 更新后的结构数据
    """
    # 检查是否已经有abstract和introduction
    has_both = abstract_intro_data.get("has_both_sections", False)
    if has_both:
        print(f"{Fore.GREEN}结构中已包含abstract和introduction，无需插入")
        return structure_data
    
    # 获取缺失的部分
    missing_sections = abstract_intro_data.get("missing_sections", [])
    extracted_data = abstract_intro_data.get("extracted_data", {})
    
    # 找到level=0的元素索引
    level0_index = -1
    for i, item in enumerate(structure_data):
        if item.get("level") == 0:
            level0_index = i
            break
    
    if level0_index == -1:
        print(f"{Fore.RED}错误: 无法找到level=0的元素")
        return structure_data
    
    # 要插入的新章节
    new_sections = []
    
    # 存储提取的内容，用于后续处理
    abstract_content = None
    intro_content = None
    
    # 处理缺失的abstract
    if "abstract" in missing_sections and "abstract" in extracted_data:
        print(f"{Fore.CYAN}正在处理缺失的abstract")
        abstract_start = extracted_data["abstract"].get("start")
        abstract_end = extracted_data["abstract"].get("end")
        
        if abstract_start and abstract_end:
            # 查找行号
            start_line, end_line = find_line_number_improved(markdown_lines, abstract_start, abstract_end)
            
            if start_line >= 0 and end_line >= 0:
                # 提取文本内容
                abstract_content = "".join(markdown_lines[start_line:end_line+1])
                
                # 创建abstract条目
                abstract_entry = create_section_entry(
                    "Abstract", 
                    start_line, 
                    end_line + 1, 
                    abstract_content
                )
                
                new_sections.append(abstract_entry)
                print(f"{Fore.GREEN}已创建Abstract条目，行号: {start_line}-{end_line}")
    else:
        # 如果abstract已存在，找到它的内容
        for item in structure_data:
            if item.get("title", "").lower() == "abstract":
                abstract_content = item.get("text_content", "")
                break
    
    # 处理缺失的introduction
    if "introduction" in missing_sections and "introduction" in extracted_data:
        print(f"{Fore.CYAN}正在处理缺失的introduction")
        intro_start = extracted_data["introduction"].get("start")
        intro_end = extracted_data["introduction"].get("end")
        
        if intro_start and intro_end:
            # 查找行号
            start_line, end_line = find_line_number_improved(markdown_lines, intro_start, intro_end)
            
            if start_line >= 0 and end_line >= 0:
                # 提取文本内容
                intro_content = "".join(markdown_lines[start_line:end_line+1])
                
                # 创建introduction条目
                intro_entry = create_section_entry(
                    "Introduction", 
                    start_line, 
                    end_line + 1, 
                    intro_content
                )
                
                new_sections.append(intro_entry)
                print(f"{Fore.GREEN}已创建Introduction条目，行号: {start_line}-{end_line}")
    else:
        # 如果introduction已存在，找到它的内容
        for item in structure_data:
            if item.get("title", "").lower() == "introduction":
                intro_content = item.get("text_content", "")
                break
    
    # 处理特殊情况：缺失introduction但有abstract，且abstract内容包含introduction
    if "introduction" in missing_sections and "abstract" not in missing_sections and abstract_content and intro_content:
        print(f"{Fore.YELLOW}检测到缺失introduction但有abstract，且abstract可能包含introduction内容")
        
        # 查找已存在的abstract条目
        for i, item in enumerate(structure_data):
            if item.get("title", "").lower() == "abstract":
                # 清理abstract内容
                cleaned_abstract = clean_abstract_content(abstract_content, intro_content)
                
                if cleaned_abstract != abstract_content:
                    print(f"{Fore.GREEN}从abstract中删除了introduction内容")
                    structure_data[i]["text_content"] = cleaned_abstract
                break
    
    # 按照行号排序新章节
    new_sections.sort(key=lambda x: x["line_number"])
    
    # 插入新章节
    for i, section in enumerate(new_sections):
        structure_data.insert(level0_index + 1 + i, section)
    
    return structure_data

def update_level0_content(structure_data, markdown_content):
    """
    更新level=0元素的text_content为全文内容
    
    Args:
        structure_data: 结构数据
        markdown_content: 完整的Markdown内容
    
    Returns:
        dict: 更新后的结构数据
    """
    for i, item in enumerate(structure_data):
        if item.get("level") == 0:
            structure_data[i]["text_content"] = markdown_content
            print(f"{Fore.GREEN}已更新level=0元素的text_content为全文内容")
            break
    
    return structure_data

def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # 设置文件路径
    structure_path = os.path.join(script_dir, "structure_with_content.json")
    abstract_intro_path = os.path.join(script_dir, "abstract_intro.json")
    markdown_path = os.path.join(parent_dir, "AER202501_8_gruber-et-al-2025-dying-or-lying-for-profit-hospices-and-end-of-life-care_full.md")
    output_path = os.path.join(script_dir, "structure_with_content_updated.json")
    
    # 加载数据
    structure_data = load_json_file(structure_path)
    abstract_intro_data = load_json_file(abstract_intro_path)
    markdown_lines = load_markdown_file(markdown_path)
    
    if not structure_data or not abstract_intro_data or not markdown_lines:
        print(f"{Fore.RED}加载数据失败，请确保所有文件都存在")
        return False
    
    # 插入缺失的章节
    updated_structure = insert_sections(structure_data, abstract_intro_data, markdown_lines)
    
    # 更新level=0元素的text_content为全文内容
    markdown_content = "".join(markdown_lines)
    updated_structure = update_level0_content(updated_structure, markdown_content)
    
    # 保存更新后的结构
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(updated_structure, f, ensure_ascii=False, indent=2)
        
        # 备份原始文件
        backup_path = os.path.join(script_dir, "structure_with_content_backup.json")
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(structure_data, f, ensure_ascii=False, indent=2)
        
        # 替换原始文件
        with open(structure_path, 'w', encoding='utf-8') as f:
            json.dump(updated_structure, f, ensure_ascii=False, indent=2)
        
        print(f"{Fore.GREEN}已成功插入缺失的章节并更新结构文件")
        print(f"{Fore.GREEN}原始文件已备份为: {backup_path}")
        return True
    except Exception as e:
        print(f"{Fore.RED}保存更新后的结构时出错: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="将缺失的abstract和introduction插入到结构中")
    parser.add_argument("--structure", help="结构JSON文件路径", default="structure_with_content.json")
    parser.add_argument("--abstract-intro", help="abstract和introduction数据文件路径", default="abstract_intro.json")
    parser.add_argument("--markdown", help="Markdown文件路径", default="../AER202501_8_gruber-et-al-2025-dying-or-lying-for-profit-hospices-and-end-of-life-care_full.md")
    parser.add_argument("--output", help="输出文件路径", default="structure_with_content_updated.json")
    
    args = parser.parse_args()
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置文件路径
    structure_path = os.path.join(script_dir, args.structure) if not os.path.isabs(args.structure) else args.structure
    abstract_intro_path = os.path.join(script_dir, args.abstract_intro) if not os.path.isabs(args.abstract_intro) else args.abstract_intro
    markdown_path = args.markdown if os.path.isabs(args.markdown) else os.path.join(os.path.dirname(script_dir), os.path.basename(args.markdown))
    output_path = os.path.join(script_dir, args.output) if not os.path.isabs(args.output) else args.output
    
    # 修改全局变量
    globals()["structure_path"] = structure_path
    globals()["abstract_intro_path"] = abstract_intro_path
    globals()["markdown_path"] = markdown_path
    globals()["output_path"] = output_path
    
    success = main()
    sys.exit(0 if success else 1)