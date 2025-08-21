import os
import sys
import gradio as gr
import tempfile
import json
import time
import random
import string
import subprocess
from pathlib import Path
import markdown
import re
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入自定义模块
from pdf_processor import process_pdf_file, save_uploaded_pdf, logger, frontend_logger

# 导入滚动截图相关模块
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, JavascriptException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

# 导入截图函数
from auto_scoll_shot import take_html_screenshots, take_ppt_style_html_screenshots

# 确保输出目录存在
os.makedirs("frontend/static/outputs", exist_ok=True)
os.makedirs("static/outputs", exist_ok=True)

def render_markdown(markdown_text):
    """渲染Markdown文本为HTML，支持数学公式和高级格式"""
    if not markdown_text:
        return ""

    # 使用Python-Markdown库渲染Markdown，添加更多扩展
    html = markdown.markdown(
        markdown_text,
        extensions=[
            'tables',                # 表格支持
            'fenced_code',           # 代码块支持
            'codehilite',            # 代码高亮
            'toc',                   # 目录支持
            'sane_lists',            # 更好的列表支持
            'smarty',                # 智能标点
            'nl2br',                 # 换行转换为<br>
            'attr_list',             # 属性列表
            'def_list',              # 定义列表
            'footnotes',             # 脚注
            'abbr',                  # 缩写
            'md_in_html'             # HTML中的Markdown
        ],
        extension_configs={
            'codehilite': {
                'linenums': False,
                'use_pygments': True,
                'css_class': 'highlight'
            }
        }
    )

    # 添加MathJax支持，但不添加自定义样式（使用Gradio主题样式）
    html = f"""
    <div class="markdown-body">
        {html}
    </div>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script>
    // 全局错误处理
    window.onerror = function(message, source, lineno, colno, error) {{
        try {{
            const errorData = {{
                message: message,
                source: source,
                lineno: lineno,
                colno: colno,
                stack: error ? error.stack : 'No stack trace'
            }};
            // 发送错误信息到后端
            fetch('/frontend_error_log', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(errorData)
            }});
        }} catch(e) {{
            console.error('Error sending error report:', e);
        }}
        return false;
    }};

    // MathJax配置
    MathJax = {{
        tex: {{
            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
            displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
            processEscapes: true,
            processEnvironments: true,
            processRefs: true,
            tags: 'ams',
            tagSide: 'right',
            tagIndent: '0.8em',
            multlineWidth: '85%',
            maxMacros: 1000,
            maxBuffer: 5 * 1024
        }},
        options: {{
            skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
            processEscapes: true,
            processEnvironments: true
        }}
    }};
    </script>
    """

    return html

def process_pdf(pdf_file, progress=gr.Progress()):
    """处理PDF文件并返回结果"""
    if not pdf_file:
        return "请先上传PDF文件", None

    # 定义安全的进度回调函数
    def safe_progress_callback(value, desc=""):
        try:
            if progress is not None:
                progress(value, desc)
        except Exception as e:
            print(f"进度更新错误: {str(e)}")

    try:
        # 保存上传的PDF
        pdf_path, temp_dir = save_uploaded_pdf(pdf_file)

        # 设置输出目录
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = f"static/outputs/output_{timestamp}"

        safe_progress_callback(0.1, "PDF已保存，准备进行处理...")

        # 调用PDF处理函数
        success, message, markdown_content, json_content = process_pdf_file(
            pdf_path,
            output_dir,
            progress_callback=safe_progress_callback
        )

        if not success:
            return f"<div style='color: red; padding: 20px; border: 1px solid red; border-radius: 5px;'><h3>处理失败</h3><p>{message}</p></div>", None

        # 使用增强的render_markdown函数渲染Markdown内容
        rendered_html = render_markdown(markdown_content)

        return rendered_html, output_dir
    except Exception as e:
        return f"<div style='color: red; padding: 20px; border: 1px solid red; border-radius: 5px;'><h3>处理错误</h3><p>处理PDF文件时发生错误: {str(e)}</p></div>", None

