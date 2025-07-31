from mistralai import Mistral
from pathlib import Path
import os
import base64
import sys
import argparse
from mistralai import DocumentURLChunk
from mistralai.models import OCRResponse

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有安装 python-dotenv，手动读取 .env 文件
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

class OCRProcessingError(Exception):
    """Raised when an OCR processing step fails."""
# The mistralai.exceptions module does not exist; use base Exception for error handling.
MistralAPIException = MistralConnectionException = MistralException = Exception

def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
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

def save_ocr_results(ocr_response: OCRResponse, output_dir: str) -> None:
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # 为单独的页面创建目录
    pages_dir = os.path.join(output_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)
    
    all_markdowns = []
    
    ## mistral ocr是按页输出的，这里是把按页输出的结果给拼起来
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
    with open(os.path.join(output_dir, "complete.md"), 'w', encoding='utf-8') as f:
        f.write("\n\n".join(all_markdowns))
        print(f"已保存完整文档到 complete.md")

def process_pdf(pdf_path: str, output_dir_arg: str = None) -> None:
    # 获取 API Key
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY 环境变量未设置。")

    # 初始化客户端
    client = Mistral(api_key=api_key)
    
    # 确认PDF文件存在
    pdf_file = Path(pdf_path)
    if not pdf_file.is_file():
        # This check might be redundant if argparse handles file existence,
        # but good for direct calls or future refactoring.
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    
    # 确定输出目录
    if output_dir_arg:
        output_dir = output_dir_arg
    else:
        output_dir = f"ocr_results_{pdf_file.stem}"
    
    # 上传并处理PDF
    print(f"正在上传文件: {pdf_file.name}...")
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
        # Should be caught by the earlier check, but raise for safety
        raise FileNotFoundError(f"PDF文件 '{pdf_path}' 未找到。")
    except (MistralAPIException, MistralConnectionException) as e:
        raise OCRProcessingError(f"上传PDF文件时发生API或连接错误: {e}") from e
    except MistralException as e:
        raise OCRProcessingError(f"上传PDF文件时发生Mistral相关错误: {e}") from e
    except Exception as e:
        raise OCRProcessingError(f"上传PDF文件时发生未知错误: {e}") from e

    print("正在获取签名URL...")
    try:
        signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=60)  # Increased expiry to 60 seconds
    except (MistralAPIException, MistralConnectionException) as e:
        raise OCRProcessingError(f"获取签名URL时发生API或连接错误: {e}") from e
    except MistralException as e:
        raise OCRProcessingError(f"获取签名URL时发生Mistral相关错误: {e}") from e
    except Exception as e:
        raise OCRProcessingError(f"获取签名URL时发生未知错误: {e}") from e
    
    print("OCR处理中，请稍候...")
    try:
        pdf_response = client.ocr.process(
            document=DocumentURLChunk(document_url=signed_url.url),
            model="mistral-ocr-latest",
            include_image_base64=True
        )
    except (MistralAPIException, MistralConnectionException) as e:
        raise OCRProcessingError(f"OCR处理过程中发生API或连接错误: {e}") from e
    except MistralException as e:
        raise OCRProcessingError(f"OCR处理过程中发生Mistral相关错误: {e}") from e
    except Exception as e:
        raise OCRProcessingError(f"OCR处理过程中发生未知错误: {e}") from e
    
    print("OCR处理已完成，正在保存结果...")
    # 保存结果
    save_ocr_results(pdf_response, output_dir)
    print(f"OCR处理完成。结果保存在: {output_dir}")

def main():
    # API_KEY 将从环境变量 MISTRAL_API_KEY 读取 (process_pdf内处理)
    
    parser = argparse.ArgumentParser(description="使用 Mistral AI OCR 功能处理 PDF 文件。")
    parser.add_argument("pdf_path", help="要处理的 PDF 文件的路径。")
    parser.add_argument(
        "-o", "--output_dir",
        help="存储结果的输出目录。如果未提供，则默认为 'ocr_results_[PDF文件名]'。"
    )

    args = parser.parse_args()

    try:
        process_pdf(args.pdf_path, args.output_dir)
    except (FileNotFoundError, ValueError, OCRProcessingError) as e:
        print(f"主程序错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"主程序未知错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

