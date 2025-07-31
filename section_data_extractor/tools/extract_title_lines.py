import json
import re
import os
import difflib
import sys

def load_json_structure(json_path):
    """从文件加载JSON结构"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"文件不存在: {json_path}")
        return None
    except json.JSONDecodeError:
        print("JSON格式错误，请检查输入文件")
        return None
    except Exception as e:
        print(f"读取JSON文件时出错: {e}")
        return None

def load_markdown_file(file_path):
    """加载Markdown文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        return lines
    except FileNotFoundError:
        print(f"文件不存在: {file_path}")
        return None
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

def identify_footnote_section(md_lines):
    """识别脚注区域的开始行号"""
    footnote_indicators = [
        "## 参考文献", "## References", "# 参考文献", "# References",
        "## 脚注", "## Footnotes", "# 脚注", "# Footnotes",
        "## 附录", "## Appendix", "# 附录", "# Appendix"
    ]
    
    for i, line in enumerate(md_lines):
        line_lower = line.strip().lower()
        if any(indicator.lower() in line_lower for indicator in footnote_indicators):
            # 返回下一行，而不是References标题行本身
            return i + 1
    
    # 如果没有明确的脚注标记，可以尝试识别参考文献的模式
    for i, line in enumerate(md_lines):
        if re.match(r'^[\[\(]?\d+[\]\)]?\s+\w+', line.strip()):  # 匹配类似 [1] Author 或 (1) Author 的格式
            consecutive_refs = 0
            for j in range(i, min(i+5, len(md_lines))):
                if re.match(r'^[\[\(]?\d+[\]\)]?\s+\w+', md_lines[j].strip()):
                    consecutive_refs += 1
            
            if consecutive_refs >= 3:  # 如果连续3行都是参考文献格式，认为这是参考文献区域
                return i
    
    return len(md_lines)  # 如果没找到，返回文件末尾

def extract_sentences(text, num_sentences=2):
    """
    从文本中提取句子
    """
    # 使用正则表达式分割句子（按.!?分割）
    sentences = re.split(r'[.!?]', text)
    # 过滤空句子并限制数量
    sentences = [s.strip() for s in sentences if s.strip()][:num_sentences]
    return sentences

def find_title_line_number_robust(title, md_lines, start_line, end_line):
    """更鲁棒的标题行号查找方法，使用句子级模糊匹配"""
    title_clean = title.strip()
    
    # 1. 优先匹配Markdown标题格式（考虑不同级别的标题）
    for i in range(start_line, min(end_line, len(md_lines))):
        line = md_lines[i].strip()
        # 匹配任何级别的Markdown标题
        if re.match(r'^#+\s+', line):
            # 提取标题文本，去除#号
            title_part = re.sub(r'^#+\s+', '', line).strip()
            
            # 使用模糊匹配比较标题文本
            ratio = difflib.SequenceMatcher(None, title_clean.lower(), title_part.lower()).ratio()
            if ratio > 0.8:  # 如果相似度高于阈值
                print(f"找到标题匹配 (Markdown格式): '{title_clean}' 在行 {i}, 相似度: {ratio:.2f}")
                print(f"匹配内容: {line}")
                return i
            
            # 特殊处理：如果标题只是"Abstract"或"Introduction"等常见标题
            common_titles = ["abstract", "introduction", "conclusion", "references", "appendix"]
            if title_clean.lower() in common_titles and title_clean.lower() in title_part.lower():
                print(f"找到常见标题匹配: '{title_clean}' 在行 {i}")
                print(f"匹配内容: {line}")
                return i
    
    # 2. 使用句子级模糊匹配
    # 从标题中提取句子
    title_sentences = extract_sentences(title_clean)
    
    best_overall_ratio = 0
    best_match = None
    
    for i in range(start_line, min(end_line, len(md_lines))):
        line = md_lines[i].strip()
        
        # 跳过空行
        if not line:
            continue
        
        # 从行中提取句子
        line_sentences = extract_sentences(line)
        if not line_sentences:
            continue
        
        # 计算每个句子与目标句子的最佳匹配度
        sentence_ratios = []
        for target_sent in title_sentences:
            best_sent_ratio = 0
            for line_sent in line_sentences:
                ratio = difflib.SequenceMatcher(None, target_sent.lower(), line_sent.lower()).ratio()
                best_sent_ratio = max(best_sent_ratio, ratio)
            if best_sent_ratio > 0:  # 只考虑有匹配的句子
                sentence_ratios.append(best_sent_ratio)
        
        # 计算整体匹配度（句子匹配度的平均值）
        if sentence_ratios:
            overall_ratio = sum(sentence_ratios) / len(sentence_ratios)
            if overall_ratio > best_overall_ratio:
                best_overall_ratio = overall_ratio
                best_match = i
    
    # 如果找到足够相似的行
    if best_overall_ratio >= 0.7:
        print(f"找到标题匹配 (句子级): '{title_clean}' 在行 {best_match}, 相似度: {best_overall_ratio:.2f}")
        print(f"匹配内容: {md_lines[best_match].strip()}")
        return best_match
    
    # 3. 回退到原始的模糊匹配方法
    best_match = None
    best_ratio = 0
    
    for i in range(start_line, min(end_line, len(md_lines))):
        line_clean = re.sub(r'[^\w\s]', '', md_lines[i].strip().lower())
        title_clean_for_fuzzy = re.sub(r'[^\w\s]', '', title_clean.lower())
        
        ratio = difflib.SequenceMatcher(None, title_clean_for_fuzzy, line_clean).ratio()
        
        # 对于标题，更看重开头的匹配
        if len(title_clean_for_fuzzy) > 5 and len(line_clean) > 5:
            prefix_ratio = difflib.SequenceMatcher(None, title_clean_for_fuzzy[:5], line_clean[:5]).ratio()
            ratio = (ratio + prefix_ratio) / 2
        
        if ratio > best_ratio and ratio > 0.6:  # 降低相似度阈值以增加匹配机会
            best_ratio = ratio
            best_match = i
    
    if best_match is not None:
        print(f"找到标题匹配 (模糊): '{title_clean}' 在行 {best_match}, 相似度: {best_ratio:.2f}")
        print(f"匹配内容: {md_lines[best_match].strip()}")
    else:
        print(f"未找到标题匹配: '{title_clean}'")
    
    return best_match

