import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
import argparse
from selenium.common.exceptions import JavascriptException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def take_html_screenshots(html_file_path, width=1080, height=1440, screenshot_count=18, chromedriver_path=None, font_scale_percent=125):
    """直接对HTML文件进行滚动截图，支持字体缩放"""
    # 检查HTML文件是否存在
    if not os.path.isfile(html_file_path):
        raise FileNotFoundError(f"HTML文件不存在: {html_file_path}")
    
    # 转换为文件URL
    html_file_url = f"file://{os.path.abspath(html_file_path)}"
    print(f"正在加载HTML文件: {html_file_url}")
    
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument(f"--window-size={width},{height}")
    chrome_options.add_argument("--log-level=3")  # 减少日志输出

    # Windows特定选项
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--force-device-scale-factor=1")
    
    # 设置WebDriver
    driver = None
    max_retries = 3

    for attempt in range(max_retries):
        try:
            print(f"尝试启动Chrome WebDriver (第 {attempt + 1}/{max_retries} 次)...")

            if chromedriver_path:
                service = Service(chromedriver_path)
            elif WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    service = Service(ChromeDriverManager().install())
                except Exception as e:
                    print(f"webdriver-manager安装失败: {e}")
                    service = Service()
            else:
                # 尝试使用系统的ChromeDriver
                service = Service()

            # 尝试创建WebDriver
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Chrome WebDriver启动成功！")
            break

        except Exception as e:
            print(f"第 {attempt + 1} 次启动失败: {e}")
            if attempt < max_retries - 1:
                print("等待5秒后重试...")
                time.sleep(5)
                # 尝试清理可能的Chrome进程
                try:
                    import subprocess
                    subprocess.run(["taskkill", "/f", "/im", "chrome.exe"],
                                 capture_output=True, check=False)
                    subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"],
                                 capture_output=True, check=False)
                except:
                    pass
            else:
                raise Exception(f"经过 {max_retries} 次尝试后仍无法启动Chrome WebDriver: {e}")

    if driver is None:
        raise Exception("无法创建Chrome WebDriver实例")
    
    try:
        driver.get(html_file_url)
        
        # 给页面足够的加载时间 - 增加等待时间以确保内容渲染完成
        print("等待页面加载和渲染...")
        time.sleep(5)  # 等待基本内容加载
        
        # 执行JavaScript等待MathJax渲染完成
        print("等待MathJax公式渲染...")
        driver.execute_script("""
            function waitForMathJax() {
                if (window.MathJax && window.MathJax.typesetPromise) {
                    return window.MathJax.typesetPromise()
                        .then(() => {
                            console.log("MathJax渲染完成");
                            return true;
                        })
                        .catch((err) => {
                            console.error("MathJax渲染错误:", err);
                            return false;
                        });
                } else {
                    console.log("找不到MathJax对象");
                    return Promise.resolve(false);
                }
            }
            return waitForMathJax();
        """)
        
        # 额外等待以确保渲染完成
        time.sleep(3)
        
        # ---- 注入 CSS 进行字体缩放 ----
        if font_scale_percent > 100:
            print(f"注入自定义 CSS，字体放大到 {font_scale_percent}%...")
            custom_css_script = f"""
            var style = document.createElement('style');
            style.type = 'text/css';
            style.innerHTML = `
                /* 全局字体缩放 */
                html {{ 
                    font-size: {font_scale_percent}% !important; 
                }}
                
                /* 调整行高以适应更大字体 */
                body {{ 
                    line-height: 1.6 !important;
                    overflow-x: hidden !important; /* 隐藏可能的水平滚动条 */
                }}
                
                /* 标题字体调整 */
                h1 {{ font-size: 2.5em !important; }}
                h2 {{ font-size: 2em !important; }}
                h3 {{ font-size: 1.75em !important; }}
                h4 {{ font-size: 1.5em !important; }}
                h5 {{ font-size: 1.25em !important; }}
                h6 {{ font-size: 1.1em !important; }}
                
                /* 正文和列表字体 */
                p, li, td, th, div {{
                    font-size: 1em !important;
                }}
                
                /* 代码块字体 */
                pre, code {{
                    font-size: 0.95em !important;
                    line-height: 1.4 !important;
                }}
                
                /* 引用块字体 */
                blockquote {{
                    font-size: 1em !important;
                    line-height: 1.5 !important;
                }}
                
                /* MathJax 公式缩放 */
                mjx-container {{
                    font-size: 1em !important;
                }}
                
                .MathJax {{
                    font-size: 1em !important;
                }}
                
                /* 表格字体 */
                table {{
                    font-size: 1em !important;
                }}
                
                /* 链接字体 */
                a {{
                    font-size: inherit !important;
                }}
                
                /* 其他可能的文本元素 */
                span, em, strong, b, i {{
                    font-size: inherit !important;
                }}
            `;
            document.head.appendChild(style);
            console.log('自定义大字体 CSS 已注入，字体缩放：{font_scale_percent}%');
            """
            
            try:
                driver.execute_script(custom_css_script)
                print("CSS 注入成功")
                time.sleep(2)  # 给CSS应用足够的时间
            except Exception as e:
                print(f"注入CSS时出错: {{e}}")
        else:
            print("字体缩放比例 <= 100%，跳过字体放大")
        
        # 重新获取文档高度（CSS修改后可能发生变化）
        doc_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
        window_height = driver.execute_script("return window.innerHeight")
        
        print(f"字体缩放后 - 文档总高度: {doc_height}像素, 窗口高度: {window_height}像素")
        
        # 确定保存截图的位置
        folder_path = os.path.dirname(html_file_path) or '.'
        base_name = os.path.splitext(os.path.basename(html_file_path))[0]
        
        # 从base_name中移除可能的_temp后缀
        if base_name.endswith('_temp'):
            base_name = base_name[:-5]
        
        screenshots_taken = 0
        current_scroll = 0
        
        while screenshots_taken < screenshot_count:
            # 截图
            screenshot_path = os.path.join(folder_path, f"{base_name}_screenshot_{screenshots_taken+1}.png")
            driver.save_screenshot(screenshot_path)
            screenshots_taken += 1
            print(f"已保存截图 {screenshots_taken}/{screenshot_count}: {screenshot_path}")
            
            # 检查是否已到达文档底部
            if current_scroll >= doc_height - window_height:
                print("已到达文档底部")
                break
            
            # 向下滚动一个窗口高度
            current_scroll += window_height
            driver.execute_script(f"window.scrollTo(0, {current_scroll});")
            
            # 短暂延迟以确保渲染完成
            time.sleep(2)
    
    finally:
        # 关闭浏览器
        driver.quit()
    
    print(f"完成！已为 {html_file_path} 生成 {screenshots_taken} 张截图")
    return screenshots_taken

