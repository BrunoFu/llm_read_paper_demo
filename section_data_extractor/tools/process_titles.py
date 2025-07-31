#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
标题处理流程脚本
将提取标题行号和验证标题行号两个步骤连接起来
"""

import os
import sys
import subprocess
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

def run_script(script_path):
    """运行指定的Python脚本"""
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            text=True,
            capture_output=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}脚本执行失败: {e}")
        print(f"{Fore.RED}错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"{Fore.RED}发生错误: {e}")
        return False

def main():
    """主函数"""
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建脚本路径
    extract_script = os.path.join(script_dir, "extract_title_lines.py")
    verify_script = os.path.join(script_dir, "verify_title_lines.py")
    
    print(f"{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}标题处理流程")
    print(f"{Fore.CYAN}{'='*80}")
    
    # 步骤1: 提取标题行号
    print(f"\n{Fore.YELLOW}步骤1: 提取标题行号")
    print(f"{Fore.YELLOW}{'-'*80}")
    if not run_script(extract_script):
        print(f"{Fore.RED}提取标题行号失败，流程终止")
        return
    
    # 步骤2: 验证标题行号
    print(f"\n{Fore.YELLOW}步骤2: 验证标题行号")
    print(f"{Fore.YELLOW}{'-'*80}")
    if not run_script(verify_script):
        print(f"{Fore.RED}验证标题行号失败")
        return
    
    print(f"\n{Fore.GREEN}{'='*80}")
    print(f"{Fore.GREEN}处理完成!")
    print(f"{Fore.GREEN}{'='*80}")
    print(f"{Fore.GREEN}生成的文件:")
    print(f"{Fore.GREEN}1. input_with_row_num.json - 带行号的标题")
    print(f"{Fore.GREEN}2. verified_titles.json - 验证后的标题(包含行内容和匹配质量)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}程序已被用户中断")
    except Exception as e:
        print(f"\n{Fore.RED}发生错误: {e}") 