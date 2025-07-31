import os
import re
from pathlib import Path
import asyncio
import aiofiles


async def process_report(report_file_path, output_path=None, pdf_name=None):
    """
    处理Markdown报告文件，进行格式优化和内容清理
    
    参数:
        report_file_path: 原始报告文件路径
        output_path: 输出目录路径，如果为None则使用原始文件所在目录
        pdf_name: PDF文件名，用于生成最终报告文件名，如果为None则从report_file_path提取
        
    返回:
        最终报告文件的路径
    """
    # 设置默认输出路径
    if output_path is None:
        output_path = Path(report_file_path).parent
    else:
        output_path = Path(output_path)
    
    # 确保输出目录存在
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 读取原始报告内容
    report_file = Path(report_file_path)
    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替换LaTeX公式标记
    content = content.replace(r"\[", "$$")
    content = content.replace(r"\]", "$$")
    content = content.replace(r"\(", "$")
    content = content.replace(r"\)", "$")
    
    # 删除多余的Markdown标记
    content = remove_extra_hashes(content)
    content = remove_code_blocks(content)
    content = remove_horizontal_rules(content)
    
    # 删除特定的文本
    content = remove_specific_text(content)
    
    # 确定最终报告文件名
    if pdf_name is None:
        # 尝试从文件名中提取pdf_name
        file_stem = report_file.stem
        if file_stem == "report":
            # 如果文件名就是report.md，则使用父目录名作为pdf_name
            pdf_name = report_file.parent.name
        else:
            # 否则使用文件名作为pdf_name
            pdf_name = file_stem
    
    # 生成最终报告文件路径
    final_report_path = output_path / f"report_{pdf_name}.md"
    
    # 写入最终报告
    with open(final_report_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    # 如果原始文件与最终文件不同，则删除原始文件
    if report_file != final_report_path:
        report_file.unlink(missing_ok=True)
    
    print(f"报告处理完成，已保存为 {final_report_path}")
    return final_report_path


def remove_extra_hashes(markdown_text):
    """删除 Markdown 文件中多余的 # 号"""
    # 使用正则表达式匹配 n 个 # 和后面空格后再跟 m 个 # 号
    # 找到 n 个 # 和空格后，检查是否存在多余的 m 个 # 号，删除它们
    updated_text = re.sub(r'^(#+)\s+(#+)\s+', r'\1 ', markdown_text, flags=re.MULTILINE)
    return updated_text


def remove_code_blocks(markdown_text):
    """删除 Markdown 中的代码块标记 (``` + 任意字符 和 ```)"""
    # 正则表达式匹配以 ``` 开头和 ``` 结尾的代码块
    updated_text = re.sub(r'```.*?```', '', markdown_text, flags=re.DOTALL)
    return updated_text


def remove_horizontal_rules(markdown_text):
    """删除 Markdown 中单独成行的水平分隔线 (---)"""
    # 正则表达式匹配单独成行的 --- 或 *** 或 ___
    updated_text = re.sub(r'^\s*[-*_]{3,}\s*$', '', markdown_text, flags=re.MULTILINE)
    return updated_text


def remove_specific_text(markdown_text):
    """删除特定的文本内容"""
    # 删除Gemini App Activity相关文本
    specific_text = "By the way, there are some extensions that require Gemini App Activity to work. You can turn this on at [Gemini App Activity](https://myactivity.google.com/product/gemini)."
    updated_text = markdown_text.replace(specific_text, "")
    
    # 如果需要删除更多特定文本，可以在这里添加更多的替换
    
    return updated_text


# 提供一个同步版本的接口，方便直接调用
def process_report_sync(report_file_path, output_path=None, pdf_name=None):
    """同步版本的报告处理函数"""
    return asyncio.run(process_report(report_file_path, output_path, pdf_name))


if __name__ == "__main__":
    # 示例用法
    import sys
    
    if len(sys.argv) > 1:
        report_path = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else None
        pdf_name = sys.argv[3] if len(sys.argv) > 3 else None
        
        result_path = process_report_sync(report_path, output_dir, pdf_name)
        print(f"处理完成: {result_path}")
    else:
        print("用法: python report_processor.py <报告文件路径> [输出目录] [PDF名称]") 