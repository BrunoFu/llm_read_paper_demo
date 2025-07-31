#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
增强版PDF结构化内容提取工具 (pdf_extract_enhanced.py)

这个模块整合了pdf_extract.py和paper_metadata_extractor_mineru.py的功能，用于从PDF文件中提取结构化内容，主要功能包括：
1. 使用magic_pdf库分析并提取PDF内容
2. 识别文档标题层次结构和各级标题内容
3. 支持中英文多种标题格式(数字编号、罗马数字、中文数字等)
4. 提取文档中的表格、图片和数学公式
5. 提取脚注和页眉页脚
6. 生成不同版本的Markdown输出（完整版、清洁版、前几页）
7. 将内容转换为Markdown格式，并替换表格为图片引用
8. 输出结构化的JSON数据，包含文档的完整层次结构及内容

输出结果包括:
- 完整Markdown文件 (name_full.md) - 包含所有内容
- 清洁版Markdown文件 (name_clean_full.md) - 不含页眉页脚
- 前几页Markdown文件 (name_first_three_pages.md) - 仅包含前几页内容
- 结构化内容的JSON文件 (_extract_result.json)
- 图片内容存储到images文件夹
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 尝试导入MinerU相关库
try:
    from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
    from magic_pdf.data.dataset import PymuDocDataset
    from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
    from magic_pdf.config.enums import SupportedPdfParseMethod
    from magic_pdf.config.make_content_config import DropMode, MakeMode
except ImportError:
    print("无法导入magic_pdf库，请确保已激活包含MinerU的环境")
    print("可以使用: conda activate /Volumes/ssd/conda_env/mineru")
    sys.exit(1)

def extract_headings_with_levels_and_contents(markdown_text):
    """提取标题、确定级别和编号，并获取每个标题下的内容"""
    heading_pattern = re.compile(r'^(#+)\s+(.*?)$', re.MULTILINE)
    matches = list(heading_pattern.finditer(markdown_text))
    
    if not matches:
        return []
    
    headings = []
    
    for i, match in enumerate(matches):
        heading_markers = match.group(1)
        heading_text = match.group(2).strip()
        
        md_level = len(heading_markers) - 1
        prefix = extract_title_prefix(heading_text)
        actual_level = determine_actual_level(heading_text)
        
        start_pos = match.end()
        
        if i < len(matches) - 1:
            end_pos = matches[i+1].start()
        else:
            end_pos = len(markdown_text)
        
        content = markdown_text[start_pos:end_pos].strip()
        
        headings.append({
            "title": heading_text,
            "prefix": prefix,
            "markdown_level": md_level,
            "actual_level": actual_level,
            "subtitle": [],
            "contents": content
        })
    
    return headings

def extract_title_prefix(title):
    """提取标题的编号前缀，包括中文数字、罗马数字、字母及阿拉伯数字编号"""
    patterns = [
        # 中文数字标题模式 - 支持全角和半角
        r'^(一|二|三|四|五|六|七|八|九|十)、',                   # 匹配中文一级标题，如 "一、"
        r'^[（(](一|二|三|四|五|六|七|八|九|十)[）)]',           # 匹配中文二级标题，支持半角和全角括号
        # 原有的模式
        r'^(I{1,3}|IV|V|VI{1,3}|IX|X)\.([A-Z])[\.\s]*',     # 匹配罗马数字+字母，如 "II.A."
        r'^(I{1,3}|IV|V|VI{1,3}|IX|X)[\.\s]*',              # 匹配ASCII罗马数字，如 "II."
        r'^(Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|Ⅵ|Ⅶ|Ⅷ|Ⅸ|Ⅹ)[\.\s]*',                # 匹配Unicode罗马数字
        r'^([A-Z])[\.\s]*',                                 # 匹配字母标题
        r'^(\d+)\.(\d+)\.(\d+)[\.\s]*',                     # 匹配三级数字标题
        r'^(\d+)\.(\d+)[\.\s]*',                            # 匹配二级数字标题
        r'^(\d+)[\.\s]*'                                    # 匹配一级数字标题
    ]
    
    for pattern in patterns:
        match = re.match(pattern, title)
        if match:
            return match.group(0)
    
    return ""

