import os
import sys
import time
import json
import glob
import shutil
import zipfile
import requests
import urllib3
import argparse
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, List, Any, Optional, Tuple

# 导入PDF裁剪功能
from crop_pdf_first_page import crop_first_pages

# 导入元数据提取功能
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from meta_data_extractor.metadata_extractor import extract_metadata
except ImportError:
    print("警告: 无法导入元数据提取模块")
    extract_metadata = None

# 禁用不安全连接警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# —— 1. 基本配置 —— 
API_BASE = "https://mineru.net/api/v4"
TOKEN = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIxMDIwMzYxOSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1MjUwMzMzNSwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTMxMzcwNjY5NzIiLCJvcGVuSWQiOm51bGwsInV1aWQiOiJiYTFkYzE4MS01ODliLTQ1YmMtOTAzZS03MDg4NWZlMmQxNzEiLCJlbWFpbCI6IiIsImV4cCI6MTc1MzcxMjkzNX0.1igJ_jJsIK7Bc4a9dVlHN1LD0iaCUW1MolC4ilOyJ3sjMCGXyQd3aB6MHqLLldyJwWyri3G_zp9nyHbvzUGhyg"   # 在个人中心获取

# 创建一个带有重试机制的会话
def create_session():
    session = requests.Session()
    retry_strategy = requests.adapters.Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "PUT", "POST", "OPTIONS"]
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

session = create_session()

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def download_with_urllib3(url, output_file):
    """使用urllib3下载文件"""
    try:
        http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        r = http.request('GET', url, timeout=urllib3.Timeout(connect=30.0, read=120.0))
        if r.status == 200:
            with open(output_file, "wb") as f:
                f.write(r.data)
            return True
        return False
    except Exception as e:
        print(f"下载失败: {e}")
        return False

def process_pdf(local_pdf_path, output_dir="results"):
    """处理单个PDF文件，调用API进行OCR"""
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成唯一的输出文件名（基于原文件名和时间戳）
    base_name = os.path.splitext(os.path.basename(local_pdf_path))[0]
    timestamp = int(time.time())
    output_file = os.path.join(output_dir, f"{base_name}_{timestamp}.zip")
    
    print(f"开始处理文件: {os.path.basename(local_pdf_path)}")
    
    # —— 2. 批量申请上传链接并提交解析任务 —— 
    batch_payload = {
        "enable_formula": True,      # 是否识别公式
        "language": "auto",          # 文档语言，auto 表示自动识别
        "enable_table": True,        # 是否识别表格
        "files": [
            {
                "name": os.path.basename(local_pdf_path),  # 只使用文件名
                "is_ocr": True,      # 是否启用 OCR
                "data_id": f"file_{timestamp}"  # 使用时间戳作为唯一ID
            }
        ]
    }

    try:
        resp = session.post(f"{API_BASE}/file-urls/batch", headers=headers, json=batch_payload, verify=False, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        if result["code"] != 0:
            raise RuntimeError(f"申请上传链接失败：{result['msg']}")
        batch_id = result["data"]["batch_id"]
        upload_urls = result["data"]["file_urls"]
        print(f"✔ batch_id: {batch_id}")  # 之后查询任务时用到
    except Exception as e:
        print(f"申请上传链接失败: {e}")
        return None, None

    # —— 3. 将本地文件通过预签名 URL 上传 —— 
    try:
        with open(local_pdf_path, "rb") as f:
            upload_resp = session.put(upload_urls[0], data=f, verify=False, timeout=60)
            if upload_resp.status_code == 200:
                print(f"✔ 文件上传成功")
            else:
                print(f"✖ 文件上传失败: {upload_resp.status_code}")
                return None, None
            upload_resp.raise_for_status()
    except Exception as e:
        print(f"文件上传过程中出错: {e}")
        return None, None

    # —— 4. 轮询任务状态 —— 
    max_attempts = 30  # 最多尝试30次，每次间隔5秒
    attempts = 0
    download_url = None
    
    while attempts < max_attempts:
        try:
            resp = session.get(f"{API_BASE}/extract-results/batch/{batch_id}", headers=headers, verify=False, timeout=30)
            resp.raise_for_status()
            data = resp.json()["data"]["extract_result"]
            
            all_done = True
            for item in data:
                print(f"文件: {item['file_name']}, 状态: {item['state']}")
                if item['state'] != "done":
                    all_done = False
            
            if all_done and data:
                # 假设只处理了一个文件，就拿第一个的 full_zip_url
                download_url = data[0]["full_zip_url"]
                break
                
            attempts += 1
            time.sleep(5)
        except Exception as e:
            print(f"查询任务状态失败: {e}")
            attempts += 1
            time.sleep(5)
    
    if not download_url:
        print("任务未完成或获取下载链接失败")
        return None, None
    
    # —— 5. 下载解析结果压缩包 —— 
    # 使用urllib3下载
    try:
        if download_with_urllib3(download_url, output_file):
            print(f"✔ 下载成功，结果已保存至 {output_file}")
            return output_file, base_name
        else:
            print("下载失败")
            return None, None
    except Exception as e:
        print(f"下载过程中出错: {e}")
        return None, None

def extract_zip(zip_file, extract_dir):
    """解压ZIP文件到指定目录"""
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"✔ 解压成功到 {extract_dir}")
        return True
    except Exception as e:
        print(f"解压失败: {e}")
        return False

