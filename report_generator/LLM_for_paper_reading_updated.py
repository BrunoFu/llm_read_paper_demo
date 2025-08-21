import re
import json
import os
from openai import AsyncOpenAI, APIConnectionError, APIError
from pathlib import Path
import asyncio
from tqdm import tqdm
import aiofiles
# 导入配置文件
try:
    from ..utils.llm_config import (
        LLM_CONFIG, CURRENT_API, MAX_RETRIES, SAVE_INTERVAL,
        get_default_model, get_api_config, set_current_api
    )
    # 导入报告处理模块
    from .report_processor import process_report
except ImportError:
    # 向后兼容的导入方式
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.llm_config import (
        LLM_CONFIG, CURRENT_API, MAX_RETRIES, SAVE_INTERVAL,
        get_default_model, get_api_config, set_current_api
    )
    from report_generator.report_processor import process_report

# 初始化客户端函数
def initialize_client(api_name=None):
    """初始化OpenAI客户端"""
    api = api_name or CURRENT_API
    config = LLM_CONFIG[api]
    
    # 获取API密钥(优先使用direct key，如果没有则从环境变量获取)
    api_key = config.get("api_key")
    if not api_key and "api_key_env" in config:
        api_key = os.environ.get(config["api_key_env"])
        if not api_key:
            raise ValueError(f"缺少API密钥，请设置环境变量 {config['api_key_env']} 或直接提供 api_key")
    
    # 初始化客户端
    return AsyncOpenAI(
        api_key=api_key,
        base_url=config["api_url"],
    )

# 初始化客户端
client = initialize_client()

async def get_openai_response_conversation(conversation, max_retries=5, reasoner=False):
    retries = 0
    while retries <= max_retries:
        try:
            # 确保最后一条消息是user角色
            if conversation[-1]["role"] != "user":
                # 如果最后一条不是user，调整消息顺序或角色
                if conversation[-1]["role"] == "system":
                    # 将system消息改为user消息
                    conversation[-1]["role"] = "user"
            response = await client.chat.completions.create(
                model=get_default_model(),  # 使用配置的模型
                messages=conversation,
                temperature=0.7
            )
            assistant_reply = response.choices[0].message.content
            if assistant_reply is None:
                assistant_reply = ""
            assistant_reply = assistant_reply.strip()
            
            if reasoner and "</think>" in assistant_reply:
                processed_reply = assistant_reply.split("</think>", 1)[1].strip()
                conversation.append({"role": "assistant", "content": assistant_reply})
                return processed_reply
            else:
                conversation.append({"role": "assistant", "content": assistant_reply})
                return assistant_reply
                
        except APIConnectionError as e:
            retries += 1
            print(f"API 连接失败: {str(e)}，等待{2 ** retries}秒后重试...（重试次数：{retries}/{max_retries}）")
            if retries > max_retries:
                raise Exception(f"API 连接失败: 超过重试次数")
            await asyncio.sleep(2 ** retries)  # 指数退避
            continue
            
        except APIError as e:
            retries += 1
            error_message = str(e)
            print(f"API 错误: {error_message}，等待{2 ** retries}秒后重试...（重试次数：{retries}/{max_retries}）")
            if retries > max_retries:
                raise Exception(f"API 错误: {error_message}")
            await asyncio.sleep(2 ** retries)
            continue
            
        except asyncio.TimeoutError:
            retries += 1
            print(f"请求超时，等待{2 ** retries}秒后重试...（重试次数：{retries}/{max_retries}）")
            if retries > max_retries:
                raise Exception(f"请求超时: 超过重试次数")
            await asyncio.sleep(2 ** retries)
            continue
            
        except json.JSONDecodeError as e:
            retries += 1
            print(f"JSON解析错误: {str(e)}，等待{2 ** retries}秒后重试...（重试次数：{retries}/{max_retries}）")
            if retries > max_retries:
                raise Exception(f"JSON解析错误: {str(e)}")
            await asyncio.sleep(2 ** retries)
            continue
            
        except Exception as e:
            # 检查是否为JSON相关错误
            error_str = str(e)
            if "Expecting value" in error_str or "Invalid JSON" in error_str or "JSONDecodeError" in error_str:
                retries += 1
                print(f"JSON相关错误: {error_str}，等待{2 ** retries}秒后重试...（重试次数：{retries}/{max_retries}）")
                if retries > max_retries:
                    raise Exception(f"JSON相关错误: 超过重试次数 - {error_str}")
                await asyncio.sleep(2 ** retries)
                continue
            else:
                raise Exception(f"未处理的异常: {str(e)}")

