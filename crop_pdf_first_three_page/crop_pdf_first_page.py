"""
PDF前三页剪裁工具

此脚本用于剪裁PDF文件的前三页并保存为新文件。
使用方法：
    python crop_pdf_first_pages.py input.pdf output.pdf [pages=3] [left] [bottom] [right] [top]
    
参数说明：
    input.pdf: 输入的PDF文件路径
    output.pdf: 输出的PDF文件路径
    pages: 要裁剪的页数，默认为3 (可选)
    left: 左侧裁剪坐标，默认为0 (可选)
    bottom: 底部裁剪坐标，默认为0 (可选)
    right: 右侧裁剪坐标，默认为页面宽度 (可选)
    top: 顶部裁剪坐标，默认为页面高度 (可选)
"""

import sys
import os
from pypdf import PdfReader, PdfWriter, Transformation

def crop_first_pages(input_file, output_file, num_pages=3, left=0, bottom=0, right=None, top=None):
    """
    剪裁PDF的前几页并保存为新文件
    
    参数:
        input_file (str): 输入PDF文件的路径
        output_file (str): 输出PDF文件的路径
        num_pages (int): 要裁剪的页数，默认为3
        left (float): 裁剪区域左侧坐标
        bottom (float): 裁剪区域底部坐标
        right (float): 裁剪区域右侧坐标 (如果为None，则使用页面宽度)
        top (float): 裁剪区域顶部坐标 (如果为None，则使用页面高度)
    """
    try:
        # 打开输入的PDF文件
        reader = PdfReader(input_file)
        writer = PdfWriter()
        
        # 检查输入文件是否有页面
        if len(reader.pages) == 0:
            print(f"错误：输入文件 '{input_file}' 没有页面。")
            return False
        
        # 确定要处理的页数（不超过文件实际页数）
        pages_to_process = min(num_pages, len(reader.pages))
        
        for page_index in range(pages_to_process):
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
        
        print(f"成功剪裁PDF前 {pages_to_process} 页并保存到 '{output_file}'")
        print(f"剪裁区域: 左={left}, 底={bottom}, 右={right if right else '页面宽度'}, 顶={top if top else '页面高度'}")
        
        return True
    
    except Exception as e:
        print(f"剪裁PDF时出错: {str(e)}")
        # 如果是网络超时错误，提供更详细的错误信息
        if "timed out" in str(e).lower() or "timeout" in str(e).lower():
            print("这可能是网络连接问题，请检查网络连接后重试")
        return False

def main():
    # 检查命令行参数
    if len(sys.argv) < 3:
        print("用法: python crop_pdf_first_pages.py 输入文件.pdf 输出文件.pdf [页数=3] [左] [底] [右] [顶]")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：输入文件 '{input_file}' 不存在。")
        return
    
    # 获取可选参数
    try:
        # 如果第三个参数是数字且小于100，假设它是页数
        if len(sys.argv) > 3 and sys.argv[3].isdigit() and int(sys.argv[3]) < 100:
            num_pages = int(sys.argv[3])
            arg_offset = 4  # 后续参数偏移量
        else:
            num_pages = 3  # 默认3页
            arg_offset = 3  # 后续参数偏移量
        
        left = float(sys.argv[arg_offset]) if len(sys.argv) > arg_offset else 0
        bottom = float(sys.argv[arg_offset+1]) if len(sys.argv) > arg_offset+1 else 0
        right = float(sys.argv[arg_offset+2]) if len(sys.argv) > arg_offset+2 else None
        top = float(sys.argv[arg_offset+3]) if len(sys.argv) > arg_offset+3 else None
    except ValueError:
        print("错误：裁剪参数必须是数字。")
        return
    
    # 执行剪裁
    crop_first_pages(input_file, output_file, num_pages, left, bottom, right, top)

if __name__ == "__main__":
    main() 