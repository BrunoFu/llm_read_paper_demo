#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PDF处理辅助模块

该模块提供PDF文件处理的辅助函数，用于前端应用调用。
"""

import os
import sys
import tempfile
import subprocess
import json
import logging
import datetime
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入报告生成模块
from report_generator.LLM_for_paper_reading_updated import process_paper_report

# 配置日志
def setup_logger():
    """配置日志记录器"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logging")
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"pdf_processor_{timestamp}.log")
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 创建一个专门的前端错误记录器
    frontend_logger = logging.getLogger("frontend")
    frontend_logger.setLevel(logging.DEBUG)  # 设置为DEBUG级别，以便捕获更多信息
    frontend_logger.propagate = False  # 防止日志消息传播到根记录器
    
    # 清除现有的处理程序，以防重复
    for handler in frontend_logger.handlers[:]:
        frontend_logger.removeHandler(handler)
    
    # 添加文件处理程序
    frontend_log_file = os.path.join(log_dir, f"frontend_{timestamp}.log")
    frontend_file_handler = logging.FileHandler(frontend_log_file, encoding='utf-8')
    frontend_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    frontend_logger.addHandler(frontend_file_handler)
    
    # 添加控制台处理程序
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    frontend_logger.addHandler(console_handler)
    
    print(f"前端日志将被记录到: {frontend_log_file}")
    
    return logging.getLogger("pdf_processor"), frontend_logger

# 初始化日志记录器
logger, frontend_logger = setup_logger()

def check_environment():
    """检查环境是否满足运行条件"""
    # 硬编码API密钥，不再检查环境变量
    os.environ["MISTRAL_API_KEY"] = "FUHnqlXLiizX0TgsFM4KgVk4l9d1Ybnu"
    
    # 检查必要的脚本文件
    pdf_ocr_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              "pdf_content_extractor", "pdf_ocr.py")
    if not os.path.exists(pdf_ocr_path):
        logger.error(f"未找到OCR处理脚本: {pdf_ocr_path}")
        return False, f"未找到OCR处理脚本: {pdf_ocr_path}"
    
    integrated_processor_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          "section_data_extractor", "integrated_processor.py")
    if not os.path.exists(integrated_processor_path):
        logger.error(f"未找到结构化处理脚本: {integrated_processor_path}")
        return False, f"未找到结构化处理脚本: {integrated_processor_path}"
    
    logger.info("环境检查通过")
    return True, "环境检查通过"

def run_command(cmd, progress_callback=None, progress_start=0, progress_end=1):
    """运行命令并通过回调函数报告进度"""
    def safe_progress(value, desc=""):
        if progress_callback:
            try:
                progress_callback(value, desc)
            except Exception as e:
                logger.error(f"进度更新失败: {str(e)}")
                print(f"进度更新失败: {str(e)}")
    
    logger.info(f"运行命令: {' '.join(cmd)}")
    safe_progress(progress_start, f"运行命令: {' '.join(cmd)}")
    
    # 使用实时输出方式运行命令
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        bufsize=1,
        universal_newlines=True
    )
    
    # 实时输出命令执行结果
    output_lines = []
    if process.stdout:  # 检查stdout是否为None
        for line in process.stdout:
            line = line.rstrip()
            output_lines.append(line)
            logger.debug(line)
            
            # 如果有进度回调函数，更新进度
            # 简单的进度估计，根据输出行数计算
            current_progress = progress_start + (progress_end - progress_start) * 0.5
            safe_progress(current_progress, line)
    
    # 等待进程结束并获取返回码
    process.wait()
    
    if process.returncode != 0:
        logger.error(f"命令执行失败，返回码: {process.returncode}")
        logger.error("\n".join(output_lines))
    else:
        logger.info("命令执行完成")
    
    safe_progress(progress_end, "命令执行完成")
    
    if process.returncode != 0:
        return False, "\n".join(output_lines)
    
    return True, "\n".join(output_lines)

