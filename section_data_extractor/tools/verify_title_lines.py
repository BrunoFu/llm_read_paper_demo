import json
import os
import sys
import re
import difflib
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

def load_json_structure(json_path):
    """从文件加载JSON结构"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Fore.RED}文件不存在: {json_path}")
        return None
    except json.JSONDecodeError:
        print(f"{Fore.RED}JSON格式错误，请检查输入文件")
        return None
    except Exception as e:
        print(f"{Fore.RED}读取JSON文件时出错: {e}")
        return None

def load_markdown_file(file_path):
    """加载Markdown文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        return lines
    except FileNotFoundError:
        print(f"{Fore.RED}文件不存在: {file_path}")
        return None
    except Exception as e:
        print(f"{Fore.RED}读取文件时出错: {e}")
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
            return i
    
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

def verify_title_lines(structure, md_lines):
    """验证标题行号并显示对应内容"""
    result = []
    footnote_start_line = identify_footnote_section(md_lines)
    
    # 首先按层级排序处理标题
    sorted_items = sorted(structure, key=lambda x: x.get("level", 0))
    
    for item in sorted_items:
        title = item.get("title", "")
        level = item.get("level", 0)
        sub_level = item.get("sub_level")
        line_number = item.get("line_number")
        sub_title_list = item.get("sub_title_list", [])
        
        # 验证主标题
        line_content = get_line_content(line_number, md_lines)
        match_quality = evaluate_match_quality(title, line_content)
        
        # 检查是否在脚注区域
        if line_number is not None and line_number >= footnote_start_line:
            match_quality = f"警告: 可能在脚注区域 ({match_quality})"
        
        new_item = {
            "title": title,
            "level": level,
            "sub_level": sub_level,
            "line_number": line_number,
            "line_content": line_content,
            "match_quality": match_quality,
            "sub_title_list": []
        }
        
        # 验证子标题
        for sub_item in sub_title_list:
            sub_title = sub_item.get("title", "")
            sub_line_number = sub_item.get("line_number")
            sub_line_content = get_line_content(sub_line_number, md_lines)
            sub_match_quality = evaluate_match_quality(sub_title, sub_line_content)
            
            # 检查子标题是否在脚注区域
            if sub_line_number is not None and sub_line_number >= footnote_start_line:
                sub_match_quality = f"警告: 可能在脚注区域 ({sub_match_quality})"
            
            # 检查子标题是否在主标题之后
            if line_number is not None and sub_line_number is not None and sub_line_number <= line_number:
                sub_match_quality = f"警告: 子标题在主标题之前 ({sub_match_quality})"
            
            new_item["sub_title_list"].append({
                "title": sub_title,
                "line_number": sub_line_number,
                "line_content": sub_line_content,
                "match_quality": sub_match_quality
            })
        
        result.append(new_item)
    
    return result

def get_line_content(line_number, md_lines):
    """获取指定行号的内容"""
    if line_number is None:
        return "未找到匹配行"
    
    try:
        # 行号从0开始，直接使用作为索引
        return md_lines[line_number].strip()
    except IndexError:
        return f"行号超出范围: {line_number}"

def evaluate_match_quality(title, line_content):
    """评估标题与行内容的匹配质量"""
    if "未找到匹配行" in line_content or "行号超出范围" in line_content:
        return "无匹配"
    
    title_clean = title.strip().lower()
    line_clean = line_content.strip().lower()
    
    # 检查是否为Markdown标题格式
    is_markdown_heading = line_clean.startswith('#')
    markdown_prefix = ""
    if is_markdown_heading:
        markdown_prefix = "Markdown标题: "
    
    if title_clean == line_clean:
        return f"{markdown_prefix}精确匹配"
    elif title_clean in line_clean:
        # 如果是Markdown标题，检查标题部分是否匹配
        if is_markdown_heading:
            title_part = line_clean.split('#', 1)[1].strip()
            if title_clean in title_part:
                return f"{markdown_prefix}标题部分包含匹配"
        return f"{markdown_prefix}包含匹配"
    else:
        # 计算相似度
        ratio = difflib.SequenceMatcher(None, title_clean, line_clean).ratio()
        if ratio > 0.8:
            return f"{markdown_prefix}高相似度匹配 ({ratio:.2f})"
        elif ratio > 0.6:
            return f"{markdown_prefix}中相似度匹配 ({ratio:.2f})"
        else:
            return f"{markdown_prefix}低相似度匹配 ({ratio:.2f})"