def is_slide_style_html(html_file_path, chromedriver_path=None):
    """
    启发式检测HTML文件是否为PPT幻灯片风格。
    主要通过查找是否存在'.slide'或'.slide-page'类名的元素。
    """
    print(f"开始检测HTML风格: {html_file_path}")
    html_file_url = f"file://{os.path.abspath(html_file_path)}"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=800,600")
    chrome_options.add_argument("--log-level=3")

    try:
        if WEBDRIVER_MANAGER_AVAILABLE:
            service = Service(ChromeDriverManager().install())
        else:
            service = Service(chromedriver_path) if chromedriver_path else Service()
    except Exception:
        service = Service(chromedriver_path) if chromedriver_path else Service()

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(html_file_url)
        driver.implicitly_wait(3)

        # 检查是否存在 .slide 元素
        slide_elements = driver.find_elements(By.CLASS_NAME, "slide")
        if slide_elements:
            print(f"检测到 '.slide' 元素 ({len(slide_elements)}个)，判定为PPT风格。")
            return True

        # 检查是否存在 .slide-page 元素
        slide_page_elements = driver.find_elements(By.CLASS_NAME, "slide-page")
        if slide_page_elements:
            print(f"检测到 '.slide-page' 元素 ({len(slide_page_elements)}个)，判定为PPT风格。")
            return True

        # 检查CSS属性
        body_overflow = driver.execute_script("return getComputedStyle(document.body).overflowY;")
        html_overflow = driver.execute_script("return getComputedStyle(document.documentElement).overflowY;")
        scroll_snap = driver.execute_script("return getComputedStyle(document.body).scrollSnapType || getComputedStyle(document.documentElement).scrollSnapType;")

        if "hidden" in body_overflow or "hidden" in html_overflow:
            print(f"检测到 body/html overflow:hidden，可能为PPT风格。")
            return True

        if scroll_snap and scroll_snap != "none":
            print(f"检测到 scroll-snap-type: {scroll_snap}，可能为PPT风格。")
            return True

        print("未检测到明显的PPT风格特征，判定为普通滚动风格。")
        return False

    except Exception as e:
        print(f"检测HTML风格时出错: {e}。将默认为普通滚动风格。")
        return False
    finally:
        if driver:
            driver.quit()


def generate_screenshots(html_file_path, progress_bar_instance=None, chromedriver_path_for_detection=None, font_scale_percent=125):
    """
    生成HTML文件的截图，自动判断是普通滚动还是PPT幻灯片风格。
    :param html_file_path: HTML文件路径
    :param progress_bar_instance: Gradio的 gr.Progress() 实例 (可选)
    :param chromedriver_path_for_detection: 用于风格检测的ChromeDriver路径 (可选)
    :param font_scale_percent: 字体缩放百分比，默认125%
    :return: 截图文件路径列表
    """
    def update_progress(value, desc):
        try:
            if progress_bar_instance and hasattr(progress_bar_instance, '__call__'):
                progress_bar_instance(value, desc=desc)
            else:
                print(f"进度: {value*100:.0f}% - {desc}")
        except Exception as e:
            # 如果进度条更新失败，只打印到控制台，不影响主要功能
            print(f"进度: {value*100:.0f}% - {desc} (进度条更新失败: {e})")

    try:
        if html_file_path is None or not os.path.exists(html_file_path):
            raise gr.Error("HTML文件不存在，请确保先处理PDF并生成HTML文件")

        update_progress(0.1, "准备截图环境...")
        output_dir = os.path.dirname(html_file_path) or '.'
        base_name_full = Path(html_file_path).stem
        # 从base_name中移除可能的_temp后缀
        base_name = base_name_full[:-5] if base_name_full.endswith('_temp') else base_name_full

        update_progress(0.2, "检测HTML文件风格...")
        is_ppt_style = is_slide_style_html(html_file_path, chromedriver_path_for_detection)

        screenshots_count = 0
        screenshot_files = []

        if is_ppt_style:
            update_progress(0.3, "检测为PPT风格，开始逐页截图...")
            screenshots_count = take_ppt_style_html_screenshots(
                html_file_path,
                width=1200,
                height=1600,
            )
            # 收集PPT风格截图文件
            for f in os.listdir(output_dir):
                if f.startswith(f"{base_name}_slide_") and f.endswith(".png"):
                    screenshot_files.append(os.path.join(output_dir, f))

            # 如果没找到预期的文件名，尝试其他可能的命名
            if not screenshot_files and screenshots_count > 0:
                for i in range(1, screenshots_count + 1):
                    potential_path = os.path.join(output_dir, f"{i}.png")
                    if os.path.exists(potential_path):
                        screenshot_files.append(potential_path)

        else:  # 普通滚动风格
            update_progress(0.3, "检测为普通滚动风格，开始滚动截图...")
            max_scroll_screenshots = 10
            screenshots_count = take_html_screenshots(
                html_file_path,
                width=1080,
                height=1440,
                screenshot_count=max_scroll_screenshots,
                font_scale_percent=font_scale_percent
            )

            # 收集普通滚动截图文件
            for f in os.listdir(output_dir):
                if f.startswith(f"{base_name}_screenshot_") and f.endswith(".png"):
                    screenshot_files.append(os.path.join(output_dir, f))

        update_progress(0.9, f"截图处理完成，共 {len(screenshot_files)} 张。")
        update_progress(1.0, f"成功处理 {len(screenshot_files)} 张截图!")

        return sorted(screenshot_files)

    except gr.Error as e_gr:
        raise e_gr
    except Exception as e:
        error_message = f"截图过程中发生严重错误: {str(e)}"
        update_progress(1.0, f"错误: {error_message}")
        print(error_message)
        import traceback
        traceback.print_exc()
        raise gr.Error(error_message)