def get_block_text(block):
    """获取文本块中的文本"""
    # 根据MinerU中间JSON的结构获取文本
    if "text" in block:
        return block["text"]
    
    # 从lines和spans中获取文本
    if "lines" in block:
        lines_texts = []
        for line in block.get("lines", []):
            line_text = ""
            if "spans" in line:
                for span in line.get("spans", []):
                    if "text" in span:
                        line_text += span.get("text", "")
                    elif "content" in span:
                        line_text += span.get("content", "")
            lines_texts.append(line_text)
        return " ".join(lines_texts)
    
    # 尝试从spans直接获取文本
    if "spans" in block:
        spans_texts = []
        for span in block["spans"]:
            if "text" in span:
                spans_texts.append(span["text"])
            elif "content" in span:
                spans_texts.append(span["content"])
        return " ".join(spans_texts)
    
    # 尝试从content字段获取文本
    if "content" in block:
        return block["content"]
    
    return ""

def is_header_block(block, page_height):
    """判断文本块是否为页眉页脚"""
    # 获取块文本
    text = get_block_text(block)
    if not text:
        return False
    
    # 检查是否在页面顶部或底部
    if "bbox" in block:
        bbox = block.get("bbox", [0, 0, 0, 0])
        
        # 安全检查
        if not isinstance(bbox, list) or len(bbox) < 2:
            return False
        
        # 页眉通常在页面顶部10%以内
        if bbox[1] < page_height * 0.1:
            return True
        
        # 页脚通常在页面底部10%以内
        if bbox[1] > page_height * 0.9:
            return True
    
    return False

def is_footnote_block(block, page_height):
    """判断文本块是否为脚注"""
    # 获取块文本
    text = get_block_text(block)
    if not text:
        return False
    
    # 检查是否有脚注标记
    footnote_patterns = [
        r'^\s*\d+\.\s+',  # "1. "
        r'^\s*\[\d+\]\s+', # "[1] "
        r'^\s*\(\d+\)\s+', # "(1) "
        r'^\s*[*†‡§]\s+',  # "* "
    ]
    
    for pattern in footnote_patterns:
        if re.match(pattern, text):
            return True
    
    # 检查是否在页面底部
    if "bbox" in block:
        bbox = block.get("bbox", [0, 0, 0, 0])
        
        # 安全检查
        if not isinstance(bbox, list) or len(bbox) < 2:
            return False
            
        if bbox[1] > page_height * 0.8:  # 如果在页面底部80%以下
            # 检查字体大小，脚注通常字体较小
            if "font_size" in block and block["font_size"] < 10:
                return True
    
    return False

def safe_get_y_coordinate(block):
    """安全地获取块的y坐标（即bbox的第二个元素，表示左上角的y坐标）"""
    if "bbox" not in block:
        return 0
    
    bbox = block.get("bbox")
    if not isinstance(bbox, list):
        return 0
    
    if len(bbox) < 2:
        return 0
    
    return bbox[1]  # 返回y1坐标，即左上角的y坐标

