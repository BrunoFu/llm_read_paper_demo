#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
属性树提取器

从论文全文中提取核心属性，如研究动机、研究问题、方法论、数据集和关键结论
"""

import os
import sys
import json
import asyncio
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union

# 修复import路径
try:
    from .prompt_utils import fill_prompt_with_document, extract_and_repair_json
    from ..utils.llm_client import LLMClient
except ImportError:
    # 尝试从相对路径导入
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from attribute_tree_extractor.prompt_utils import fill_prompt_with_document, extract_and_repair_json
        from utils.llm_client import LLMClient
    except ImportError:
        print("无法导入必要的模块，请确保相关文件存在")
        sys.exit(1)

# 默认模板路径
DEFAULT_EMPIRICAL_TEMPLATE = "resources/extract_attribute_tree_empirical.md"
DEFAULT_STRUCTURAL_TEMPLATE = "resources/extract_attribute_tree_structural.md"

class AttributeTreeExtractor:
    """属性树提取器类"""
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None, api_name: Optional[str] = None):
        """
        初始化属性树提取器
        
        Args:
            llm_config: LLM配置
            api_name: API名称
        """
        self.llm_config = llm_config
        self.api_name = api_name
        self.client = LLMClient(api_name=api_name)
    
    async def extract_attribute_tree_from_paper(
        self, 
        paper_content_path: str, 
        template_path: str, 
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从论文全文中提取属性树
        
        Args:
            paper_content_path: 论文全文文件路径
            template_path: prompt模板文件路径
            output_path: 输出文件路径，如果为None则不保存结果
            
        Returns:
            提取的属性树
        """
        # 读取论文全文
        try:
            with open(paper_content_path, 'r', encoding='utf-8') as f:
                document_text = f.read()
        except Exception as e:
            raise ValueError(f"读取论文全文失败: {e}")
        
        # 使用LLM提取属性树
        print(f"正在使用LLM提取论文属性树...")
        if self.api_name:
            print(f"使用API: {self.api_name}")
        
        # 填充提示词
        prompt = fill_prompt_with_document(template_path, document_text)
        
        try:
            # 调用LLM API
            response = await self.client.get_completion(prompt)
            
            # 解析并修复JSON响应
            attribute_tree = extract_and_repair_json(response)
        except Exception as e:
            raise Exception(f"提取属性树时出错: {e}")
        
        # 如果指定了输出路径，保存结果
        if output_path:
            try:
                # 确保输出目录存在
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                
                # 保存JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(attribute_tree, f, indent=2, ensure_ascii=False)
                print(f"属性树已保存到: {output_path}")
            except Exception as e:
                print(f"保存属性树失败: {e}")
        
        return attribute_tree
    
    async def extract_attribute_tree(
        self,
        paper_name: str,
        output_dir: str,
        paper_type: str = None,
        empirical_template_path: str = DEFAULT_EMPIRICAL_TEMPLATE,
        structural_template_path: str = DEFAULT_STRUCTURAL_TEMPLATE
    ) -> Dict[str, Any]:
        """
        提取论文属性树的主函数
        
        Args:
            paper_name: 论文文件名（不含路径和后缀）
            output_dir: 输出目录
            paper_type: 论文类型，"empirical"或"structural"，如果为None则尝试从分类结果中获取
            empirical_template_path: 经验研究型论文的prompt模板路径
            structural_template_path: 结构模型型论文的prompt模板路径
            
        Returns:
            提取的属性树
        """
        # 构建文件路径 - 优先查找complete.md，然后查找{paper_name}_full.md
        paper_content_path = os.path.join(output_dir, "complete.md")
        if not os.path.exists(paper_content_path):
            paper_content_path = os.path.join(output_dir, f"{paper_name}_full.md")

        attribute_tree_path = os.path.join(output_dir, f"{paper_name}_attribute_tree.json")
        classification_path = os.path.join(output_dir, f"{paper_name}_classification.json")

        # 检查文件是否存在
        if not os.path.exists(paper_content_path):
            raise FileNotFoundError(f"未找到论文全文文件: {paper_content_path}")
        
        # 如果未指定论文类型，尝试从分类结果中获取
        if paper_type is None:
            if os.path.exists(classification_path):
                try:
                    with open(classification_path, 'r', encoding='utf-8') as f:
                        classification_result = json.load(f)
                    
                    # 导入论文类型判断函数
                    try:
                        from .paper_type_classifier import PaperTypeClassifier
                        paper_type = PaperTypeClassifier.determine_paper_type(classification_result)
                        print(f"从分类结果中获取论文类型: {paper_type}")
                    except ImportError:
                        # 简单判断论文类型
                        research_nature = classification_result.get("research_nature_assessment", "")
                        if "Theoretical" in research_nature or "with Theoretical Model" in research_nature:
                            paper_type = "structural"
                        else:
                            paper_type = "empirical"
                        print(f"简单判断论文类型: {paper_type}")
                except Exception as e:
                    print(f"无法从分类结果中获取论文类型: {e}")
                    paper_type = "empirical"  # 默认为经验研究型
                    print(f"使用默认论文类型: {paper_type}")
            else:
                paper_type = "empirical"  # 默认为经验研究型
                print(f"未找到分类结果，使用默认论文类型: {paper_type}")
        
        # 根据论文类型选择模板
        if paper_type.lower() == "structural":
            template_path = structural_template_path
            print(f"使用结构模型型论文模板: {template_path}")
        else:
            template_path = empirical_template_path
            print(f"使用经验研究型论文模板: {template_path}")
        
        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"未找到模板文件: {template_path}")
        
        # 提取属性树
        return await self.extract_attribute_tree_from_paper(
            paper_content_path=paper_content_path,
            template_path=template_path,
            output_path=attribute_tree_path
        )


