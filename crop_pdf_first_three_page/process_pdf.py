#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PDF处理流程工具

此脚本实现一个完整流程：
1. 裁剪PDF第一页
2. 调用Mistral OCR API处理裁剪后的PDF
3. 提取元数据

使用方法：
    python process_pdf.py input.pdf [output_dir] [template_path] [api_name]

注意：
    使用前请在代码中将 'your_mistral_api_key_here' 替换为您的实际 Mistral API 密钥
"""

import os
import sys
import json
import asyncio
import base64
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union

# 导入PDF裁剪函数
try:
    from .crop_pdf_first_page import crop_first_pages
except ImportError:
    try:
        from crop_pdf_first_page import crop_first_pages
    except ImportError:
        print("无法导入crop_pdf_first_page模块，请确保文件存在")
        sys.exit(1)

# 尝试导入元数据提取器
try:
    from meta_data_extractor.metadata_extractor import extract_metadata_from_pdf_first_pages
except ImportError:
    # 尝试从上级目录导入
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    try:
        from meta_data_extractor.metadata_extractor import extract_metadata_from_pdf_first_pages
    except ImportError:
        print("无法导入元数据提取器，请确保meta_data_extractor/metadata_extractor.py文件存在")
        # 不退出，继续执行，但标记为无法提取元数据
        extract_metadata_from_pdf_first_pages = None

# 尝试导入Mistral AI库
try:
    from mistralai import Mistral
    from mistralai import DocumentURLChunk
    from mistralai.models import OCRResponse
except ImportError:
    print("错误：未安装mistralai库，请使用 'pip install mistralai' 安装")
    sys.exit(1)

# Mistral OCR处理错误类
class OCRProcessingError(Exception):
    """OCR处理过程中出现的错误"""
    pass

def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    """
    替换Markdown中的图片引用路径
    
    Args:
        markdown_str: Markdown字符串
        images_dict: 图片ID到路径的映射字典
        
    Returns:
        替换后的Markdown字符串
    """
    for img_name, img_path in images_dict.items():
        markdown_str = markdown_str.replace(f"![{img_name}]({img_name})", f"![{img_name}]({img_path})")
    return markdown_str

def normalize_heading_levels(markdown_str: str) -> str:
    """
    将markdown中的所有标题级别（#、##、###等）都统一为一级标题（# ）
    
    Args:
        markdown_str: 原始markdown字符串
        
    Returns:
        标题格式已标准化的markdown字符串
    """
    import re
    # 匹配所有形式的markdown标题（# 到 ###### ）
    pattern = r'^(#{1,6})\s+'
    
    # 使用正则表达式查找所有行中的标题标记，并替换为一级标题（# ）
    lines = markdown_str.split('\n')
    for i, line in enumerate(lines):
        lines[i] = re.sub(pattern, '# ', line, flags=re.MULTILINE)
    
    return '\n'.join(lines)

def save_ocr_results(ocr_response, output_dir: str) -> Dict[str, Any]:
    """
    保存OCR处理结果到指定目录
    
    Args:
        ocr_response: OCR响应对象
        output_dir: 输出目录
        
    Returns:
        处理结果的字典
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # 为单独的页面创建目录
    pages_dir = os.path.join(output_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)
    
    all_markdowns = []
    
    # Mistral OCR是按页输出的，这里是把按页输出的结果拼起来
    for i, page in enumerate(ocr_response.pages, 1):
        # 保存图片
        page_images = {}
        for img in page.images:
            img_data = base64.b64decode(img.image_base64.split(',')[1])
            img_path = os.path.join(images_dir, f"{img.id}.png")
            with open(img_path, 'wb') as f:
                f.write(img_data)
            page_images[img.id] = f"../images/{img.id}.png"  # 相对路径，从pages目录访问images目录
        
        # 处理markdown内容
        page_markdown = replace_images_in_markdown(page.markdown, page_images)
        
        # 将所有标题级别标准化为一级标题
        page_markdown = normalize_heading_levels(page_markdown)
        
        all_markdowns.append(page_markdown)
        
        # 保存单独的页面markdown
        page_filename = f"page_{i:03d}.md"  # 使用3位数字格式，例如：page_001.md
        with open(os.path.join(pages_dir, page_filename), 'w', encoding='utf-8') as f:
            f.write(page_markdown)
            print(f"已保存第 {i} 页到 {page_filename}")
        
        # 为完整markdown中的图片路径重新调整
        for img_id in page_images:
            page_images[img_id] = f"images/{img_id}.png"  # 调整回相对于主目录的路径
        page_markdown = replace_images_in_markdown(page.markdown, page_images)
        
        # 为完整文档的每页内容也标准化标题级别
        page_markdown = normalize_heading_levels(page_markdown)
        
        all_markdowns[i-1] = page_markdown  # 更新all_markdowns中的内容
    
    # 保存完整markdown
    complete_path = os.path.join(output_dir, "complete.md")
    with open(complete_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(all_markdowns))
        print(f"已保存完整文档到 complete.md")
    
    # 提取前三页内容供元数据提取使用
    first_pages_content = "\n\n".join(all_markdowns[:3]) if len(all_markdowns) >= 3 else "\n\n".join(all_markdowns)
    first_pages_file = os.path.join(output_dir, f"{os.path.basename(output_dir)}_first_three_pages.md")
    with open(first_pages_file, 'w', encoding='utf-8') as f:
        f.write(first_pages_content)
    print(f"首页内容已保存至: {first_pages_file}")
    
    # 返回处理结果
    result = {
        "success": True,
        "complete_path": complete_path,
        "first_pages_path": first_pages_file,
        "page_count": len(ocr_response.pages)
    }
    return result