def take_ppt_style_html_screenshots(html_file_path, width=1920, height=1080, chromedriver_path=None, max_screenshots=None):
    """
    对PPT风格的HTML文件进行逐个slide截图。
    每个slide应该是一个独立的、可滚动到的全屏元素。
    支持 .slide 和 .slide-page 类名。
    """
    if not os.path.isfile(html_file_path):
        raise FileNotFoundError(f"HTML文件不存在: {html_file_path}")

    html_file_url = f"file://{os.path.abspath(html_file_path)}"
    print(f"正在加载HTML文件: {html_file_url}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--remote-debugging-port=9223")
    chrome_options.add_argument(f"--window-size={width},{height}") # 设置窗口大小以匹配视口
    chrome_options.add_argument("--hide-scrollbars") # 尝试隐藏滚动条
    chrome_options.add_argument("--log-level=3")

    # Windows特定选项
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--force-device-scale-factor=1")

    driver = None
    max_retries = 3

    for attempt in range(max_retries):
        try:
            print(f"尝试启动Chrome WebDriver (第 {attempt + 1}/{max_retries} 次)...")

            if chromedriver_path:
                service = Service(chromedriver_path)
            elif WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    service = Service(ChromeDriverManager().install())
                except Exception as e:
                    print(f"webdriver-manager安装失败: {e}")
                    service = Service()
            else:
                service = Service() # 尝试使用系统路径的ChromeDriver

            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Chrome WebDriver启动成功！")
            break

        except Exception as e:
            print(f"第 {attempt + 1} 次启动失败: {e}")
            if attempt < max_retries - 1:
                print("等待5秒后重试...")
                time.sleep(5)
                # 尝试清理可能的Chrome进程
                try:
                    import subprocess
                    subprocess.run(["taskkill", "/f", "/im", "chrome.exe"],
                                 capture_output=True, check=False)
                    subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"],
                                 capture_output=True, check=False)
                except:
                    pass
            else:
                raise Exception(f"经过 {max_retries} 次尝试后仍无法启动Chrome WebDriver: {e}")

    if driver is None:
        raise Exception("无法创建Chrome WebDriver实例")

    folder_path = os.path.dirname(html_file_path) or '.'
    base_name_full = os.path.splitext(os.path.basename(html_file_path))[0]
    base_name = base_name_full[:-5] if base_name_full.endswith('_temp') else base_name_full

    screenshots_taken = 0
    try:
        driver.get(html_file_url)
        print("等待页面基本加载...")
        time.sleep(3) # 初始加载

        # 等待并确认 MathJax 渲染
        print("等待MathJax公式渲染...")
        try:
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("""
                    if (window.MathJax && typeof window.MathJax.typesetPromise === 'function') {
                        return window.MathJax.typesetPromise().then(() => true).catch(() => false);
                    }
                    return document.readyState === 'complete'; // Fallback if MathJax not found or already done
                """)
            )
            print("MathJax渲染（或页面加载）完成。")
        except TimeoutException:
            print("MathJax渲染超时或未找到。继续截图...")
        except JavascriptException as e:
            print(f"MathJax检查脚本执行错误: {e}。继续截图...")
        
        time.sleep(2) # MathJax渲染后额外等待

        # 查找所有的 slide 元素，优先查找 .slide，如果没有则查找 .slide-page
        slide_elements = driver.find_elements(By.CLASS_NAME, "slide")
        slide_class_name = "slide"
        
        if not slide_elements:
            print("未找到 '.slide' 元素，尝试查找 '.slide-page' 元素...")
            slide_elements = driver.find_elements(By.CLASS_NAME, "slide-page")
            slide_class_name = "slide-page"
        
        if not slide_elements:
            print("错误：在页面中未找到 '.slide' 或 '.slide-page' 元素。请确保HTML结构正确。")
            return 0
        
        num_slides = len(slide_elements)
        print(f"检测到 {num_slides} 个幻灯片 ('{slide_class_name}' 元素)。")

        screenshots_to_take = num_slides
        if max_screenshots is not None and max_screenshots < num_slides:
            screenshots_to_take = max_screenshots
            print(f"将截图数量限制为: {max_screenshots}")

        for i in range(screenshots_to_take):
            slide = slide_elements[i]
            slide_id = slide.get_attribute("id") or f"index_{i}"
            print(f"\n正在处理幻灯片 {i+1}/{screenshots_to_take} (ID/Index: {slide_id})...")

            # 1. 将slide滚动到视图中
            try:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'start'});", slide)
                print(f"已滚动到幻灯片: {slide_id}")
            except Exception as e:
                print(f"滚动到幻灯片 {slide_id} 失败: {e}")
                continue

            # 2. 等待slide内容和动画完成
            print("等待幻灯片动画和内容渲染...")
            try:
                # 等待slide本身和其主要内容卡片可见
                WebDriverWait(driver, 10).until(
                    EC.visibility_of(slide)
                )
                # 尝试等待内部的 main-card 可见，如果存在的话
                main_cards_in_slide = slide.find_elements(By.CLASS_NAME, "main-card")
                if main_cards_in_slide:
                     WebDriverWait(driver, 10).until(
                        EC.visibility_of(main_cards_in_slide[0]) # 假设至少一个main-card会触发动画
                    )
                print("Slide动画和主要内容已变为可见。")
            except TimeoutException:
                print(f"等待幻灯片 {slide_id} 的 'is-visible' 状态超时。可能动画未按预期工作或选择器错误。仍尝试截图。")
            
            time.sleep(2.5) # 关键：给予足够的时间让CSS过渡/动画完成，尤其是复杂的交错动画

            # 3. 截图当前视口 (即当前slide)
            # 修改为使用简单数字作为文件名
            screenshot_name = f"{screenshots_taken+1}.png"  # 直接使用数字作为文件名
            screenshot_path = os.path.join(folder_path, screenshot_name)
            
            if driver.save_screenshot(screenshot_path):
                screenshots_taken += 1
                print(f"已保存截图 {screenshots_taken}/{screenshots_to_take}: {screenshot_path}")
            else:
                print(f"保存截图失败: {screenshot_path}")

    except Exception as e:
        print(f"截图过程中发生错误: {e}")
    finally:
        driver.quit()

    print(f"\n完成！已为 {html_file_path} 生成 {screenshots_taken} 张幻灯片截图。")
    return screenshots_taken