def extract_content_with_headers_footers(middle_json):
    """从middle_json中提取内容，包括页眉页脚"""
    # 如果middle_json是字符串，尝试解析为JSON
    if isinstance(middle_json, str):
        try:
            middle_json = json.loads(middle_json)
        except Exception as e:
            print(f"解析middle_json失败: {e}")
            return "无法解析middle_json"
    
    content = ""
    
    # 获取pdf_info
    pdf_info = middle_json.get("pdf_info", [])
    if not pdf_info:
        return "未找到pdf_info数据"
    
    # 处理每一页
    for i, page in enumerate(pdf_info):
        page_num = i + 1
        print(f"正在提取第 {page_num} 页内容...")
        
        # 获取页面尺寸
        page_size = page.get("page_size", [0, 0])
        page_height = page_size[1] if len(page_size) > 1 else 1000
        
        # 获取预处理块和丢弃的块
        preproc_blocks = page.get("preproc_blocks", [])
        discarded_blocks = page.get("discarded_blocks", [])
        
        # 合并所有块
        all_blocks = preproc_blocks + discarded_blocks
        
        # 分离正文、脚注和页眉页脚
        main_blocks = []
        footnote_blocks = []
        header_blocks = []
        
        # 识别不同类型的块
        for block in all_blocks:
            if is_footnote_block(block, page_height):
                footnote_blocks.append(block)
            elif is_header_block(block, page_height):
                header_blocks.append(block)
            else:
                main_blocks.append(block)
        
        # 按y坐标排序块
        sorted_main_blocks = sorted(main_blocks, key=safe_get_y_coordinate)
        
        # 添加页面标题
        content += f"## 第{page_num}页\n\n"
        
        # 添加页眉
        if header_blocks:
            content += "### 页眉页脚\n\n"
            for block in header_blocks:
                block_text = get_block_text(block)
                if block_text:
                    content += f"{block_text}\n\n"
        
        # 添加正文内容
        content += "### 正文内容\n\n"
        for block in sorted_main_blocks:
            block_text = get_block_text(block)
            if block_text:
                content += f"{block_text}\n\n"
        
        # 添加脚注
        if footnote_blocks:
            content += "### 脚注\n\n"
            for block in footnote_blocks:
                block_text = get_block_text(block)
                if block_text:
                    content += f"- {block_text}\n\n"
        
        # 添加页面分隔符
        if i < len(pdf_info) - 1:
            content += "---\n\n"
    
    return content

def clean_up_files(files_to_clean):
    """清理中间文件"""
    for file_path in files_to_clean:
        if not file_path:
            continue
            
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"已删除文件: {file_path}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"已删除目录: {file_path}")
        except Exception as e:
            print(f"删除 {file_path} 时出错: {e}")

def process_single_pdf(pdf_path, output_dir="results", template_path=None, keep_intermediate_files=False):
    """处理单个PDF文件的完整流程"""
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 裁剪PDF的前三页
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    cropped_pdf_path = os.path.join(output_dir, f"{base_name}_first_three_pages.pdf")
    
    print(f"裁剪PDF前三页: {pdf_path}")
    if not crop_first_pages(pdf_path, cropped_pdf_path, num_pages=3):
        print(f"裁剪PDF失败: {pdf_path}")
        return None
    
    print(f"✔ 裁剪成功，保存到: {cropped_pdf_path}")
    
    # 2. 调用API进行OCR
    zip_file, _ = process_pdf(cropped_pdf_path, output_dir)
    if not zip_file:
        print(f"处理失败: {cropped_pdf_path}")
        # 清理裁剪的PDF
        if not keep_intermediate_files and os.path.exists(cropped_pdf_path):
            os.remove(cropped_pdf_path)
        return None
    
    # 3. 解压ZIP文件
    extract_dir = os.path.join(output_dir, base_name)
    os.makedirs(extract_dir, exist_ok=True)
    
    if not extract_zip(zip_file, extract_dir):
        print(f"解压失败: {zip_file}")
        # 清理裁剪的PDF和ZIP文件
        if not keep_intermediate_files:
            clean_up_files([cropped_pdf_path, zip_file])
        return None
    
    # 4. 查找layout.json文件
    layout_json_path = None
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file == "layout.json":
                layout_json_path = os.path.join(root, file)
                break
        if layout_json_path:
            break
    
    if not layout_json_path:
        print(f"未找到layout.json文件")
        # 清理裁剪的PDF、ZIP文件和解压目录
        if not keep_intermediate_files:
            clean_up_files([cropped_pdf_path, zip_file, extract_dir])
        return None
    
    # 5. 读取layout.json
    try:
        with open(layout_json_path, 'r', encoding='utf-8') as f:
            middle_json = json.load(f)
    except Exception as e:
        print(f"读取layout.json失败: {e}")
        # 清理裁剪的PDF、ZIP文件和解压目录
        if not keep_intermediate_files:
            clean_up_files([cropped_pdf_path, zip_file, extract_dir])
        return None
    
    # 6. 提取内容，包括页眉页脚
    markdown_content = extract_content_with_headers_footers(middle_json)
    
    # 7. 保存Markdown文件
    markdown_path = os.path.join(output_dir, f"{base_name}_first_three_pages.md")
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    print(f"✔ Markdown内容已保存到 {markdown_path}")
    
    # 8. 提取元数据
    metadata = None
    metadata_path = os.path.join(output_dir, f"{base_name}_metadata.json")
    
    # 使用导入的元数据提取函数
    if extract_metadata:
        try:
            print("使用元数据提取模块提取元数据...")
            # 如果没有提供模板路径，使用默认模板
            if not template_path:
                template_path = "resources/extract_metadata_from_face_page.md"
            
            # 调用导入的extract_metadata函数
            metadata = extract_metadata(
                pdf_name=base_name,
                output_dir=output_dir,
                template_path=template_path
            )
        except Exception as e:
            print(f"使用元数据提取模块提取元数据失败: {e}")
            # 如果元数据提取失败，不清理文件，以便调试
            return None
    else:
        print("未找到元数据提取模块，无法提取元数据")
        # 清理所有中间文件
        if not keep_intermediate_files:
            clean_up_files([cropped_pdf_path, zip_file, extract_dir, markdown_path])
        return None
    
    # 9. 清理中间文件
    if not keep_intermediate_files:
        files_to_clean = [
            cropped_pdf_path,  # 裁剪的PDF
            zip_file,          # ZIP压缩包
            extract_dir,       # 解压目录
            markdown_path      # Markdown文件
        ]
        clean_up_files(files_to_clean)
    
    return {
        "pdf_path": pdf_path,
        "metadata_path": metadata_path,
        "metadata": metadata
    }