def call_mistral_ocr(pdf_path: str, output_dir: str) -> Dict[str, Any]:
    """
    调用Mistral OCR API处理PDF文件
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
        
    Returns:
        处理结果的字典
    """
    # 设置 API Key（直接硬编码到代码中）
    api_key = "FUHnqlXLiizX0TgsFM4KgVk4l9d1Ybnu"  # 请将此处替换为您的实际API密钥

    # 初始化客户端
    client = Mistral(api_key=api_key)
    
    # 确认PDF文件存在
    pdf_file = Path(pdf_path)
    if not pdf_file.is_file():
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    
    # 上传并处理PDF
    print(f"步骤2.1: 正在上传文件: {pdf_file.name}...")
    try:
        uploaded_file = client.files.upload(
            file={
                "file_name": pdf_file.stem,
                "content": pdf_file.read_bytes(),
            },
            purpose="ocr",
        )
        print(f"文件已上传成功，文件ID: {uploaded_file.id}")
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF文件 '{pdf_path}' 未找到。")
    except Exception as e:
        raise OCRProcessingError(f"上传PDF文件时发生错误: {e}")

    print("步骤2.2: 正在获取签名URL...")
    try:
        signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=60)  # 60秒有效期
    except Exception as e:
        raise OCRProcessingError(f"获取签名URL时发生错误: {e}")
    
    print("步骤2.3: OCR处理中，请稍候...")
    try:
        pdf_response = client.ocr.process(
            document=DocumentURLChunk(document_url=signed_url.url),
            model="mistral-ocr-latest",
            include_image_base64=True
        )
    except Exception as e:
        raise OCRProcessingError(f"OCR处理过程中发生错误: {e}")
    
    print("OCR处理已完成，正在保存结果...")
    # 保存结果
    result = save_ocr_results(pdf_response, output_dir)
    print(f"OCR处理完成。结果保存在: {output_dir}")
    
    return result

