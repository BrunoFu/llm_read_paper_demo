#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM客户端工具

用于调用大模型API提取元数据
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional, List, Union

# 尝试导入OpenAI库
try:
    import openai
    from openai import AsyncOpenAI, APIConnectionError, APIError
    openai_available = True
except ImportError:
    print("警告: 未安装openai库，请使用 'pip install openai' 安装")
    openai_available = False

# 尝试导入json_repair
try:
    from json_repair import repair_json
except ImportError:
    print("警告: 未安装json_repair库，请使用 'pip install json-repair' 安装")
    def repair_json(json_str):
        """简单的JSON修复函数，当json_repair库不可用时使用"""
        return json_str

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入prompt工具
from utils.prompt_utils import fill_prompt_with_document, extract_json_from_response

# 导入LLM配置
from utils.llm_config import LLM_CONFIG, get_default_model, get_api_config, set_current_api, CURRENT_API, MAX_RETRIES

class LLMClient:
    """LLM客户端类"""
    
    def __init__(self, api_name: Optional[str] = None):
        """
        初始化LLM客户端
        
        Args:
            api_name: API名称，如果为None则使用当前API
        """
        self.api_name = api_name or CURRENT_API
        self.config = get_api_config(self.api_name)
        
        # 获取API密钥
        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError(f"缺少API密钥，请在llm_config.py中为{self.api_name}配置api_key")
        
        # 初始化客户端
        if not openai_available:
            raise ImportError("未安装openai库，无法初始化客户端")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.config["api_url"]
        )
    
    async def get_completion(
        self, 
        prompt: str, 
        model: Optional[str] = None, 
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        max_retries: int = MAX_RETRIES
    ) -> str:
        """
        获取LLM完成结果
        
        Args:
            prompt: 提示词
            model: 模型名称，如果为None则使用默认模型
            temperature: 温度参数
            max_tokens: 最大生成token数
            max_retries: 最大重试次数
            
        Returns:
            LLM响应文本
        """
        model_name = model or self.config["default_model"]
        retries = 0
        
        while retries <= max_retries:
            try:
                response = await self.client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                return response.choices[0].message.content
                
            except APIConnectionError as e:
                retries += 1
                print(f"API 连接失败: {str(e)}，等待{2 ** retries}秒后重试...（重试次数：{retries}/{max_retries}）")
                if retries > max_retries:
                    raise Exception(f"API 连接失败: 超过重试次数")
                await asyncio.sleep(2 ** retries)  # 指数退避
                
            except APIError as e:
                retries += 1
                error_message = str(e)
                print(f"API 错误: {error_message}，等待{2 ** retries}秒后重试...（重试次数：{retries}/{max_retries}）")
                if retries > max_retries:
                    raise Exception(f"API 错误: {error_message}")
                await asyncio.sleep(2 ** retries)
                
            except asyncio.TimeoutError:
                retries += 1
                print(f"请求超时，等待{2 ** retries}秒后重试...（重试次数：{retries}/{max_retries}）")
                if retries > max_retries:
                    raise Exception(f"请求超时: 超过重试次数")
                await asyncio.sleep(2 ** retries)
                
            except Exception as e:
                retries += 1
                print(f"未知错误: {str(e)}，等待{2 ** retries}秒后重试...（重试次数：{retries}/{max_retries}）")
                if retries > max_retries:
                    raise Exception(f"未知错误: {str(e)}")
                await asyncio.sleep(2 ** retries)
    
    async def get_json_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        max_retries: int = MAX_RETRIES
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        获取JSON格式的LLM完成结果

        Args:
            prompt: 提示词
            model: 模型名称，如果为None则使用默认模型
            temperature: 温度参数
            max_tokens: 最大生成token数
            max_retries: 最大重试次数

        Returns:
            解析后的JSON数据（字典或列表）
        """
        # 获取LLM响应
        response = await self.get_completion(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries
        )

        # 提取JSON
        json_str = extract_json_from_response(response)

        # 尝试解析JSON
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 如果解析失败，尝试修复JSON
            try:
                repaired_json = repair_json(json_str)
                return json.loads(repaired_json)
            except Exception as e:
                raise ValueError(f"无法解析为有效的JSON: {str(e)}")

    async def extract_metadata(
        self,
        document_text: str,
        template_path: str,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        max_retries: int = MAX_RETRIES
    ) -> Dict[str, Any]:
        """
        提取元数据

        Args:
            document_text: 文档内容
            template_path: 提示词模板路径
            model: 模型名称，如果为None则使用默认模型
            temperature: 温度参数
            max_tokens: 最大生成token数
            max_retries: 最大重试次数

        Returns:
            提取的元数据
        """
        # 填充提示词模板
        prompt = fill_prompt_with_document(template_path, document_text)

        # 获取LLM响应
        response = await self.get_completion(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries
        )

        # 提取JSON
        json_str = extract_json_from_response(response)

        # 尝试解析JSON
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 如果解析失败，尝试修复JSON
            try:
                repaired_json = repair_json(json_str)
                return json.loads(repaired_json)
            except Exception as e:
                raise ValueError(f"无法解析为有效的JSON: {str(e)}")

async def get_metadata_from_text(
    document_text: str,
    template_path: str = "resources/extract_metadata_from_face_page.md",
    api_name: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    从文本中提取元数据
    
    Args:
        document_text: 文档内容
        template_path: 提示词模板路径
        api_name: API名称，如果为None则使用当前API
        config: 配置参数
        
    Returns:
        提取的元数据
    """
    # 初始化配置
    if config is None:
        config = {}
    
    # 初始化客户端
    client = LLMClient(api_name)
    
    # 提取元数据
    metadata = await client.extract_metadata(
        document_text=document_text,
        template_path=template_path,
        model=config.get("model"),
        temperature=config.get("temperature", 0.2),
        max_tokens=config.get("max_tokens"),
        max_retries=config.get("max_retries", MAX_RETRIES)
    )
    
    return metadata

if __name__ == "__main__":
    # 示例用法
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM元数据提取工具")
    parser.add_argument("document_path", help="文档文件路径")
    parser.add_argument("--template", "-t", default="resources/extract_metadata_from_face_page.md", help="提示词模板路径")
    parser.add_argument("--api", "-a", help="API名称")
    parser.add_argument("--model", "-m", help="模型名称")
    parser.add_argument("--temperature", type=float, default=0.2, help="温度参数")
    
    args = parser.parse_args()
    
    # 读取文档内容
    try:
        with open(args.document_path, 'r', encoding='utf-8') as f:
            document_text = f.read()
    except Exception as e:
        print(f"读取文档文件失败: {e}")
        sys.exit(1)
    
    # 提取元数据
    try:
        metadata = asyncio.run(get_metadata_from_text(
            document_text=document_text,
            template_path=args.template,
            api_name=args.api,
            config={
                "model": args.model,
                "temperature": args.temperature
            }
        ))
        
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"提取元数据失败: {e}")
        sys.exit(1) 