def determine_actual_level(heading_text):
    """根据标题文本确定实际级别，支持中文数字、罗马数字和字母的嵌套结构"""
    # 中文数字标题模式，适配中文期刊
    chinese_first_level = r'^(一|二|三|四|五|六|七|八|九|十)、'    # 一、二、三、等
    chinese_second_level = r'^[（(](一|二|三|四|五|六|七|八|九|十)[）)]'  # 支持半角和全角括号
    
    # 三级数字标题，如 "2.1.1 "
    third_level_pattern = r'^(\d+)\.(\d+)\.(\d+)[\.\s]*'
    # 二级数字标题，如 "2.1 "
    second_level_pattern = r'^(\d+)\.(\d+)[\.\s]*'
    # 一级数字标题，如 "2 "
    first_level_pattern = r'^(\d+)[\.\s]*'
    
    # 罗马数字标题(ASCII形式)，如 "I.", "II.", "III."
    roman_pattern = r'^(I{1,3}|IV|V|VI{1,3}|IX|X)[\.\s]*'
    # 罗马数字+字母组合，如 "I.A.", "II.B."
    roman_alpha_pattern = r'^(I{1,3}|IV|V|VI{1,3}|IX|X)\.([A-Z])[\.\s]*'
    # 普通字母标题，如 "A "
    alpha_pattern = r'^([A-Z])[\.\s]*'
    
    # Unicode罗马数字，如 "Ⅰ "
    unicode_roman_pattern = r'^(Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|Ⅵ|Ⅶ|Ⅷ|Ⅸ|Ⅹ)[\.\s]*'
    
    # 中文标题判断
    if re.search(chinese_second_level, heading_text):
        return 2  # 中文（一）（二）等是二级标题
    if re.search(chinese_first_level, heading_text):
        return 1  # 中文一、二、等是一级标题
    
    if re.search(roman_alpha_pattern, heading_text):
        return 3  # 罗马数字+字母是三级标题
    if re.search(third_level_pattern, heading_text):
        return 3
    if re.search(roman_pattern, heading_text):
        return 2  # 罗马数字是二级标题
    if re.search(second_level_pattern, heading_text):
        return 2
    if re.search(alpha_pattern, heading_text):
        return 2
    if re.search(unicode_roman_pattern, heading_text):
        return 1
    if re.search(first_level_pattern, heading_text):
        return 1
    
    return 0

def build_title_hierarchy(headings):
    """构建标题层次结构，为每个标题添加subtitle属性"""
    level_groups = {0: [], 1: [], 2: [], 3: []}
    for heading in headings:
        level = heading["actual_level"]
        level_groups[level].append(heading)
    
    for level_2 in level_groups[2]:
        prefix = level_2["prefix"]
        if prefix:
            parent_prefix_match = re.match(r'^(\d+)\.', prefix)
            if parent_prefix_match:
                parent_prefix = parent_prefix_match.group(1) + ". "
                for level_1 in level_groups[1]:
                    if level_1["prefix"] == parent_prefix:
                        level_1["subtitle"].append(level_2["title"])
    
    for level_3 in level_groups[3]:
        prefix = level_3["prefix"]
        if prefix:
            parent_prefix_match = re.match(r'^(\d+)\.(\d+)\.', prefix)
            if parent_prefix_match:
                parent_prefix = f"{parent_prefix_match.group(1)}.{parent_prefix_match.group(2)}. "
                for level_2 in level_groups[2]:
                    if level_2["prefix"] == parent_prefix:
                        level_2["subtitle"].append(level_3["title"])
    
    return headings