async def process_pdf(
    input_pdf: str,
    output_dir: Optional[str] = None,
    template_path: Optional[str] = None,
    api_name: Optional[str] = None,
    crop_params: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    处理PDF的主流程函数
    
    Args:
        input_pdf: 输入PDF文件路径
        output_dir: 输出目录，默认为"output/{pdf文件名}"
        template_path: 元数据提取的prompt模板路径，默认为"resources/LLM/extract_metadata_from_face_page.md"
        api_name: 使用的LLM API名称
        crop_params: PDF裁剪参数，格式为 {"left": 50, "bottom": 50, "right": 500, "top": 700}
        
    Returns:
        元数据提取结果
    """
    # 设置默认参数
    pdf_name = os.path.splitext(os.path.basename(input_pdf))[0]
    if not output_dir:
        output_dir = os.path.join("output", pdf_name)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    if not template_path:
        template_path = "resources/LLM/extract_metadata_from_face_page.md"
        # 检查默认模板是否存在
        if not os.path.exists(template_path):
            print(f"警告: 未找到默认模板文件 {template_path}，可能会影响元数据提取")
    
    # 设置裁剪参数
    if not crop_params:
        crop_params = {"left": 0, "bottom": 0, "right": None, "top": None}
    
    # 1. 裁剪PDF前三页
    print(f"步骤1: 裁剪PDF前三页")
    cropped_pdf = os.path.join(output_dir, f"{pdf_name}_first_three_pages.pdf")
    crop_success = crop_first_pages(
        input_pdf,
        cropped_pdf,
        num_pages=3,
        left=crop_params.get("left", 0),
        bottom=crop_params.get("bottom", 0),
        right=crop_params.get("right", None),
        top=crop_params.get("top", None)
    )
    
    if not crop_success:
        raise RuntimeError("PDF裁剪失败")
    
    # 2. 调用Mistral OCR API
    print(f"步骤2: 调用Mistral OCR API处理裁剪后的PDF")
    ocr_result = call_mistral_ocr(cropped_pdf, output_dir)
    
    # 3. 提取元数据
    print(f"步骤3: 提取元数据")
    first_pages_path = ocr_result["first_pages_path"]
    metadata_path = os.path.join(output_dir, f"{pdf_name}_metadata.json")
    
    # 检查首页内容文件是否存在
    if not os.path.exists(first_pages_path):
        raise FileNotFoundError(f"未找到首页内容文件: {first_pages_path}")
    
    # 提取元数据
    metadata = await extract_metadata_from_pdf_first_pages(
        first_pages_path=first_pages_path,
        template_path=template_path,
        output_path=metadata_path,
        api_name=api_name
    )
    
    print(f"处理完成! 元数据已保存至: {metadata_path}")
    return metadata

def main():
    """命令行入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF处理流程工具")
    parser.add_argument("input_pdf", help="输入PDF文件路径")
    parser.add_argument("--output-dir", "-d", default=None, help="输出目录")
    parser.add_argument("--template", "-t", default=None, help="元数据提取的prompt模板路径")
    parser.add_argument("--api", "-a", default=None, help="使用的LLM API名称")
    parser.add_argument("--left", type=float, default=0, help="左侧裁剪坐标")
    parser.add_argument("--bottom", type=float, default=0, help="底部裁剪坐标")
    parser.add_argument("--right", type=float, default=None, help="右侧裁剪坐标")
    parser.add_argument("--top", type=float, default=None, help="顶部裁剪坐标")
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input_pdf):
        print(f"错误：输入文件 '{args.input_pdf}' 不存在。")
        return 1
    
    # 构建裁剪参数
    crop_params = {
        "left": args.left,
        "bottom": args.bottom,
        "right": args.right,
        "top": args.top
    }
    
    try:
        # 执行处理流程
        asyncio.run(process_pdf(
            input_pdf=args.input_pdf,
            output_dir=args.output_dir,
            template_path=args.template,
            api_name=args.api,
            crop_params=crop_params
        ))
        return 0
    except OCRProcessingError as e:
        print(f"OCR处理失败: {str(e)}")
        return 1
    except Exception as e:
        print(f"处理失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