def batch_process_pdfs(pdf_dir_or_pattern, output_dir="results", template_path=None, keep_intermediate_files=False):
    """批量处理PDF文件"""
    # 如果输入是目录，则处理目录中所有PDF文件
    if os.path.isdir(pdf_dir_or_pattern):
        pdf_files = glob.glob(os.path.join(pdf_dir_or_pattern, "*.pdf"))
    else:
        # 否则将输入视为glob模式
        pdf_files = glob.glob(pdf_dir_or_pattern)
    
    if not pdf_files:
        print(f"未找到PDF文件: {pdf_dir_or_pattern}")
        return
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    
    # 记录处理结果
    results = []
    
    # 处理每个PDF文件
    for i, pdf_path in enumerate(pdf_files):
        print(f"\n[{i+1}/{len(pdf_files)}] 处理文件: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            print(f"错误: 文件不存在 {pdf_path}")
            results.append({
                "file": pdf_path,
                "success": False,
                "error": "文件不存在"
            })
            continue
        
        result = process_single_pdf(pdf_path, output_dir, template_path, keep_intermediate_files)
        
        if result:
            print(f"处理完成! 元数据已保存到: {result['metadata_path']}")
            results.append({
                "file": pdf_path,
                "success": True,
                "metadata": result["metadata"]
            })
        else:
            print(f"处理失败!")
            results.append({
                "file": pdf_path,
                "success": False,
                "error": "处理失败"
            })
    
    # 生成统计报告
    success_count = sum(1 for r in results if r["success"])
    
    print("\n===== 处理统计 =====")
    print(f"总文件数: {len(pdf_files)}")
    print(f"成功数量: {success_count}")
    print(f"失败数量: {len(pdf_files) - success_count}")
    
    # 保存处理结果到JSON文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_dir, f"ocr_report_{timestamp}.json")
    
    report_data = {
        "timestamp": timestamp,
        "total_files": len(pdf_files),
        "success_count": success_count,
        "failure_count": len(pdf_files) - success_count,
        "results": results
    }
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细报告已保存至: {report_file}")
    
    return results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MinerU OCR处理工具")
    parser.add_argument("input", help="PDF文件路径或包含PDF文件的目录")
    parser.add_argument("--output", "-o", default="results", help="输出目录")
    parser.add_argument("--template", "-t", default=None, help="元数据提取模板路径")
    parser.add_argument("--keep-files", "-k", action="store_true", help="保留中间文件（默认删除）")
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)
    
    # 如果输入是单个文件
    if os.path.isfile(args.input) and args.input.lower().endswith(".pdf"):
        print(f"处理单个PDF文件: {args.input}")
        result = process_single_pdf(args.input, args.output, args.template, args.keep_files)
        if result:
            print(f"处理成功! 元数据已保存到: {result['metadata_path']}")
        else:
            print("处理失败!")
    else:
        # 批量处理
        print(f"批量处理PDF文件: {args.input}")
        batch_process_pdfs(args.input, args.output, args.template, args.keep_files)

if __name__ == "__main__":
    main() 