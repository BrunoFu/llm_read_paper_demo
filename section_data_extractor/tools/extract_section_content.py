import json
import os
import sys
import re
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
        print(f"{Fore.RED}读取文件时出错: {e}")
        return None

def extract_section_contents(flattened_data, md_lines):
    """从Markdown文件中提取各节的内容"""
    section_contents = []
    
    for item in flattened_data:
        title = item.get("title", "")
        line_number = item.get("line_number")
        next_line_number = item.get("next_line_number")
        level = item.get("level", 0)
        
        if line_number is None:
            print(f"{Fore.YELLOW}跳过没有行号的标题: {title}")
            continue
        
        # 确定内容的结束行
        end_line = next_line_number if next_line_number is not None else len(md_lines)
        
        # 提取内容（排除标题行）
        content_lines = md_lines[line_number+1:end_line]
        content = "".join(content_lines).strip()
        
        # 移除内容中的Markdown标题标记
        content = re.sub(r'^#+\s+.*$', '', content, flags=re.MULTILINE)
        
        # 创建节内容对象
        section = {
            "title": title,
            "level": level,
            "line_number": line_number,
            "next_line_number": next_line_number,
            "content": content,
            "figures": item.get("figures", []),
            "tables": item.get("tables", [])
        }
        
        section_contents.append(section)
    
    return section_contents

def save_section_contents(section_contents, output_path):
    """保存节内容到JSON文件"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(section_contents, f, ensure_ascii=False, indent=2)
        print(f"{Fore.GREEN}已成功保存节内容到 '{output_path}'")
        return True
    except Exception as e:
        print(f"{Fore.RED}保存节内容时出错: {e}")
        return False

def save_individual_sections(section_contents, output_dir):
    """将每个节保存为单独的文件"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        for i, section in enumerate(section_contents):
            title = section.get("title", "").replace("/", "-").replace("\\", "-")
            level = section.get("level", 0)
            
            # 创建文件名
            file_name = f"{i+1:02d}_level{level}_{title[:30]}.md"
            file_path = os.path.join(output_dir, file_name)
            
            # 准备内容
            content = f"# {title}\n\n{section.get('content', '')}"
            
            # 添加图表引用信息
            figures = section.get("figures", [])
            tables = section.get("tables", [])
            
            if figures:
                content += "\n\n## 图片引用\n"
                for fig in figures:
                    content += f"- {fig}\n"
            
            if tables:
                content += "\n\n## 表格引用\n"
                for table in tables:
                    content += f"- {table}\n"
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"{Fore.GREEN}已成功将各节内容保存到目录 '{output_dir}'")
        return True
    except Exception as e:
        print(f"{Fore.RED}保存单独节文件时出错: {e}")
        return False

def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # 输入和输出文件路径
    flattened_json_path = os.path.join(script_dir, "flattened_structure.json")
    md_file_path = os.path.join(parent_dir, "AER202501_8_gruber-et-al-2025-dying-or-lying-for-profit-hospices-and-end-of-life-care_full.md")
    output_json_path = os.path.join(script_dir, "section_contents.json")
    output_sections_dir = os.path.join(script_dir, "sections")
    
    # 加载展平结构
    flattened_data = load_json_file(flattened_json_path)
    
    if not flattened_data:
        print(f"{Fore.RED}无法加载展平结构文件，请先运行 flatten_structure.py")
        return
    
    # 加载Markdown文件
    md_lines = load_markdown_file(md_file_path)
    
    if not md_lines:
        print(f"{Fore.RED}无法加载Markdown文件")
        return
    
    # 提取节内容
    section_contents = extract_section_contents(flattened_data, md_lines)
    
    # 保存节内容到JSON文件
    save_section_contents(section_contents, output_json_path)
    
    # 保存各节为单独文件
    save_individual_sections(section_contents, output_sections_dir)
    
    # 打印统计信息
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}内容提取统计")
    print(f"{Fore.CYAN}{'='*80}")
    print(f"总节数: {len(section_contents)}")
    
    # 统计每个级别的节数量
    level_counts = {}
    for section in section_contents:
        level = section.get("level", 0)
        level_counts[level] = level_counts.get(level, 0) + 1
    
    for level, count in sorted(level_counts.items()):
        print(f"级别 {level} 的节: {count}")
    
    # 统计内容长度
    total_content_length = sum(len(section.get("content", "")) for section in section_contents)
    avg_content_length = total_content_length / len(section_contents) if section_contents else 0
    
    print(f"总内容长度: {total_content_length} 字符")
    print(f"平均节长度: {avg_content_length:.1f} 字符")
    print(f"{Fore.CYAN}{'='*80}\n")

if __name__ == "__main__":
    main() 