# 保持向后兼容的函数接口
async def extract_attribute_tree_from_paper(
    paper_content_path: str, 
    template_path: str, 
    output_path: Optional[str] = None, 
    api_name: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """向后兼容的函数接口"""
    extractor = AttributeTreeExtractor(llm_config=llm_config, api_name=api_name)
    return await extractor.extract_attribute_tree_from_paper(paper_content_path, template_path, output_path)

def extract_attribute_tree(
    paper_name: str, 
    output_dir: str, 
    paper_type: str = None,
    empirical_template_path: str = DEFAULT_EMPIRICAL_TEMPLATE,
    structural_template_path: str = DEFAULT_STRUCTURAL_TEMPLATE,
    api_name: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """向后兼容的函数接口"""
    extractor = AttributeTreeExtractor(llm_config=llm_config, api_name=api_name)
    return extractor.extract_attribute_tree(
        paper_name, output_dir, paper_type, 
        empirical_template_path, structural_template_path
    )


if __name__ == "__main__":
    # 测试代码
    import argparse
    
    parser = argparse.ArgumentParser(description="从论文全文中提取属性树")
    parser.add_argument("paper_name", help="论文文件名（不含路径和后缀）")
    parser.add_argument("--output-dir", "-d", default=None, help="输出目录")
    parser.add_argument("--paper-type", "-p", choices=["empirical", "structural"], help="论文类型")
    parser.add_argument("--empirical-template", default=DEFAULT_EMPIRICAL_TEMPLATE, help="经验研究型论文的prompt模板路径")
    parser.add_argument("--structural-template", default=DEFAULT_STRUCTURAL_TEMPLATE, help="结构模型型论文的prompt模板路径")
    parser.add_argument("--api", "-a", default=None, help="API名称")
    
    args = parser.parse_args()
    
    # 确定输出目录
    output_dir = args.output_dir or f"outputs/{args.paper_name}"
    
    try:
        attribute_tree = extract_attribute_tree(
            paper_name=args.paper_name, 
            output_dir=output_dir,
            paper_type=args.paper_type,
            empirical_template_path=args.empirical_template,
            structural_template_path=args.structural_template,
            api_name=args.api
        )
        print(json.dumps(attribute_tree, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