def process_pdf_file(pdf_file_path, output_dir, progress_callback=None):
    """处理PDF文件并返回结果"""
    logger.info(f"开始处理PDF文件: {pdf_file_path}")
    logger.info(f"输出目录: {output_dir}")
    
    # 检查环境
    env_check, message = check_environment()
    if not env_check:
        logger.error(f"环境检查失败: {message}")
        return False, message, None, None
    
    # 确保输出目录存在
    # 处理相对路径和绝对路径
    if not os.path.isabs(output_dir):
        # 如果是相对路径，转换为绝对路径
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"使用绝对输出路径: {output_dir}")
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 定义安全的进度回调函数
    def safe_progress(value, desc=""):
        if progress_callback:
            try:
                progress_callback(value, desc)
            except Exception as e:
                logger.error(f"进度更新失败: {str(e)}")
                print(f"进度更新失败: {str(e)}")
    
    # 调用OCR处理脚本
    logger.info("开始OCR处理...")
    safe_progress(0.1, "开始OCR处理...")
    
    ocr_script_path = os.path.join(project_root, "pdf_content_extractor", "pdf_ocr.py")
    ocr_cmd = [
        sys.executable,
        ocr_script_path,
        pdf_file_path,
        "-o", output_dir
    ]
    
    success, output = run_command(
        ocr_cmd, 
        progress_callback=safe_progress, 
        progress_start=0.1, 
        progress_end=0.4
    )
    
    if not success:
        logger.error(f"OCR处理失败: {output}")
        return False, f"OCR处理失败: {output}", None, None
    
    # 检查OCR结果
    complete_md_path = os.path.join(output_dir, "complete.md")
    if not os.path.exists(complete_md_path):
        logger.error("OCR处理失败：未生成complete.md文件")
        return False, "OCR处理失败：未生成complete.md文件", None, None
    
    # 调用结构化处理脚本
    logger.info("开始结构化处理...")
    safe_progress(0.4, "开始结构化处理...")
    
    processor_script_path = os.path.join(project_root, "section_data_extractor", "integrated_processor.py")
    processor_cmd = [
        sys.executable,
        processor_script_path,
        "--input", complete_md_path,
        "--output-dir", output_dir
    ]
    
    success, output = run_command(
        processor_cmd, 
        progress_callback=safe_progress, 
        progress_start=0.4, 
        progress_end=0.6
    )
    
    if not success:
        logger.error(f"结构化处理失败: {output}")
        return False, f"结构化处理失败: {output}", None, None
    
    # 查找结构化处理后的JSON文件
    json_path = os.path.join(output_dir, "paper_structure.json")
    json_found = False
    
    if os.path.exists(json_path):
        json_found = True
    else:
        # 尝试在子目录中查找paper_structure.json
        subdirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
        for subdir in subdirs:
            subdir_json_path = os.path.join(output_dir, subdir, "json", "structure_with_content_updated.json")
            if os.path.exists(subdir_json_path):
                json_path = subdir_json_path
                json_found = True
                logger.info(f"在子目录 {subdir} 中找到结构化数据")
                break
    
    if not json_found:
        logger.error("结构化处理失败：未找到JSON结果文件")
        return False, "结构化处理失败：未找到JSON结果文件", None, None
    
    # 生成报告
    logger.info("开始生成报告...")
    safe_progress(0.6, "开始生成报告...")
    
    try:
        # 异步调用报告生成函数，但使用同步方式等待结果
        report_file_path = asyncio.run(process_paper_report(json_path, output_dir))
        
        # 检查报告文件是否生成
        if not os.path.exists(report_file_path):
            logger.error("报告生成失败：未找到报告文件")
            return False, "报告生成失败：未找到报告文件", None, None
        
        logger.info(f"报告生成成功: {report_file_path}")
        safe_progress(0.8, "报告生成成功")
    except Exception as e:
        logger.error(f"报告生成失败: {str(e)}")
        return False, f"报告生成失败: {str(e)}", None, None
    
    # 读取处理结果
    logger.info("读取处理结果...")
    safe_progress(0.9, "读取处理结果...")
    
    # 读取Markdown结果（使用生成的报告文件）
    try:
        with open(report_file_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
    except Exception as e:
        logger.error(f"读取报告文件失败: {str(e)}")
        return False, f"读取报告文件失败: {str(e)}", None, None
    
    # 读取JSON结果
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            json_content = json.load(f)
    except Exception as e:
        logger.error(f"读取JSON结果失败: {str(e)}")
        return False, f"读取JSON结果失败: {str(e)}", markdown_content, None
    
    logger.info("处理完成！")
    safe_progress(1.0, "处理完成！")
    
    return True, "处理成功", markdown_content, json_content

def save_uploaded_pdf(pdf_file, temp_dir=None):
    """保存上传的PDF文件"""
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    
    pdf_path = os.path.join(temp_dir, "input.pdf")
    
    logger.info(f"保存上传的PDF文件到: {pdf_path}")
    
    # 保存上传的PDF
    try:
        with open(pdf_path, "wb") as f:
            # 从Gradio文件对象中读取内容
            if hasattr(pdf_file, "name"):
                # 处理Gradio的文件对象
                content = pdf_file.read() if hasattr(pdf_file, "read") else open(pdf_file.name, "rb").read()
                f.write(content)
            else:
                # 直接处理文件路径
                f.write(open(pdf_file, "rb").read())
        
        logger.info(f"PDF文件保存成功")
        return pdf_path, temp_dir
    except Exception as e:
        logger.error(f"保存PDF文件失败: {str(e)}")
        raise 