async def generate_report(json_result, output_path, reasoner=False, max_concurrency=5, progress_callback=None):
    # 从json_result中提取level=0的text_content作为全文内容
    full_text = ""
    for section in json_result:
        if section.get("level", -1) == 0:
            full_text = section.get("text_content", "")
            break
    
    if not full_text:
        print("警告：未找到level=0的文本内容，将使用空字符串作为全文")
    
    semaphore = asyncio.Semaphore(max_concurrency)
    # 添加一个列表来存储所有的prompt
    all_prompts = []

    # 过滤掉以下情况的章节:
    # 1. level为0且title包含reference, data availability等关键词的条目
    # 2. 标准章节名称如Abstract, Introduction等，除非它们有内容
    standard_sections = ["abstract", "introduction", "data", "institutional details", 
                        "facts", "theoretical framework", "policy implications", 
                        "model calibration", "conclusion"]
    
    filtered_json_result = []
    for section in json_result:
        # 检查是否是要过滤的章节
        title_lower = section.get("title", "").lower()
        
        # 过滤条件1: 包含特定关键词的章节
        if re.search(r"reference|data availability|acknowledgments|supplementary material|keywords", title_lower, re.I):
            continue
            
        # 过滤条件2: 标准章节名称且没有内容
        if any(std_section in title_lower for std_section in standard_sections) and not section.get("text_content", "").strip():
            print(f"跳过空章节: {section.get('title', '')}")
            continue
            
        filtered_json_result.append(section)
    
    json_result = filtered_json_result
    print(f"过滤后剩余章节数: {len(json_result)}")

    # 封装带索引的任务，增加重试机制
    async def wrapped_task(index, task_func, prompt_info=None, max_retries=3):
        async with semaphore:
            retry_count = 0
            while retry_count <= max_retries:
                try:
                    # 记录prompt信息
                    if prompt_info and retry_count == 0:  # 只在第一次尝试时记录prompt
                        all_prompts.append(prompt_info)
                    
                    # 如果是异步任务而非协程函数，直接返回索引和任务
                    if isinstance(task_func, asyncio.Task):
                        return index, await task_func
                    
                    # 否则执行协程函数并返回结果
                    return index, await task_func
                except Exception as e:
                    retry_count += 1
                    error_msg = f"章节 {index} 处理失败: {str(e)}"
                    if retry_count <= max_retries:
                        wait_time = 2 ** retry_count  # 指数退避
                        print(f"{error_msg} - 等待 {wait_time} 秒后重试... (尝试 {retry_count}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"{error_msg} - 超过最大重试次数，标记为失败")
                        return index, f"（内容生成失败：{str(e)}，已尝试 {max_retries} 次）"
    
    paper_title = json_result[0].get("title", "论文报告")
    markdown_results = [f"# {paper_title}\n ## 论文整体概括\n"]

    # 记录整体概括的prompt
    overall_prompt = f"阅读下面整篇论文内容，使用中文概括主要内容：\n{full_text[:200]}..."  # 截取部分内容以避免JSON文件过大
    all_prompts.append({
        "section": "整体概括",
        "prompt": overall_prompt,
        "timestamp": None  # 可以添加时间戳
    })
    
    # 异步处理整体概括
    overall_task = get_openai_response_conversation(
        [{"role": "system", "content": f"阅读下面整篇论文内容，使用中文概括主要内容：\n{full_text}"}],
        reasoner=reasoner
    )
    markdown_results.append(await overall_task + "\n")

    print("开始处理各章节...")

    # 并行处理各章节
    section_tasks = []
    section_metadata = []

    for section in json_result[1:]:
        level = section.get("level", 0)
        if level == 0:
            continue  # 跳过 level=0 的章节

        section_title = section.get("title", "untitled content")
        # 适配新的JSON结构：使用text_content替代contents
        section_content = section.get("text_content", "").strip()
        formulas = section.get("formulas", [])
        figures = section.get("figures", [])
        tables = section.get("tables", [])
        sub_title_list = section.get("sub_title_list", [])  # 适配新的JSON结构
        
        # 检查section_content是否为空
        if not section_content:
            print(f"跳过空内容章节: {section_title}")
            continue  # 直接跳过空内容章节，不再添加任务或元数据

        # 系统消息内容
        system_content = f"""以下是论文中章节 \"{section_title}\" 的内容, 请仔细阅读，使用中文完成我的任务，注意将输出内容好好组织一下，用一些markdown排版的语法，比如加粗、无序列表、小标题等。在输出公式时，检查一下公式是否正确（检查是否正确的内容不用输出）。在回答时，直接输出对内容的讲解，不要输出\"好的\"、\"明白了\"、等无意义的内容。当输出行间公式时，采用下面的格式：
        \\[
        公式内容
        \\]
        """

        user_prompt = f"请阅读章节 \"{section_title}\"，先讲解其主要内容。"
        
        # 简化图片处理逻辑
        if figures and len(figures) > 0:
            figures_str = ", ".join(figures)
            user_prompt += f" 然后描述涉及的图片 {figures_str}，包括图片上的内容是什么，图片支持了文章的哪些论述。"
        
        # 简化表格处理逻辑
        if tables and len(tables) > 0:
            tables_str = ", ".join(tables)
            user_prompt += f" 然后描述涉及的表格 {tables_str}，在学术研究中，表格通常包含丰富的信息，请你给我讲解这个表格的内容是什么，表格支持了文章的哪些论文（不需要输出表格具体内容）。"
            
        if formulas:
            formulas_str = ", ".join(formulas)
            user_prompt += f" 此外，请结合文章内容解释以下公式：{formulas_str}。公式输出使用markdown的行间公式格式（\\[ ... \\]）。"

        user_prompt += "小标题以markdown四级标题（####）格式给出。"
        user_prompt += f" 章节内容：\n{section_content}"
        
        # 合并系统消息和用户提示为一个完整的提示词
        combined_prompt = f"{system_content}\n\n{user_prompt}"
        
        # 记录该章节的prompt信息
        prompt_info = {
            "section": section_title,
            "level": level,
            "prompt": combined_prompt,
            "system_message": system_content
        }
        
        # 创建带索引的任务，使用合并后的提示词
        task = wrapped_task(
            len(section_tasks),  # 记录原始索引
            get_openai_response_conversation(
                [{"role": "user", "content": combined_prompt}],  # 只传递一个用户消息
                reasoner=reasoner
            ),
            prompt_info,
            max_retries=5  # 为重要章节设置更多的重试次数
        )
        section_tasks.append(task)
        section_metadata.append({
            "title": section_title,
            "level": level,
            "index": len(section_tasks)-1,  # 记录任务索引
            "empty_content": False,  # 标记为非空内容
        })
    
    # 如果提供了进度回调函数，通知开始处理并传递总章节数
    if progress_callback:
        asyncio.create_task(progress_callback(len(section_tasks)))

    # 处理带索引的结果
    sorted_results = {}
    for future in tqdm(asyncio.as_completed(section_tasks), total=len(section_tasks)):
        try:
            index, result = await future
            # 处理空内容任务的特殊情况
            if isinstance(result, asyncio.Task):
                await result  # 等待占位任务完成
                sorted_results[index] = ""  # 为空内容任务设置空字符串结果
            else:
                sorted_results[index] = result
        except Exception as e:
            print(f"处理任务结果时出错: {str(e)}")
            # 这里不会阻止其他任务继续执行

    # 按原始顺序构建Markdown
    for index in range(len(section_tasks)):
        result = sorted_results.get(index, "（内容缺失）")
        meta = next(m for m in section_metadata if m["index"] == index)
        
        # 根据level动态生成标题级别
        heading_level = "#" * meta["level"]
        
        # 对于非空内容的章节，正常添加标题和内容
        markdown_results.append(f"{heading_level} {meta['title']}\n{result}\n\n")

    # 异步写入结果
    output_file = Path(output_path) / "report.md"
    async with aiofiles.open(output_file, "w", encoding="utf-8") as f:
        await f.write("\n".join(markdown_results))
    
    # 保存所有prompt到JSON文件
    prompts_file = Path(output_path) / "prompts.json"
    async with aiofiles.open(prompts_file, "w", encoding="utf-8") as f:
        await f.write(json.dumps(all_prompts, ensure_ascii=False, indent=2))
    
    print(f"初始报告已生成，等待进一步处理...")
    
    return all_prompts

async def process_paper_report(json_path, output_path, reasoner=True):
    """处理论文并生成报告"""
    # 加载JSON文件
    with open(json_path, 'r', encoding='utf-8') as f:
        json_result = json.load(f)
    
    # 生成初始报告
    await generate_report(json_result, output_path, reasoner=reasoner)
    
    # 使用报告处理模块处理报告文件
    report_file = Path(output_path) / "report.md"
    
    # 从json_path中提取pdf名称
    pdf_name = os.path.basename(os.path.dirname(os.path.dirname(json_path)))
    
    # 处理报告文件
    final_report_path = await process_report(
        report_file_path=report_file,
        output_path=output_path,
        pdf_name=pdf_name
    )
    
    print(f"论文报告生成完成: {final_report_path}")
    return final_report_path

if __name__ == "__main__":
    # 示例用法
    json_path = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/complete_20250713_182557/complete_20250713_182616/json/structure_with_content_updated.json"
    output_path = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/complete_20250713_182557"
    
    asyncio.run(process_paper_report(json_path, output_path)) 