def extract_tables_and_figures(content, content_list_content=None):
    """
    提取内容中的表格和图片名称，并在content_list_content中查找匹配项
    支持中英文格式
    
    Args:
        content: 要分析的文本内容
        content_list_content: 可选，包含表格和图片信息的内容列表
    
    Returns:
        包含表格和图片信息的字典
    """
    tables = []
    figures = []
    matched_tables = []
    matched_figures = []
    
    # 英文表格模式
    table_patterns = [
        r'Table\s+([A-Z0-9]+\.[A-Z0-9]+|[0-9]+)', 
        r'Table\s+([0-9]+)\s+in\s+\w+\s+appendix',
        r'Table\s+(I{1,3}|IV|V|VI{1,3}|IX|X{1,3}|XI{1,3}|XI{0,1}V|XV|XVI{1,3}|XIX|XX)'  # 匹配罗马数字表格引用
    ]
    
    # 中文表格模式
    chinese_table_patterns = [
        r'表\s*([0-9]+)',  # 匹配中文表格，如"表 1"、"表1"
        r'表\s*(I{1,3}|IV|V|VI{1,3}|IX|X{1,3}|XI{1,3}|XI{0,1}V|XV|XVI{1,3}|XIX|XX)',  # 匹配中文罗马数字表格，如"表 I"
        r'表\s*([一二三四五六七八九十]{1,2})'  # 匹配中文数字表格，如"表一"、"表十二"
    ]
    
    # 处理英文表格引用
    for pattern in table_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            table_num = match.group(1)
            table_ref = f"Table {table_num}"
            if table_ref not in tables:
                tables.append(table_ref)
    
    # 处理中文表格引用
    for pattern in chinese_table_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            table_num = match.group(1)
            table_ref = f"表 {table_num}"
            if table_ref not in tables:
                tables.append(table_ref)
    
    # 英文图片模式
    figure_patterns = [
        r'Fig(?:ure)?\.?\s+([0-9]+)',
        r'Fig(?:ure)?\.?\s+([0-9]+)\s+in\s+\w+\s+appendix',
        r'Fig(?:ure)?\.?\s+(I{1,3}|IV|V|VI{1,3}|IX|X{1,3}|XI{1,3}|XI{0,1}V|XV|XVI{1,3}|XIX|XX)'  # 匹配罗马数字图片引用
    ]
    
    # 中文图片模式
    chinese_figure_patterns = [
        r'图\s*([0-9]+)',  # 匹配中文图片，如"图 1"、"图1"
        r'图\s*(I{1,3}|IV|V|VI{1,3}|IX|X{1,3}|XI{1,3}|XI{0,1}V|XV|XVI{1,3}|XIX|XX)',  # 匹配中文罗马数字图片，如"图 I"
        r'图\s*([一二三四五六七八九十]{1,2})'  # 匹配中文数字图片，如"图一"、"图十二"
    ]
    
    # 处理英文图片引用
    for pattern in figure_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            fig_num = match.group(1)
            fig_ref = f"Figure {fig_num}"
            if fig_ref not in figures:
                figures.append(fig_ref)
    
    # 处理中文图片引用
    for pattern in chinese_figure_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            fig_num = match.group(1)
            fig_ref = f"图 {fig_num}"
            if fig_ref not in figures:
                figures.append(fig_ref)
    
    # 如果提供了content_list_content，查找匹配的表格和图片
    if content_list_content:
        # 查找匹配的表格
        for table_ref in tables:
            parts = table_ref.split(" ")
            if len(parts) >= 2:
                table_prefix = parts[0]  # "Table" 或 "表"
                table_num = parts[1]     # 数字或罗马数字
                
                for item in content_list_content:
                    if item.get("type") == "table":
                        captions = item.get("table_caption", [])
                        if captions and any(is_reference_in_caption(table_num, caption, table_prefix) for caption in captions):
                            matched_item = {
                                "reference": table_ref,
                                "caption": captions,
                                "path": item.get("img_path"),
                            }
                            matched_tables.append(matched_item)
                            break
        
        # 查找匹配的图片
        for fig_ref in figures:
            parts = fig_ref.split(" ")
            if len(parts) >= 2:
                fig_prefix = parts[0]  # "Figure" 或 "图"
                fig_num = parts[1]     # 数字或罗马数字
                
                for item in content_list_content:
                    if item.get("type") == "image":
                        captions = item.get("img_caption", [])
                        if captions and any(is_reference_in_caption(fig_num, caption, fig_prefix) for caption in captions):
                            matched_item = {
                                "reference": fig_ref,
                                "caption": captions,
                                "path": item.get("img_path"),
                            }
                            matched_figures.append(matched_item)
                            break
    
    return {
        "tables": tables, 
        "figures": figures,
        "matched_tables": matched_tables,
        "matched_figures": matched_figures
    }

