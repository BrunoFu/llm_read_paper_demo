#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
从structure_with_content_updated.json中提取数学公式

该脚本用于从structure_with_content_updated.json中提取数学公式，
并将其添加到每个子JSON对象中。

用法:
    python extract_formulas.py --input structure_with_content_updated.json --output structure_with_content_updated.json
"""

import os
import sys
import json
import re
import argparse
import shutil
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Fore.RED}错误: 文件不存在 - {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"{Fore.RED}错误: 无效的JSON文件 - {file_path}")
        return None
    except Exception as e:
        print(f"{Fore.RED}错误: 加载JSON文件时出现未知错误 - {e}")
        return None

def save_json_file(data, file_path):
    """保存JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"{Fore.RED}错误: 保存JSON文件时出现错误 - {e}")
        return False

def extract_formulas(text):
    """
    从文本中提取所有由双美元符号($$)包裹的数学公式
    
    Args:
        text: 要处理的文本
        
    Returns:
        提取的公式列表
    """
    if not text:
        return []
    
    # 使用正则表达式提取所有由双美元符号包裹的内容
    # 需要对$符号进行转义，并使用非贪婪模式匹配
    pattern = r'\$\$(.*?)\$\$'
    
    # 使用re.DOTALL标志使.能够匹配换行符
    matches = re.findall(pattern, text, re.DOTALL)
    
    # 返回非空公式列表
    return [formula.strip() for formula in matches if formula.strip()]

def add_formulas_to_structure(structure_data):
    """
    为结构中的每个节点添加公式字段
    
    Args:
        structure_data: 论文结构数据
        
    Returns:
        添加了公式字段的结构数据
    """
    total_formulas = 0
    items_with_formulas = 0
    
    for item in structure_data:
        # 检查是否有text_content字段
        if "text_content" in item and item["text_content"]:
            # 提取公式
            formulas = extract_formulas(item["text_content"])
            
            # 添加公式字段
            item["formulas"] = formulas
            
            # 统计信息
            if formulas:
                items_with_formulas += 1
                total_formulas += len(formulas)
    
    return structure_data, total_formulas, items_with_formulas

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="从structure_with_content_updated.json中提取数学公式")
    parser.add_argument("--input", default="structure_with_content_updated.json", help="输入的JSON文件路径")
    parser.add_argument("--output", default=None, help="输出的JSON文件路径(默认与输入相同)")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置输入文件路径
    input_path = args.input
    if not os.path.isabs(input_path):
        input_path = os.path.join(script_dir, input_path)
    
    # 设置输出文件路径
    output_path = args.output if args.output else input_path
    if not os.path.isabs(output_path):
        output_path = os.path.join(script_dir, output_path)
    
    # 如果启用调试模式，测试正则表达式
    if args.debug:
        test_text = """
        这是一个测试文本，包含以下公式：
        
        $$E = mc^2$$
        
        以及另一个公式
        
        $$F = ma$$
        
        还有一个多行公式
        
        $$
        x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
        $$
        
        以及一个行内公式 $E=mc^2$ 不应该被提取
        """
        
        print(f"{Fore.CYAN}测试文本:")
        print(test_text)
        
        print(f"{Fore.CYAN}提取的公式:")
        formulas = extract_formulas(test_text)
        for i, formula in enumerate(formulas, 1):
            print(f"{i}. {formula}")
        
        return True
    
    # 加载JSON文件
    structure_data = load_json_file(input_path)
    if not structure_data:
        print(f"{Fore.RED}无法加载JSON文件，请检查文件路径")
        return False
    
    # 提取公式并添加到结构中
    print(f"{Fore.CYAN}正在提取数学公式...")
    updated_data, total_formulas, items_with_formulas = add_formulas_to_structure(structure_data)
    
    # 保存更新后的数据
    if output_path == input_path:
        # 如果输出路径与输入路径相同，先创建备份
        backup_path = input_path + ".bak"
        try:
            shutil.copy2(input_path, backup_path)
            print(f"{Fore.CYAN}已创建原文件备份: {backup_path}")
        except Exception as e:
            print(f"{Fore.YELLOW}警告: 无法创建备份文件 - {e}")
    
    success = save_json_file(updated_data, output_path)
    
    if success:
        # 统计信息
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}公式提取统计")
        print(f"{Fore.CYAN}{'='*80}")
        print(f"总节点数: {len(structure_data)}")
        print(f"包含公式的节点数: {items_with_formulas}")
        print(f"提取的公式总数: {total_formulas}")
        
        if items_with_formulas > 0:
            print(f"平均每个包含公式的节点的公式数: {total_formulas / items_with_formulas:.2f}")
        
        print(f"{Fore.CYAN}{'='*80}\n")
        
        print(f"{Fore.GREEN}已成功提取公式并保存")
        return True
    else:
        print(f"{Fore.RED}保存更新后的数据失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 