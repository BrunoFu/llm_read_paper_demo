#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PDF处理工具

提供PDF裁剪、OCR处理等功能
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

# 导入PDF裁剪函数
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from crop_pdf_first_three_page.process_pdf import call_mistral_ocr
    from crop_pdf_first_three_page.crop_pdf_first_page import crop_first_page
except ImportError:
    print("无法导入PDF处理模块，请确保相关文件存在")
    sys.exit(1)

from pypdf import PdfReader, PdfWriter, Transformation

def crop_pdf_pages(
    input_file: str, 
    output_file: str, 
    page_count: int = 3, 
    left: float = 0, 
    bottom: float = 0, 
    right: Optional[float] = None, 
    top: Optional[float] = None
) -> bool:
    """
    裁剪PDF的前N页并保存为新文件
    
    参数:
        input_file (str): 输入PDF文件的路径
        output_file (str): 输出PDF文件的路径
        page_count (int): 要裁剪的页数，默认为3
        left (float): 裁剪区域左侧坐标
        bottom (float): 裁剪区域底部坐标
        right (float): 裁剪区域右侧坐标 (如果为None，则使用页面宽度)
        top (float): 裁剪区域顶部坐标 (如果为None，则使用页面高度)
        
    返回:
        bool: 是否成功裁剪
    """
    try:
        # 打开输入的PDF文件
        reader = PdfReader(input_file)
        writer = PdfWriter()
        
        # 检查输入文件是否有页面
        if len(reader.pages) == 0:
            print(f"错误：输入文件 '{input_file}' 没有页面。")
            return False
        
        # 确定要处理的页数
        actual_page_count = min(page_count, len(reader.pages))
        
        for page_index in range(actual_page_count):
            # 获取当前页
            current_page = reader.pages[page_index]
            
            # 获取原始页面尺寸
            media_box = current_page.mediabox
            original_width = media_box.width
            original_height = media_box.height
            
            # 如果未指定right或top，则使用原始页面尺寸
            current_right = right if right is not None else original_width
            current_top = top if top is not None else original_height
            
            # 确保剪裁区域在有效范围内
            current_left = max(0, min(left, original_width))
            current_bottom = max(0, min(bottom, original_height))
            current_right = max(current_left, min(current_right, original_width))
            current_top = max(current_bottom, min(current_top, original_height))
            
            # 计算裁剪宽度和高度
            crop_width = current_right - current_left
            crop_height = current_top - current_bottom
            
            # 创建一个转换对象，将剪裁区域移到页面左下角
            transform = Transformation().translate(-current_left, -current_bottom)
            
            # 应用转换
            current_page.add_transformation(transform)
            
            # 设置新的页面尺寸为裁剪区域大小
            current_page.mediabox.lower_left = (0, 0)
            current_page.mediabox.upper_right = (crop_width, crop_height)
            
            # 添加修改后的页面到新PDF
            writer.add_page(current_page)
        
        # 保存新PDF
        with open(output_file, 'wb') as output:
            writer.write(output)
        
        print(f"成功裁剪PDF前{actual_page_count}页并保存到 '{output_file}'")
        print(f"裁剪区域: 左={left}, 底={bottom}, 右={right}, 顶={top}")
        
        return True
    
    except Exception as e:
        print(f"裁剪PDF时出错: {str(e)}")
        return False

def process_pdf_for_metadata(
    input_pdf: str,
    output_dir: Optional[str] = None,
    page_count: int = 3,
    crop_params: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    处理PDF文件，裁剪前N页并进行OCR处理，用于元数据提取
    
    参数:
        input_pdf (str): 输入PDF文件的路径
        output_dir (str): 输出目录，默认为临时目录
        page_count (int): 要裁剪的页数，默认为3
        crop_params (dict): 裁剪参数，包含left, bottom, right, top
        
    返回:
        dict: 处理结果，包含状态和输出路径
    """
    # 获取PDF文件名（不含扩展名）
    pdf_file = Path(input_pdf)
    if not pdf_file.exists():
        return {
            "success": False,
            "error": f"PDF文件不存在: {input_pdf}"
        }
    
    pdf_name = pdf_file.stem
    
    # 设置输出目录
    if not output_dir:
        output_dir = os.path.join(tempfile.gettempdir(), f"pdf_metadata_{pdf_name}")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 设置裁剪参数
    if not crop_params:
        crop_params = {
            "left": 0,
            "bottom": 0,
            "right": None,
            "top": None
        }
    
    # 裁剪PDF前N页
    cropped_pdf = os.path.join(output_dir, f"{pdf_name}_first_{page_count}_pages.pdf")
    crop_success = crop_pdf_pages(
        input_file=input_pdf,
        output_file=cropped_pdf,
        page_count=page_count,
        left=crop_params.get("left", 0),
        bottom=crop_params.get("bottom", 0),
        right=crop_params.get("right"),
        top=crop_params.get("top")
    )
    
    if not crop_success:
        return {
            "success": False,
            "error": "PDF裁剪失败"
        }
    
    # 调用Mistral OCR处理裁剪后的PDF
    try:
        ocr_result = call_mistral_ocr(cropped_pdf, output_dir)
        
        return {
            "success": True,
            "output_dir": output_dir,
            "cropped_pdf": cropped_pdf,
            "complete_path": ocr_result.get("complete_path"),
            "first_pages_path": ocr_result.get("first_pages_path")
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"OCR处理失败: {str(e)}"
        }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="处理PDF文件，裁剪前N页并进行OCR处理")
    parser.add_argument("input_pdf", help="输入PDF文件的路径")
    parser.add_argument("--output-dir", "-o", help="输出目录")
    parser.add_argument("--page-count", "-p", type=int, default=3, help="要裁剪的页数，默认为3")
    parser.add_argument("--left", "-l", type=float, default=0, help="裁剪区域左侧坐标")
    parser.add_argument("--bottom", "-b", type=float, default=0, help="裁剪区域底部坐标")
    parser.add_argument("--right", "-r", type=float, help="裁剪区域右侧坐标")
    parser.add_argument("--top", "-t", type=float, help="裁剪区域顶部坐标")
    
    args = parser.parse_args()
    
    # 设置裁剪参数
    crop_params = {
        "left": args.left,
        "bottom": args.bottom,
        "right": args.right,
        "top": args.top
    }
    
    # 处理PDF
    result = process_pdf_for_metadata(
        input_pdf=args.input_pdf,
        output_dir=args.output_dir,
        page_count=args.page_count,
        crop_params=crop_params
    )
    
    if result["success"]:
        print(f"处理成功！")
        print(f"输出目录: {result['output_dir']}")
        print(f"裁剪后的PDF: {result['cropped_pdf']}")
        print(f"完整OCR结果: {result['complete_path']}")
        print(f"首页OCR结果: {result['first_pages_path']}")
    else:
        print(f"处理失败: {result.get('error', '未知错误')}") 