def is_reference_in_caption(ref_num, caption, ref_type=None):
    """
    检查引用编号是否出现在标题中（主要是":"之前的部分）
    支持中英文格式
    
    Args:
        ref_num: 引用编号，如 "1", "2.1", "I", "II", "III", "一", "二" 等
        caption: 标题字符串
        ref_type: 引用类型，如 "Table", "Figure", "表", "图" 等
    
    Returns:
        布尔值，表示是否匹配
    """
    # 获取冒号前的部分
    prefix = caption.split(':', 1)[0] if ':' in caption else caption
    
    # 检查是否为罗马数字
    is_roman = bool(re.match(r'^(I{1,3}|IV|V|VI{1,3}|IX|X{1,3}|XI{1,3}|XI{0,1}V|XV|XVI{1,3}|XIX|XX)$', ref_num))
    
    # 检查是否为中文数字
    is_chinese_num = bool(re.match(r'^[一二三四五六七八九十]{1,2}$', ref_num))
    
    # 初始化模式列表
    patterns = []
    
    # 根据引用类型添加相应的模式
    if ref_type in ["Table", "TABLE", "table"]:
        patterns = [
            rf'\bTable\s*{re.escape(ref_num)}\b',  # Table 1 或 Table I
            rf'\bTab\.\s*{re.escape(ref_num)}\b',  # Tab. 1 等
            rf'\bTab\s*{re.escape(ref_num)}\b'     # Tab 1 等
        ]
    elif ref_type in ["Figure", "FIGURE", "figure", "Fig", "FIG", "fig"]:
        patterns = [
            rf'\bFigure\s*{re.escape(ref_num)}\b',  # Figure 1
            rf'\bFig\.\s*{re.escape(ref_num)}\b',   # Fig. 1
            rf'\bFig\s*{re.escape(ref_num)}\b'      # Fig 1
        ]
    elif ref_type in ["表"]:
        patterns = [
            rf'表\s*{re.escape(ref_num)}\b'  # 表 1, 表1, 表 I, 表一
        ]
    elif ref_type in ["图"]:
        patterns = [
            rf'图\s*{re.escape(ref_num)}\b'  # 图 1, 图1, 图 I, 图一
        ]
    else:
        # 默认匹配所有类型
        patterns = [
            rf'\bTable\s*{re.escape(ref_num)}\b',  # Table 1 或 Table 2.1
            rf'\bTab\.\s*{re.escape(ref_num)}\b',  # Tab. 1 等
            rf'\bTab\s*{re.escape(ref_num)}\b',    # Tab 1 等
            rf'\bFigure\s*{re.escape(ref_num)}\b',  # Figure 1
            rf'\bFig\.\s*{re.escape(ref_num)}\b',   # Fig. 1
            rf'\bFig\s*{re.escape(ref_num)}\b',     # Fig 1
            rf'表\s*{re.escape(ref_num)}\b',       # 表 1, 表1
            rf'图\s*{re.escape(ref_num)}\b'        # 图 1, 图1
        ]
    
    # 匹配模式
    for pattern in patterns:
        if re.search(pattern, prefix, re.IGNORECASE):
            return True
    
    # 如果标题简单只包含数字，也视为匹配
    if caption.strip() == ref_num:
        return True
        
    return False

def extract_block_formulas(content):
    """只提取块级数学公式（$$..$$），忽略行内公式"""
    formulas = []
    
    block_formula_pattern = r'\$\$(.*?)\$\$'
    block_matches = re.finditer(block_formula_pattern, content, re.DOTALL)
    
    for match in block_matches:
        formula = match.group(1).strip()
        if formula and formula not in formulas:
            formulas.append(formula)
    
    return formulas

def process_markdown_file(file_content, content_list_content=None):
    """处理Markdown文件，提取标题结构及内容"""
    headings = extract_headings_with_levels_and_contents(file_content)
    headings = build_title_hierarchy(headings)
    
    for heading in headings:
        media = extract_tables_and_figures(heading["contents"], content_list_content)
        heading["tables"] = media["tables"]
        heading["figures"] = media["figures"]
        heading["matched_tables"] = media["matched_tables"]
        heading["matched_figures"] = media["matched_figures"]
        heading["formulas"] = extract_block_formulas(heading["contents"])
    
    simplified_headings = []
    for h in headings:
        simplified_headings.append({
            "title": h["title"],
            "level": h["actual_level"],
            "subtitle": h["subtitle"],
            "contents": h["contents"],
            "tables": h["tables"],
            "figures": h["figures"],
            "matched_tables": h["matched_tables"],
            "matched_figures": h["matched_figures"],
            "formulas": h["formulas"],
        })
    
    return simplified_headings

