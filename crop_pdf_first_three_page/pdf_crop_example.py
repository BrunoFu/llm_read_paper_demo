"""
PDF第一页剪裁示例

此脚本展示了如何使用crop_pdf_first_page模块来剪裁PDF的第一页。
"""

from crop_pdf_first_page import crop_first_page

def example_crop():
    # 示例：剪裁一个PDF文件的第一页
    input_pdf = "example.pdf"  # 替换为您要剪裁的PDF文件路径
    output_pdf = "example_cropped.pdf"
    
    # 裁剪参数 (单位: 点/points)
    # 这些值需要根据您的实际PDF进行调整
    left = 50    # 左边距离
    bottom = 50  # 底部距离
    right = 500  # 右边距离（或设为None以使用页面宽度）
    top = 700    # 顶部距离（或设为None以使用页面高度）
    
    # 执行裁剪
    crop_first_page(input_pdf, output_pdf, left, bottom, right, top)
    
    print("示例裁剪完成！")

if __name__ == "__main__":
    example_crop()