def take_screenshots_with_path(output_dir, custom_path=None, font_scale_percent=125, progress=gr.Progress()):
    """
    根据输出目录或自定义路径生成截图
    """
    # 处理自定义路径，去除可能的引号
    if custom_path:
        custom_path = custom_path.strip().strip('"').strip("'")

    if custom_path and os.path.exists(custom_path):
        html_path = custom_path
    elif output_dir:
        # 查找可能的HTML文件
        html_path = None

        # 首先查找固定名称的HTML文件
        possible_html_files = [
            os.path.join(output_dir, "report.html"),
            os.path.join(output_dir, "index.html"),
            os.path.join(output_dir, "output.html")
        ]

        for possible_path in possible_html_files:
            if os.path.exists(possible_path):
                html_path = possible_path
                break

        # 如果没找到固定名称的文件，则查找所有HTML文件
        if not html_path:
            import glob
            # 查找以report_开头的HTML文件（带时间戳的）
            report_pattern = os.path.join(output_dir, "report_*.html")
            report_files = glob.glob(report_pattern)

            if report_files:
                # 如果有多个，选择最新的（按文件名排序，时间戳越大越新）
                html_path = sorted(report_files)[-1]
            else:
                # 查找目录中的任何HTML文件
                all_html_pattern = os.path.join(output_dir, "*.html")
                all_html_files = glob.glob(all_html_pattern)
                if all_html_files:
                    html_path = all_html_files[0]

        if not html_path:
            raise gr.Error(f"在输出目录 {output_dir} 中未找到HTML文件")
    else:
        raise gr.Error("未找到HTML文件路径，请先处理PDF或手动输入HTML路径")

    if not os.path.exists(html_path):
        raise gr.Error(f"HTML文件不存在: {html_path}")

    return generate_screenshots(html_path, progress_bar_instance=progress, font_scale_percent=font_scale_percent)



def create_demo():
    """创建Gradio演示界面"""
    # 设置页面标题和描述
    title = "学术论文OCR与智能解析系统"
    description = """
    ## 学术论文OCR与智能解析系统

    本系统可以对上传的PDF论文进行OCR识别、结构化处理和智能报告生成，完整流程包括：
    1. **OCR识别**：提取PDF中的文本、图表和公式
    2. **结构化处理**：识别论文的章节结构和关键元素
    3. **报告生成**：使用AI生成论文的中文解读报告

    请上传一篇学术论文PDF文件，系统将自动处理并生成结果。
    """

    # 创建Gradio界面
    with gr.Blocks(title=title, css="static/custom.css") as demo:
        gr.Markdown(description)

        # 存储当前输出目录的状态变量
        current_output_dir = gr.State(value=None)

        # PDF处理区域
        with gr.Row():
            with gr.Column():
                pdf_upload = gr.File(label="上传PDF论文", file_types=[".pdf"])
                process_button = gr.Button("开始处理", variant="primary")
                status_message = gr.Markdown("")

                # 截图功能区域
                with gr.Row():
                    screenshot_btn = gr.Button("生成报告截图", variant="secondary")
                    html_path_input = gr.Textbox(label="HTML文件路径（可选）", placeholder="留空则使用自动检测的路径")

                # 字体缩放控件
                with gr.Row():
                    font_scale_slider = gr.Slider(
                        minimum=100,
                        maximum=200,
                        value=125,
                        step=5,
                        label="字体缩放百分比",
                        info="100% = 原始大小，125% = 放大25%"
                    )

        # 结果展示区域
        with gr.Tabs() as tabs:
            with gr.TabItem("报告内容"):
                result_html = gr.HTML(label="处理结果")
            with gr.TabItem("报告截图"):
                screenshot_gallery = gr.Gallery(
                    label="报告截图预览",
                    show_label=True,
                    columns=2,
                    rows=3,
                    height=600
                )
            with gr.TabItem("处理流程说明"):
                gr.Markdown("""
                ## 处理流程说明

                本系统处理PDF论文的完整流程如下：

                1. **OCR识别（约占40%进度）**
                   - 使用高精度OCR引擎提取PDF中的文本内容
                   - 识别图表、公式和特殊符号
                   - 生成初步的Markdown文本

                2. **结构化处理（约占20%进度）**
                   - 分析论文结构，识别章节、标题和段落
                   - 提取关键元素（图表、公式、表格等）
                   - 生成结构化JSON数据

                3. **报告生成（约占30%进度）**
                   - 基于结构化数据，使用AI生成中文解读报告
                   - 解释论文的主要内容、方法和结论
                   - 分析关键图表和公式的含义

                4. **结果整合（约占10%进度）**
                   - 整合处理结果，生成最终报告
                   - 格式化输出，优化显示效果
                """)

        # 按钮事件处理
        process_button.click(
            fn=process_pdf,
            inputs=[pdf_upload],
            outputs=[result_html, current_output_dir]
        )

        # 截图按钮事件处理
        screenshot_btn.click(
            fn=take_screenshots_with_path,
            inputs=[current_output_dir, html_path_input, font_scale_slider],
            outputs=screenshot_gallery
        )

    return demo