def main():
    parser = argparse.ArgumentParser(description='对HTML文件进行自动滚动截图')
    parser.add_argument('--html_file', type=str,
                        default=r"/Users/fro/Library/CloudStorage/OneDrive-个人/code/LLM速读论文/output_hornbeck2017/report.html",
                        help='HTML文件的路径 (默认: report_temp.html)')
    parser.add_argument('--count', type=int, default=17, help='要截取的图片数量（默认：18）')
    parser.add_argument('--width', type=int, default=1920, help='截图宽度（像素）（默认：803）')
    parser.add_argument('--height', type=int, default=1080, help='截图高度（像素）（默认：1304）')
    parser.add_argument('--chromedriver', help='ChromeDriver可执行文件的路径（可选）')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.isfile(args.html_file):
        print(f"错误：找不到HTML文件 '{args.html_file}'")
        return
    
    # 检查依赖项
    try:
        import selenium
    except ImportError:
        print("错误：未安装Selenium包。请使用以下命令安装：")
        print("pip install selenium")
        return
    
    if not WEBDRIVER_MANAGER_AVAILABLE and not args.chromedriver:
        print("警告：未安装webdriver-manager。为了自动安装ChromeDriver，请安装：")
        print("pip install webdriver-manager")
        print("或者，您可以使用--chromedriver参数指定ChromeDriver的路径")
    
    try:
        screenshots_taken = take_html_screenshots(
            args.html_file, 
            args.width, 
            args.height, 
            args.count,
            args.chromedriver
        )
        if screenshots_taken < args.count:
            print(f"注意：由于已到达文档底部，只截取了 {screenshots_taken} 张图片。")
    except Exception as e:
        print(f"错误：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()