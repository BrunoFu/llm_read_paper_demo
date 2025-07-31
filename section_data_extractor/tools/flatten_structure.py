import json
import os
import sys

def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载JSON文件时出错: {e}")
        return None

def merge_and_flatten_structure(structure_data, row_num_data):
    """合并两个JSON文件的数据并展平结构"""
    # 创建主标题和子标题的映射
    title_to_content = {}
    
    # 首先处理主标题的内容
    for item in structure_data:
        title = item.get("title", "")
        title_to_content[title] = {
            "level": item.get("level", 0),
            "sub_level": item.get("sub_level"),
            "sub_title_list": item.get("sub_title_list", []),
            "figures": item.get("figures", []),
            "tables": item.get("tables", [])
        }
    
    # 创建行号映射
    title_to_line_number = {}
    for item in row_num_data:
        title = item.get("title", "")
        title_to_line_number[title] = item.get("line_number")
        
        # 处理子标题的行号
        for sub_item in item.get("sub_title_list", []):
            sub_title = sub_item.get("title", "")
            sub_line_number = sub_item.get("line_number")
            title_to_line_number[sub_title] = sub_line_number
    
    # 创建所有标题的列表（主标题和子标题）
    all_titles = []
    
    # 添加主标题
    for item in structure_data:
        title = item.get("title", "")
        level = item.get("level", 0)
        sub_level = item.get("sub_level")
        sub_title_list = []
        
        # 复制子标题列表，但只保留title和line_number
        for sub_title in item.get("sub_title_list", []):
            if isinstance(sub_title, dict):
                sub_title_list.append({
                    "title": sub_title.get("title", ""),
                    "line_number": title_to_line_number.get(sub_title.get("title", ""))
                })
            else:
                sub_title_list.append({
                    "title": sub_title,
                    "line_number": title_to_line_number.get(sub_title)
                })
        
        # 提取主标题级别的图表（不属于任何子标题的）
        main_figures = []
        main_tables = []
        
        for fig_group in item.get("figures", []):
            if isinstance(fig_group, dict):
                # 跳过子标题特定的图表
                continue
            elif isinstance(fig_group, list) or isinstance(fig_group, str):
                # 添加主标题级别的图表
                if isinstance(fig_group, list):
                    main_figures.extend(fig_group)
                else:
                    main_figures.append(fig_group)
        
        for table_group in item.get("tables", []):
            if isinstance(table_group, dict):
                # 跳过子标题特定的表格
                continue
            elif isinstance(table_group, list) or isinstance(table_group, str):
                # 添加主标题级别的表格
                if isinstance(table_group, list):
                    main_tables.extend(table_group)
                else:
                    main_tables.append(table_group)
        
        all_titles.append({
            "title": title,
            "level": level,
            "sub_level": sub_level,
            "line_number": title_to_line_number.get(title),
            "sub_title_list": sub_title_list,
            "figures": main_figures,
            "tables": main_tables
        })
        
        # 添加子标题作为独立条目
        for sub_title in item.get("sub_title_list", []):
            sub_title_text = sub_title if isinstance(sub_title, str) else sub_title.get("title", "")
            
            # 查找对应子标题的figures和tables
            sub_figures = []
            sub_tables = []
            
            for fig_group in item.get("figures", []):
                if isinstance(fig_group, dict) and sub_title_text in fig_group:
                    fig_items = fig_group.get(sub_title_text, [])
                    if isinstance(fig_items, list):
                        sub_figures.extend(fig_items)
                    else:
                        sub_figures.append(fig_items)
            
            for table_group in item.get("tables", []):
                if isinstance(table_group, dict) and sub_title_text in table_group:
                    table_items = table_group.get(sub_title_text, [])
                    if isinstance(table_items, list):
                        sub_tables.extend(table_items)
                    else:
                        sub_tables.append(table_items)
            
            all_titles.append({
                "title": sub_title_text,
                "level": level + 1,  # 子标题级别比主标题高一级
                "sub_level": sub_level + 1 if sub_level is not None else 3,
                "line_number": title_to_line_number.get(sub_title_text),
                "sub_title_list": [],
                "figures": sub_figures,
                "tables": sub_tables
            })
    
    # 按行号排序
    all_titles.sort(key=lambda x: x.get("line_number", 0) if x.get("line_number") is not None else float('inf'))
    
    # 添加next_line_number字段
    for i in range(len(all_titles) - 1):
        all_titles[i]["next_line_number"] = all_titles[i + 1]["line_number"]
    
    # 最后一个标题的next_line_number设为None
    if all_titles:
        all_titles[-1]["next_line_number"] = None
    
    return all_titles

def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 输入和输出文件路径
    structure_json_path = os.path.join(script_dir, "input.json")
    row_num_json_path = os.path.join(script_dir, "input_with_row_num.json")
    output_json_path = os.path.join(script_dir, "flattened_structure.json")
    
    # 加载两个JSON文件
    structure_data = load_json_file(structure_json_path)
    row_num_data = load_json_file(row_num_json_path)
    
    if not structure_data or not row_num_data:
        print("无法加载输入文件，请检查路径和文件格式")
        return
    
    # 合并和展平结构
    flattened_structure = merge_and_flatten_structure(structure_data, row_num_data)
    
    # 保存结果到文件
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(flattened_structure, f, ensure_ascii=False, indent=2)
    
    print(f"已成功生成展平的结构，保存为 '{output_json_path}'")

if __name__ == "__main__":
    main() 