def print_verification_results(result):
    """以友好的方式打印验证结果"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}标题匹配验证结果")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    for item in result:
        title = item["title"]
        level = item["level"]
        line_number = item["line_number"]
        line_content = item["line_content"]
        match_quality = item["match_quality"]
        
        # 根据匹配质量选择颜色
        color = Fore.GREEN
        if "无匹配" in match_quality:
            color = Fore.RED
        elif "低相似度" in match_quality:
            color = Fore.YELLOW
        elif "警告" in match_quality:
            color = Fore.RED
        
        print(f"{Fore.BLUE}[主标题 - 级别{level}] {title}")
        print(f"  行号: {line_number}")
        print(f"  内容: {color}{line_content}")
        print(f"  匹配质量: {color}{match_quality}\n")
        
        # 打印子标题
        for sub_item in item["sub_title_list"]:
            sub_title = sub_item["title"]
            sub_line_number = sub_item["line_number"]
            sub_line_content = sub_item["line_content"]
            sub_match_quality = sub_item["match_quality"]
            
            # 根据匹配质量选择颜色
            sub_color = Fore.GREEN
            if "无匹配" in sub_match_quality:
                sub_color = Fore.RED
            elif "低相似度" in sub_match_quality:
                sub_color = Fore.YELLOW
            elif "警告" in sub_match_quality:
                sub_color = Fore.RED
            
            print(f"{Fore.MAGENTA}  [子标题] {sub_title}")
            print(f"    行号: {sub_line_number}")
            print(f"    内容: {sub_color}{sub_line_content}")
            print(f"    匹配质量: {sub_color}{sub_match_quality}\n")
    
    # 统计匹配情况
    total_titles = len(result)
    total_subtitles = sum(len(item["sub_title_list"]) for item in result)
    
    exact_matches = sum(1 for item in result if "精确匹配" in item["match_quality"])
    exact_sub_matches = sum(1 for item in result for sub_item in item["sub_title_list"] if "精确匹配" in sub_item["match_quality"])
    
    no_matches = sum(1 for item in result if "无匹配" in item["match_quality"])
    no_sub_matches = sum(1 for item in result for sub_item in item["sub_title_list"] if "无匹配" in sub_item["match_quality"])
    
    warning_matches = sum(1 for item in result if "警告" in item["match_quality"])
    warning_sub_matches = sum(1 for item in result for sub_item in item["sub_title_list"] if "警告" in sub_item["match_quality"])
    
    print(f"{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}匹配统计")
    print(f"{Fore.CYAN}{'='*80}")
    print(f"主标题总数: {total_titles}")
    print(f"子标题总数: {total_subtitles}")
    print(f"主标题精确匹配: {exact_matches}/{total_titles} ({exact_matches/total_titles*100:.1f}%)")
    
    # 修复f字符串语法错误
    if total_subtitles > 0:
        sub_match_percent = exact_sub_matches/total_subtitles*100
    else:
        sub_match_percent = 0
    print(f"子标题精确匹配: {exact_sub_matches}/{total_subtitles} ({sub_match_percent:.1f}%)")
    
    print(f"主标题无匹配: {no_matches}/{total_titles} ({no_matches/total_titles*100:.1f}%)")
    
    # 修复f字符串语法错误
    if total_subtitles > 0:
        sub_no_match_percent = no_sub_matches/total_subtitles*100
    else:
        sub_no_match_percent = 0
    print(f"子标题无匹配: {no_sub_matches}/{total_subtitles} ({sub_no_match_percent:.1f}%)")
    
    # 添加警告统计
    print(f"主标题有警告: {warning_matches}/{total_titles} ({warning_matches/total_titles*100:.1f}%)")
    if total_subtitles > 0:
        sub_warning_percent = warning_sub_matches/total_subtitles*100
    else:
        sub_warning_percent = 0
    print(f"子标题有警告: {warning_sub_matches}/{total_subtitles} ({sub_warning_percent:.1f}%)")
    
    print(f"{Fore.CYAN}{'='*80}\n")

def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取父目录
    parent_dir = os.path.dirname(script_dir)
    # 构建markdown文件路径
    md_file_path = os.path.join(parent_dir, "AER202501_8_gruber-et-al-2025-dying-or-lying-for-profit-hospices-and-end-of-life-care_full.md")
    
    # 输入和输出文件路径
    input_json_path = os.path.join(script_dir, "input_with_row_num.json")
    output_json_path = os.path.join(script_dir, "verified_titles.json")
    
    print(f"{Fore.CYAN}正在从 '{input_json_path}' 读取数据...")
    
    # 加载JSON结构
    structure = load_json_structure(input_json_path)
    
    if structure is None:
        return
    
    # 加载markdown文件
    md_lines = load_markdown_file(md_file_path)
    
    if md_lines is None:
        return
    
    # 验证标题行号
    result = verify_title_lines(structure, md_lines)
    
    # 输出友好的验证结果
    print_verification_results(result)
    
    # 保存结果到文件
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"{Fore.GREEN}已将验证结果保存为 '{output_json_path}'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}程序已被用户中断")
    except Exception as e:
        print(f"\n{Fore.RED}发生错误: {e}") 