def find_next_title_of_same_level(level, current_line, sorted_items, md_lines):
    """查找同级别的下一个标题行号"""
    if current_line is None:
        return None
    
    next_line = None
    
    for item in sorted_items:
        item_level = item.get("level", 0)
        item_line = find_title_line_number_robust(item.get("title", ""), md_lines, 0, len(md_lines))
        
        if item_level == level and item_line is not None and item_line > current_line:
            if next_line is None or item_line < next_line:
                next_line = item_line
    
    return next_line

def extract_title_line_numbers(structure, md_lines):
    """提取标题对应的行号，基于Markdown格式和层级关系"""
    result = []
    
    # 识别脚注区域的开始行号
    footnote_start_line = identify_footnote_section(md_lines)
    # 文件末尾行号
    file_end_line = len(md_lines)
    print(f"脚注区域开始行号: {footnote_start_line}")
    print(f"文件末尾行号: {file_end_line}")
    
    # 首先按层级排序处理标题
    sorted_items = sorted(structure, key=lambda x: x.get("level", 0))
    
    # 为每个层级创建一个字典，记录该层级上一个找到的标题行号
    last_found_line_by_level = {0: -1, 1: -1, 2: -1, 3: -1}
    
    # 首先找到level=0的标题行号
    level0_items = [item for item in sorted_items if item.get("level") == 0]
    for item in level0_items:
        title = item.get("title", "")
        line_number = find_title_line_number_robust(title, md_lines, 0, file_end_line)
        if line_number is not None:
            last_found_line_by_level[0] = line_number
            print(f"找到level=0标题 '{title}' 在行 {line_number}")
    
    # 创建标题到行号的映射，用于优化搜索
    title_to_line = {}
    
    # 然后处理所有标题
    for item in sorted_items:
        title = item.get("title", "")
        level = item.get("level", 0)
        sub_level = item.get("sub_level")
        sub_title_list = item.get("sub_title_list", [])
        
        print(f"\n处理标题: '{title}' (级别: {level})")
        
        # 确定搜索范围
        if level == 0:
            # 对于level=0的标题，我们已经找到了行号，直接跳过
            search_start = 0
            search_end = file_end_line
            line_number = last_found_line_by_level[0]
        else:
            # 对于其他级别的标题，设定合适的搜索范围
            
            # 从上一个找到的标题之后开始搜索
            search_start = 0
            
            # 特殊处理References标题
            if title.lower() == "references":
                # 对于References标题，从最后一个找到的标题之后开始搜索，直到文件末尾
                last_found_lines = [line for line in last_found_line_by_level.values() if line >= 0]
                if last_found_lines:
                    search_start = max(last_found_lines) + 1
                search_end = file_end_line
                print(f"特殊处理References标题，搜索范围: 行 {search_start} 到 行 {search_end}")
            else:
                # 对于其他标题，使用顺序搜索策略
                # 如果有上一个同级别的标题，从它之后开始搜索
                if level in last_found_line_by_level and last_found_line_by_level[level] >= 0:
                    search_start = last_found_line_by_level[level] + 1
                # 如果有更高级别的标题，从它之后开始搜索
                elif level > 0 and last_found_line_by_level[level-1] >= 0:
                    search_start = last_found_line_by_level[level-1] + 1
                
                search_end = file_end_line
            
            print(f"搜索范围: 行 {search_start} 到 行 {search_end}")
            
            # 查找主标题行号
            line_number = find_title_line_number_robust(title, md_lines, search_start, search_end)
            
            if line_number is not None:
                last_found_line_by_level[level] = line_number
                title_to_line[title] = line_number
                print(f"标题 '{title}' 找到在行 {line_number}")
            else:
                print(f"警告: 标题 '{title}' 未找到行号")
        
        new_item = {
            "title": title,
            "level": level,
            "sub_level": sub_level,
            "line_number": line_number,
            "sub_title_list": []
        }
        
        # 处理子标题，子标题应该在当前标题之后，下一个同级标题之前
        next_title_line = find_next_title_of_same_level(level, line_number, sorted_items, md_lines)
        sub_search_end = next_title_line if next_title_line else file_end_line
        
        if sub_title_list:
            print(f"处理 {len(sub_title_list)} 个子标题")
            
        for sub_title in sub_title_list:
            # 检查子标题是字典还是字符串
            if isinstance(sub_title, dict):
                sub_title_text = sub_title.get("title", "")
                print(f"  处理子标题(字典): '{sub_title_text}'")
            else:
                sub_title_text = sub_title  # 如果是字符串，直接使用
                print(f"  处理子标题(字符串): '{sub_title_text}'")
            
            sub_search_start = line_number + 1 if line_number is not None else search_start
            print(f"  子标题搜索范围: 行 {sub_search_start} 到 行 {sub_search_end}")
            
            sub_line_number = find_title_line_number_robust(
                sub_title_text, 
                md_lines, 
                sub_search_start, 
                sub_search_end
            )
            
            if sub_line_number is not None:
                print(f"  子标题 '{sub_title_text}' 找到在行 {sub_line_number}")
            else:
                print(f"  警告: 子标题 '{sub_title_text}' 未找到行号")
            
            # 添加到结果中，保持与原始子标题相同的格式
            if isinstance(sub_title, dict):
                sub_item = sub_title.copy()
                sub_item["line_number"] = sub_line_number
                new_item["sub_title_list"].append(sub_item)
            else:
                new_item["sub_title_list"].append({
                    "title": sub_title_text,
                    "line_number": sub_line_number
                })
        
        result.append(new_item)
    
    return result