def save_json_to_file(data, filename):
    """将数据保存为JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"JSON数据已成功保存到 {filename}")
        return True
    except Exception as e:
        print(f"保存JSON文件时出错: {e}")
        return False

def replace_tables_in_markdown(md_content, content_list_content):
    """使用更灵活的匹配方式替换表格"""
    table_items = [item for item in content_list_content if item.get("type") == "table"]
    replaced_count = 0
    not_replaced = []

    for table in table_items:
        table_body = table.get("table_body", "")
        table_path = table.get("img_path", "")
        if table_body and table_path:
            caption = table.get("table_caption", ["表格"])
            
            # 清理和规范化表格内容以便更好匹配
            cleaned_table_body = re.sub(r'\s+', ' ', table_body).strip()
            
            # 创建更灵活的匹配模式 - 基于表格的特征部分
            table_start = re.escape(cleaned_table_body[:50]) if len(cleaned_table_body) > 50 else re.escape(cleaned_table_body[:len(cleaned_table_body)//2])
            table_end = re.escape(cleaned_table_body[-50:]) if len(cleaned_table_body) > 50 else re.escape(cleaned_table_body[len(cleaned_table_body)//2:])
            
            # 尝试精确匹配
            if table_body in md_content:
                md_content = md_content.replace(table_body, f"![{caption}]({table_path})")
                replaced_count += 1
            else:
                # 尝试模糊匹配
                pattern = f"{table_start}.*?{table_end}"
                match = re.search(pattern, md_content, re.DOTALL)
                if match:
                    md_content = md_content.replace(match.group(0), f"![{caption}]({table_path})")
                    replaced_count += 1
                else:
                    not_replaced.append({
                        "caption": caption,
                        "table_preview": table_body[:100] + "..." if len(table_body) > 100 else table_body
                    })
                    
    print(f"替换完成: {replaced_count}/{len(table_items)} 个表格已替换")
    if not_replaced:
        print(f"未能替换 {len(not_replaced)} 个表格")
        
    return md_content

def is_footnote_block(block, page_height):
    """
    判断文本块是否为脚注
    
    Args:
        block: 文本块数据
        page_height: 页面高度
    
    Returns:
        是否为脚注
    """
    # 获取块文本
    text = get_block_text(block)
    if not text:
        return False
    
    # 检查是否有脚注标记
    footnote_patterns = [
        r'^\s*\d+\.\s+',  # "1. "
        r'^\s*\[\d+\]\s+', # "[1] "
        r'^\s*\(\d+\)\s+', # "(1) "
        r'^\s*[*†‡§]\s+',  # "* "
    ]
    
    for pattern in footnote_patterns:
        if re.match(pattern, text):
            return True
    
    # 检查是否在页面底部
    # 脚注通常位于页面底部，可以根据y坐标判断
    if "bbox" in block:
        bbox = block.get("bbox", [0, 0, 0, 0])
        if bbox[1] > page_height * 0.8:  # 如果在页面底部80%以下
            # 检查字体大小，脚注通常字体较小
            if "font_size" in block and block["font_size"] < 10:
                return True
    
    return False

def is_header_block(block, page_height):
    """
    判断文本块是否为页眉页脚
    
    Args:
        block: 文本块数据
        page_height: 页面高度
    
    Returns:
        是否为页眉页脚
    """
    # 获取块文本
    text = get_block_text(block)
    if not text:
        return False
    
    # 检查是否在页面顶部或底部
    if "bbox" in block:
        bbox = block.get("bbox", [0, 0, 0, 0])
        
        # 页眉通常在页面顶部10%以内
        if bbox[1] < page_height * 0.1:
            return True
        
        # 页脚通常在页面底部10%以内
        if bbox[1] > page_height * 0.9:
            # 排除已识别为脚注的块
            if not is_footnote_block(block, page_height):
                return True
    
    return False

def get_block_text(block):
    """
    获取文本块中的文本
    
    Args:
        block: 文本块数据
    
    Returns:
        文本内容
    """
    # 根据MinerU中间JSON的结构获取文本
    if "text" in block:
        return block["text"]
    
    # 从lines和spans中获取文本
    if "lines" in block:
        lines_texts = []
        for line in block.get("lines", []):
            line_text = ""
            if "spans" in line:
                for span in line.get("spans", []):
                    if "text" in span:
                        line_text += span.get("text", "")
                    elif "content" in span:
                        line_text += span.get("content", "")
            lines_texts.append(line_text)
        return " ".join(lines_texts)
    
    # 尝试从spans直接获取文本
    if "spans" in block:
        spans_texts = []
        for span in block["spans"]:
            if "text" in span:
                spans_texts.append(span["text"])
            elif "content" in span:
                spans_texts.append(span["content"])
        return " ".join(spans_texts)
    
    # 尝试从content字段获取文本
    if "content" in block:
        return block["content"]
    
    return ""

def extract_footnotes_and_headers(middle_json, max_pages=None, keep_footnotes=True):
    """
    从中间JSON数据中提取脚注和页眉页脚
    
    Args:
        middle_json: 中间JSON数据
        max_pages: 最大页数限制，默认为None表示提取所有页面
        keep_footnotes: 是否保留脚注，默认为True
    
    Returns:
        包含脚注和页眉页脚的Markdown文本
    """
    result = ""
    
    # 如果middle_json是字符串，尝试解析为JSON
    if isinstance(middle_json, str):
        try:
            import json
            middle_json = json.loads(middle_json)
        except Exception as e:
            print(f"解析middle_json失败: {e}")
            return result
    
    # 获取页面数据
    pdf_info = middle_json.get("pdf_info", [])
    if not pdf_info:
        print("警告: 未找到pdf_info数据")
        return result
    
    # 限制页数
    if max_pages is not None:
        limited_pages = pdf_info[:max_pages] if len(pdf_info) > max_pages else pdf_info
    else:
        limited_pages = pdf_info
    
    # 处理每一页
    for i, page in enumerate(limited_pages):
        page_num = i + 1
        
        # 提取页面内容和脚注
        content, footnotes, headers = extract_content_footnotes_headers(page)
        
        # 添加脚注
        if footnotes and keep_footnotes:
            result += f"### 第{page_num}页脚注\n\n"
            result += footnotes + "\n\n"
        
        # 添加页眉页脚
        if headers:
            result += f"### 第{page_num}页页眉页脚\n\n"
            result += headers + "\n\n"
    
    return result

def extract_content_footnotes_headers(page):
    """
    从页面数据中提取正文内容、脚注和页眉页脚
    
    Args:
        page: 页面数据
    
    Returns:
        (正文内容, 脚注内容, 页眉页脚内容)
    """
    content = ""
    footnotes = ""
    headers = ""
    
    # 获取页面尺寸
    page_size = page.get("page_size", [0, 0])
    page_height = page_size[1] if len(page_size) > 1 else 1000
    
    # 获取预处理块和丢弃的块
    preproc_blocks = page.get("preproc_blocks", [])
    discarded_blocks = page.get("discarded_blocks", [])
    
    # 合并所有块
    all_blocks = preproc_blocks + discarded_blocks
    
    # 分离正文、脚注和页眉页脚
    main_blocks = []
    footnote_blocks = []
    header_blocks = []
    
    # 识别不同类型的块
    for block in all_blocks:
        if is_footnote_block(block, page_height):
            footnote_blocks.append(block)
        elif is_header_block(block, page_height):
            header_blocks.append(block)
        else:
            main_blocks.append(block)
    
    # 构建正文内容
    for block in main_blocks:
        block_text = get_block_text(block)
        if block_text:
            content += block_text + "\n\n"
    
    # 构建脚注内容
    for block in footnote_blocks:
        block_text = get_block_text(block)
        if block_text:
            footnotes += f"- {block_text}\n\n"
    
    # 构建页眉页脚内容
    for block in header_blocks:
        block_text = get_block_text(block)
        if block_text:
            headers += f"- {block_text}\n\n"
    
    return content.strip(), footnotes.strip(), headers.strip()

def extract_first_three_pages(middle_json):
    """
    从middle_json中提取前三页内容（包含页眉页脚）
    
    Args:
        middle_json: 中间JSON数据
        
    Returns:
        前三页内容的Markdown文本
    """
    # 如果middle_json是字符串，尝试解析为JSON
    if isinstance(middle_json, str):
        try:
            import json
            middle_json = json.loads(middle_json)
        except Exception as e:
            print(f"解析middle_json失败: {e}")
            return "无法解析middle_json"
    
    content = ""
    
    # 获取pdf_info
    pdf_info = middle_json.get("pdf_info", [])
    if not pdf_info:
        return "未找到pdf_info数据"
    
    # 限制为前三页
    max_pages = 3
    limited_pages = pdf_info[:max_pages] if len(pdf_info) > max_pages else pdf_info
    
    print(f"提取前 {len(limited_pages)} 页内容（包含页眉页脚）...")
    
    # 处理每一页
    for i, page in enumerate(limited_pages):
        page_num = i + 1
        print(f"正在提取第 {page_num} 页内容...")
        
        # 获取预处理块和丢弃的块
        preproc_blocks = page.get("preproc_blocks", [])
        discarded_blocks = page.get("discarded_blocks", [])
        
        # 合并所有块
        all_blocks = preproc_blocks + discarded_blocks
        
        # 按y坐标排序块
        sorted_blocks = sorted(all_blocks, key=lambda b: b.get("bbox", [0, 0, 0, 0])[1] if "bbox" in b else 0)
        
        # 提取每个块的文本
        for block in sorted_blocks:
            block_text = get_block_text(block)
            if block_text:
                content += block_text + "\n\n"
        
        # 添加页面分隔符
        if i < len(limited_pages) - 1:
            content += "---\n\n"
    
    return content

def process_pdf(pdf_path, output_dir=None, max_pages=None, keep_footnotes=True):
    """
    处理PDF文件，提取结构化内容并保存结果
    
    参数:
        pdf_path: PDF文件的路径
        output_dir: 输出目录，默认为"outputs/{文件名}"
        max_pages: 最大提取页数，默认为None表示提取所有页面
        keep_footnotes: 是否保留脚注，默认为True
    
    返回:
        包含提取结果的字典
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    
    # 准备文件名和输出路径
    pdf_filename = Path(pdf_path).name
    name_without_suffix = Path(pdf_path).stem
    
    # 确定输出目录
    if output_dir is None:
        output_dir = f"outputs/{name_without_suffix}"
    
    # 准备输出目录
    local_image_dir = f"{output_dir}/images"
    local_md_dir = output_dir
    image_dir = os.path.basename(local_image_dir)
    
    os.makedirs(local_image_dir, exist_ok=True)
    os.makedirs(local_md_dir, exist_ok=True)
    
    # 检查是否已存在middle_json文件
    middle_json_path = os.path.join(local_md_dir, f"{name_without_suffix}_middle.json")
    existing_middle_json = None
    
    if os.path.exists(middle_json_path):
        print(f"发现已存在的middle_json文件: {middle_json_path}")
        try:
            with open(middle_json_path, 'r', encoding='utf-8') as f:
                existing_middle_json = f.read()
            print("成功读取已存在的middle_json文件")
        except Exception as e:
            print(f"读取已存在的middle_json文件失败: {e}")
            existing_middle_json = None
    
    # 创建数据写入器
    image_writer = FileBasedDataWriter(local_image_dir)
    md_writer = FileBasedDataWriter(local_md_dir)
    
    # 如果没有找到有效的middle_json，则处理PDF
    if existing_middle_json is None:
        print("处理PDF文件...")
        # 读取PDF文件
        reader = FileBasedDataReader("")
        pdf_bytes = reader.read(pdf_path)
        
        # 处理PDF
        ds = PymuDocDataset(pdf_bytes)
        
        # 根据PDF类型选择处理方式
        if ds.classify() == SupportedPdfParseMethod.OCR:
            infer_result = ds.apply(doc_analyze, ocr=True)
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        else:
            infer_result = ds.apply(doc_analyze, ocr=False)
            pipe_result = infer_result.pipe_txt_mode(image_writer)
        
        # 获取中间JSON数据（包含完整的页面信息）
        middle_json = pipe_result.get_middle_json()
        
        # 保存中间JSON以便检查
        pipe_result.dump_middle_json(md_writer, os.path.basename(middle_json_path))
        
        # 获取Markdown内容
        md_content = pipe_result.get_markdown(image_dir, md_make_mode=MakeMode.NLP_MD)
        
        # 获取内容列表（包含表格、图片等）
        content_list_content = pipe_result.get_content_list(image_dir)
        
        # 替换表格内容
        md_content = replace_tables_in_markdown(md_content, content_list_content)
        
        # 提取脚注和页眉页脚
        footnotes_and_headers = extract_footnotes_and_headers(middle_json, max_pages, keep_footnotes)
        
        # 将脚注和页眉页脚添加到Markdown内容中
        if footnotes_and_headers:
            full_markdown = md_content + "\n\n## 脚注和页眉页脚\n\n" + footnotes_and_headers
        else:
            full_markdown = md_content
        
        # 提取前三页内容（包含页眉页脚）
        first_three_pages_markdown = extract_first_three_pages(middle_json)
        
        # 保存content_list
        content_list_path = os.path.join(local_md_dir, f"{name_without_suffix}_content_list.json")
        pipe_result.dump_content_list(md_writer, os.path.basename(content_list_path), image_dir)
    else:
        # 如果已经有middle_json，直接使用它
        print("使用已存在的middle_json文件，跳过PDF处理")
        middle_json = existing_middle_json
        
        # 检查是否已存在content_list.json文件
        content_list_path = os.path.join(local_md_dir, f"{name_without_suffix}_content_list.json")
        content_list_content = None
        if os.path.exists(content_list_path):
            try:
                import json
                with open(content_list_path, 'r', encoding='utf-8') as f:
                    content_list_content = json.load(f)
            except Exception as e:
                print(f"读取content_list.json失败: {e}")
        
        # 提取脚注和页眉页脚
        footnotes_and_headers = extract_footnotes_and_headers(middle_json, max_pages, keep_footnotes)
        
        # 提取前三页内容（包含页眉页脚）
        first_three_pages_markdown = extract_first_three_pages(middle_json)
        
        # 构建完整的Markdown内容
        full_markdown = ""
        if isinstance(middle_json, str):
            try:
                import json
                middle_json_dict = json.loads(middle_json)
                # 从middle_json提取文本内容
                for page in middle_json_dict.get("pdf_info", []):
                    for block in page.get("preproc_blocks", []):
                        text = get_block_text(block)
                        if text:
                            full_markdown += text + "\n\n"
            except Exception as e:
                print(f"解析middle_json失败: {e}")
        
        # 添加脚注和页眉页脚
        if footnotes_and_headers:
            full_markdown += "\n\n## 脚注和页眉页脚\n\n" + footnotes_and_headers
    
    # 处理middle_json，确保它是字典类型
    if isinstance(middle_json, str):
        try:
            import json
            middle_json_dict = json.loads(middle_json)
            total_pages = len(middle_json_dict.get("pdf_info", []))
        except Exception as e:
            print(f"解析middle_json失败: {e}")
            total_pages = 0
    else:
        total_pages = len(middle_json.get("pdf_info", []))
    
    # 保存提取的内容
    full_md_path = os.path.join(local_md_dir, f"{name_without_suffix}_full.md")
    with open(full_md_path, "w", encoding="utf-8") as f:
        f.write(full_markdown)
    
    first_three_pages_path = os.path.join(local_md_dir, f"{name_without_suffix}_first_three_pages.md")
    with open(first_three_pages_path, "w", encoding="utf-8") as f:
        f.write(first_three_pages_markdown)
    
    # 处理结构化数据
    try:
        # 提取标题结构和内容
        structured_data = process_markdown_file(full_markdown, content_list_content)
        
        # 保存结构化数据
        extract_result_path = os.path.join(local_md_dir, f"{name_without_suffix}_extract_result.json")
        save_json_to_file(structured_data, extract_result_path)
    except Exception as e:
        print(f"处理结构化数据时出错: {e}")
        structured_data = []
    
    result = {
        "file_name": pdf_filename,
        "total_pages": total_pages,
        "full_markdown": full_markdown,
        "first_three_pages_markdown": first_three_pages_markdown,
        "structured_data": structured_data,
        "content_list_path": content_list_path,
        "output_dir": local_md_dir
    }
    
    return result

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="增强版PDF结构化内容提取工具")
    parser.add_argument("pdf_path", help="PDF文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径，不指定则使用PDF文件名")
    parser.add_argument("--output-dir", "-d", help="输出目录，不指定则创建临时目录")
    parser.add_argument("--pages", "-p", type=int, default=None, help="提取的最大页数，默认为所有页面")
    parser.add_argument("--no-footnotes", action="store_true", help="不提取脚注")
    
    args = parser.parse_args()
    
    # 检查PDF文件是否存在
    if not os.path.exists(args.pdf_path):
        print(f"错误: PDF文件不存在: {args.pdf_path}")
        sys.exit(1)
    
    # 确定输出路径
    if args.output:
        output_base = args.output
    else:
        output_base = os.path.splitext(args.pdf_path)[0] + "_content"
    
    # 创建输出目录（如果需要）
    output_dir = args.output_dir
    if not output_dir:
        output_dir = os.path.dirname(output_base)
        if not output_dir:
            output_dir = f"output_{Path(args.pdf_path).stem}"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"正在处理: {args.pdf_path}")
    if args.pages:
        print(f"提取前 {args.pages} 页内容...")
    else:
        print("提取所有页面内容...")
    
    # 提取数据
    try:
        data = process_pdf(
            pdf_path=args.pdf_path,
            output_dir=output_dir,
            max_pages=args.pages,
            keep_footnotes=not args.no_footnotes
        )
        
        # 打印基本信息
        print("\n提取结果:")
        print(f"文件名: {data['file_name']}")
        print(f"总页数: {data['total_pages']}")
        print(f"输出目录: {data['output_dir']}")
        print(f"全文Markdown: {os.path.join(data['output_dir'], Path(data['file_name']).stem + '_full.md')}")
        print(f"前三页Markdown: {os.path.join(data['output_dir'], Path(data['file_name']).stem + '_first_three_pages.md')}")
        
        # 如果有结构化数据，打印标题数量
        if data.get("structured_data"):
            print(f"提取的标题数量: {len(data['structured_data'])}")
        
    except Exception as e:
        print(f"处理过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n处理完成!")

if __name__ == "__main__":
    main()