def log_frontend_error(error_message):
    """记录前端错误到专门的前端日志"""
    frontend_logger.error(f"前端错误: {error_message}")
    return "错误已记录"

if __name__ == "__main__":
    # 创建Gradio演示界面
    demo = create_demo()

    # 添加Flask路由处理前端错误日志
    from flask import request, jsonify, send_from_directory

    print("应用程序配置完成，准备启动...")

    @demo.app.route('/frontend_error_log', methods=['POST'])
    def frontend_error_log():
        try:
            error_data = request.json
            print(f"收到前端错误数据: {error_data}")  # 打印到控制台

            if not error_data:
                logger.warning("收到空的前端错误数据")
                return jsonify({"status": "error", "message": "空的错误数据"})

            error_message = f"前端JS错误: {error_data.get('message', '未知错误')} - 源文件: {error_data.get('source', '未知')} - 行号: {error_data.get('lineno', 0)} - 列号: {error_data.get('colno', 0)}"
            frontend_logger.error(error_message)

            if 'stack' in error_data and error_data['stack']:
                frontend_logger.error(f"错误堆栈: {error_data['stack']}")
            else:
                frontend_logger.error("错误堆栈: 无堆栈信息")

            return jsonify({"status": "success", "message": "错误已记录"})
        except Exception as e:
            print(f"处理前端错误日志时出错: {str(e)}")  # 打印到控制台
            logger.error(f"处理前端错误日志时出错: {str(e)}")
            return jsonify({"status": "error", "message": str(e)})

    # 添加测试前端错误日志的路由
    @demo.app.route('/test_frontend_error', methods=['GET'])
    def test_frontend_error():
        try:
            frontend_logger.debug("测试前端日志 - DEBUG级别")
            frontend_logger.info("测试前端日志 - INFO级别")
            frontend_logger.warning("测试前端日志 - WARNING级别")
            frontend_logger.error("测试前端日志 - ERROR级别")
            frontend_logger.critical("测试前端日志 - CRITICAL级别")
            return jsonify({
                "status": "success",
                "message": "测试日志已记录，请检查frontend_*.log文件"
            })
        except Exception as e:
            logger.error(f"测试前端错误日志时出错: {str(e)}")
            return jsonify({"status": "error", "message": str(e)})

    # 添加manifest.json路由
    @demo.app.route('/manifest.json')
    def manifest():
        try:
            return send_from_directory('frontend/static', 'manifest.json')
        except:
            # 如果文件不存在，返回默认配置
            return jsonify({
                "name": "学术论文OCR与智能解析系统",
                "short_name": "论文OCR",
                "start_url": "/",
                "display": "standalone",
                "background_color": "#ffffff",
                "theme_color": "#ff6b35",
                "description": "一个用于解析学术论文的OCR系统",
                "icons": [
                    {
                        "src": "static/images/icon.png",
                        "sizes": "192x192",
                        "type": "image/png"
                    }
                ]
            })

    # 添加静态文件处理路由
    @demo.app.route('/static/<path:filename>')
    def serve_static_files(filename):
        try:
            return send_from_directory('frontend/static', filename)
        except:
            return '', 404

    # 添加字体文件处理路由
    @demo.app.route('/<path:filename>')
    def serve_other_files(filename):
        # 处理字体文件和其他静态资源
        if filename.endswith(('.woff2', '.woff', '.ttf', '.eot', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg')):
            try:
                # 首先尝试从frontend/static目录
                return send_from_directory('frontend/static', filename)
            except:
                try:
                    # 然后尝试从static目录
                    return send_from_directory('static', filename)
                except:
                    # 返回一个空响应，避免404错误
                    return '', 200
        return '', 404

    # 启动Gradio应用
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        debug=False,
        show_error=True,
        quiet=False
    )