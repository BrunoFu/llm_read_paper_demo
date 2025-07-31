import json
import os
import sys
import argparse
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
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.readlines()
    except Exception as e:
        print(f"{Fore.RED}读取Markdown文件时出错: {e}")
        return None

def add_text_content(structure_data, md_lines):
    """为结构数据添加文本内容"""
    for item in structure_data:
        line_number = item.get("line_number")
        next_line_number = item.get("next_line_number")
        
        if line_number is None:
            print(f"{Fore.YELLOW}警告: 标题 '{item.get('title')}' 没有行号，跳过")
            item["text_content"] = ""
            continue
        
        # 确定内容的结束行
        end_line = next_line_number if next_line_number is not None else len(md_lines)
        
        # 提取内容（包含标题行但不包含下一个标题行）
        content_lines = md_lines[line_number:end_line]
        content = "".join(content_lines)
        
        # 添加到结构中
        item["text_content"] = content
    
    return structure_data

def save_json_file(data, file_path):
    """保存JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"{Fore.GREEN}已成功保存数据到 '{file_path}'")
        return True
    except Exception as e:
        print(f"{Fore.RED}保存JSON文件时出错: {e}")
        return False

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="为结构化数据添加文本内容")
    parser.add_argument("--structure", help="结构化JSON文件路径", default="flattened_structure.json")
    parser.add_argument("--markdown", help="Markdown文件路径")
    parser.add_argument("--output", help="输出文件路径", default="structure_with_content.json")
    
    args = parser.parse_args()
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # 设置默认文件路径
    structure_path = os.path.join(script_dir, args.structure) if not os.path.isabs(args.structure) else args.structure
    
    # 如果未提供Markdown路径，使用默认路径
    if args.markdown:
        markdown_path = args.markdown if os.path.isabs(args.markdown) else os.path.join(parent_dir, args.markdown)
    else:
        # 尝试从extract_section_content.py中获取Markdown文件路径
        try:
            with open(os.path.join(script_dir, "extract_section_content.py"), 'r', encoding='utf-8') as f:
                content = f.read()
                import re
                md_path_match = re.search(r'md_file_path\s*=\s*["\']([^"\']+)["\']', content)
                if md_path_match:
                    markdown_path = md_path_match.group(1)
                else:
                    # 使用默认值
                    markdown_path = os.path.join(parent_dir, "AER202501_8_gruber-et-al-2025-dying-or-lying-for-profit-hospices-and-end-of-life-care_full.md")
        except:
            # 使用默认值
            markdown_path = os.path.join(parent_dir, "AER202501_8_gruber-et-al-2025-dying-or-lying-for-profit-hospices-and-end-of-life-care_full.md")
    
    output_path = os.path.join(script_dir, args.output) if not os.path.isabs(args.output) else args.output
    
    print(f"{Fore.CYAN}使用以下文件:")
    print(f"  结构文件: {structure_path}")
    print(f"  Markdown文件: {markdown_path}")
    print(f"  输出文件: {output_path}")
    
    # 加载结构化数据
    structure_data = load_json_file(structure_path)
    if not structure_data:
        print(f"{Fore.RED}无法加载结构化数据，请检查文件路径")
        return False
    
    # 加载Markdown文件
    md_lines = load_markdown_file(markdown_path)
    if not md_lines:
        print(f"{Fore.RED}无法加载Markdown文件，请检查文件路径")
        return False
    
    # 添加文本内容
    updated_data = add_text_content(structure_data, md_lines)
    
    # 保存更新后的数据
    success = save_json_file(updated_data, output_path)
    
    if success:
        # 统计信息
        total_items = len(updated_data)
        items_with_content = sum(1 for item in updated_data if item.get("text_content", "").strip())
        total_content_length = sum(len(item.get("text_content", "")) for item in updated_data)
        
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}内容添加统计")
        print(f"{Fore.CYAN}{'='*80}")
        print(f"总条目数: {total_items}")
        print(f"有内容的条目数: {items_with_content}")
        print(f"内容总长度: {total_content_length} 字符")
        
        if total_items > 0:
            print(f"平均内容长度: {total_content_length / total_items:.1f} 字符/条目")
        
        print(f"{Fore.CYAN}{'='*80}\n")
        
        print(f"{Fore.GREEN}已成功添加文本内容并保存")
        return True
    else:
        print(f"{Fore.RED}添加文本内容失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 