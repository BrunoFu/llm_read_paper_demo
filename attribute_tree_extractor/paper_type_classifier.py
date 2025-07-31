#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
论文类型分类器

分析论文全文内容，将论文分类为经验研究型(Empirical)或结构模型型(Structural)
"""

import os
import sys
import json
import asyncio
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

class PaperTypeClassifier:
    """论文类型分类器类"""
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None, api_name: Optional[str] = None):
        """
        初始化分类器
        
        Args:
            llm_config: LLM配置
            api_name: API名称
        """
        self.llm_config = llm_config
        self.api_name = api_name
        self.client = LLMClient(api_name=api_name)
    
    async def classify_paper_type(
        self, 
        paper_content_path: str, 
        template_path: str, 
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析论文全文内容，将论文分类为经验研究型(Empirical)或结构模型型(Structural)
        
        Args:
            paper_content_path: 论文全文文件路径
            template_path: prompt模板文件路径
            output_path: 输出文件路径，如果为None则不保存结果
            
        Returns:
            论文分类结果
        """
        # 读取论文全文
        try:
            with open(paper_content_path, 'r', encoding='utf-8') as f:
                document_text = f.read()
        except Exception as e:
            raise ValueError(f"读取论文全文失败: {e}")
        
        # 使用LLM进行论文分类
        print(f"正在使用LLM进行论文类型分类...")
        if self.api_name:
            print(f"使用API: {self.api_name}")
        
        # 填充提示词
        prompt = fill_prompt_with_document(template_path, document_text)
        
        try:
            # 调用LLM API
            response = await self.client.get_completion(prompt)
            
            # 解析并修复JSON响应
            classification_result = extract_and_repair_json(response)
        except Exception as e:
            raise Exception(f"论文分类时出错: {e}")
        
        # 如果指定了输出路径，保存结果
        if output_path:
            try:
                # 确保输出目录存在
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                
                # 保存JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(classification_result, f, indent=2, ensure_ascii=False)
                print(f"论文分类结果已保存到: {output_path}")
            except Exception as e:
                print(f"保存论文分类结果失败: {e}")
        
        return classification_result
    
    async def classify_paper(
        self,
        paper_name: str,
        output_dir: str,
        template_path: str
    ) -> Dict[str, Any]:
        """
        论文分类的主函数
        
        Args:
            paper_name: 论文文件名（不含路径和后缀）
            output_dir: 输出目录
            template_path: prompt模板文件路径
            
        Returns:
            论文分类结果
        """
        # 构建文件路径 - 优先查找complete.md，然后查找{paper_name}_full.md
        paper_content_path = os.path.join(output_dir, "complete.md")
        if not os.path.exists(paper_content_path):
            paper_content_path = os.path.join(output_dir, f"{paper_name}_full.md")

        classification_path = os.path.join(output_dir, f"{paper_name}_classification.json")

        # 检查文件是否存在
        if not os.path.exists(paper_content_path):
            raise FileNotFoundError(f"未找到论文全文文件: {paper_content_path}")
        
        # 进行论文分类
        return await self.classify_paper_type(
            paper_content_path=paper_content_path,
            template_path=template_path,
            output_path=classification_path
        )
    
    @staticmethod
    def determine_paper_type(classification_result: Dict[str, Any]) -> str:
        """
        根据分类结果确定论文类型（Empirical或Structural）
        
        Args:
            classification_result: 论文分类结果
            
        Returns:
            论文类型: "empirical" 或 "structural"
        """
        # 获取研究性质评估
        research_nature = classification_result.get("research_nature_assessment", "")
        
        # 获取研究方法维度
        research_methods = classification_result.get("research_method_dimension", [])
        
        # 判断是否为结构模型型论文
        is_structural = False
        
        # 如果研究性质包含"Theoretical"或"with Theoretical Model"，倾向于结构模型
        if "Theoretical Research" in research_nature or "with Theoretical Model" in research_nature:
            is_structural = True
        
        # 如果研究方法包含"Structural Estimation"或"Quantitative Theory & Calibration"，倾向于结构模型
        if "Structural Estimation" in research_methods or "Quantitative Theory & Calibration" in research_methods:
            is_structural = True
        
        # 返回论文类型
        return "structural" if is_structural else "empirical"


# 保持向后兼容的函数接口
async def classify_paper_type(
    paper_content_path: str, 
    template_path: str, 
    output_path: Optional[str] = None, 
    api_name: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """向后兼容的函数接口"""
    classifier = PaperTypeClassifier(llm_config=llm_config, api_name=api_name)
    return await classifier.classify_paper_type(paper_content_path, template_path, output_path)

def classify_paper(
    paper_name: str, 
    output_dir: str, 
    template_path: str, 
    api_name: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """向后兼容的函数接口"""
    classifier = PaperTypeClassifier(llm_config=llm_config, api_name=api_name)
    return classifier.classify_paper(paper_name, output_dir, template_path)

def determine_paper_type(classification_result: Dict[str, Any]) -> str:
    """向后兼容的函数接口"""
    return PaperTypeClassifier.determine_paper_type(classification_result)


if __name__ == "__main__":
    # 测试代码
    import argparse
    
    parser = argparse.ArgumentParser(description="对论文进行类型分类")
    parser.add_argument("paper_name", help="论文文件名（不含路径和后缀）")
    parser.add_argument("--output-dir", "-d", default=None, help="输出目录")
    parser.add_argument("--template", "-t", default="resources/paper_type_classify.md", help="prompt模板文件路径")
    parser.add_argument("--api", "-a", default=None, help="API名称")
    
    args = parser.parse_args()
    
    # 确定输出目录
    output_dir = args.output_dir or f"outputs/{args.paper_name}"
    
    try:
        classification_result = classify_paper(
            paper_name=args.paper_name, 
            output_dir=output_dir, 
            template_path=args.template,
            api_name=args.api
        )
        
        # 确定论文类型
        paper_type = determine_paper_type(classification_result)
        
        print(f"\n论文分类结果:")
        print(json.dumps(classification_result, indent=2, ensure_ascii=False))
        print(f"\n论文类型: {paper_type}")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