def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取父目录
    parent_dir = os.path.dirname(script_dir)
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="提取标题对应的行号")
    parser.add_argument("--md_file", help="Markdown文件路径", default=None)
    parser.add_argument("--input_json", help="输入JSON文件路径", default="input.json")
    parser.add_argument("--output_json", help="输出JSON文件路径", default="input_with_row_num.json")
    parser.add_argument("--verbose", help="显示详细信息", action="store_true")
    args = parser.parse_args()
    
    # 设置默认Markdown文件路径
    if args.md_file:
        md_file_path = args.md_file if os.path.isabs(args.md_file) else os.path.join(parent_dir, args.md_file)
    else:
        # 尝试查找当前目录下的markdown文件
        md_files = [f for f in os.listdir(parent_dir) if f.endswith('.md')]
        if md_files:
            md_file_path = os.path.join(parent_dir, md_files[0])
            print(f"自动选择Markdown文件: {md_files[0]}")
        else:
            md_file_path = os.path.join(parent_dir, "AER202501_8_gruber-et-al-2025-dying-or-lying-for-profit-hospices-and-end-of-life-care_full.md")
    
    # 输入和输出文件路径
    input_json_path = os.path.join(script_dir, args.input_json)
    output_json_path = os.path.join(script_dir, args.output_json)
    
    print(f"使用Markdown文件: {md_file_path}")
    print(f"输入JSON文件: {input_json_path}")
    print(f"输出JSON文件: {output_json_path}")
    
    # 加载JSON结构
    structure = load_json_structure(input_json_path)
    
    if structure is None:
        return
    
    # 加载markdown文件
    md_lines = load_markdown_file(md_file_path)
    
    if md_lines is None:
        return
    
    # 提取标题行号
    result = extract_title_line_numbers(structure, md_lines)
    
    # 保存结果到文件
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"已将提取的行号添加到JSON中并保存为 '{output_json_path}'")
    
    # 统计找到行号的标题数量
    found_count = 0
    total_count = 0
    
    for item in result:
        total_count += 1
        if item["line_number"] is not None:
            found_count += 1
        
        for sub_item in item.get("sub_title_list", []):
            total_count += 1
            if sub_item.get("line_number") is not None:
                found_count += 1
    
    print(f"总共 {total_count} 个标题，成功找到 {found_count} 个标题的行号 ({found_count/total_count*100:.1f}%)")

if __name__ == "__main__":
    main() 