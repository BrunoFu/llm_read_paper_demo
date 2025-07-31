#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
第五阶段：Post Process 后处理

清理中间文件，重命名输出文件，整理最终结果
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
import json
import time

class Stage5PostProcessor:
    """第五阶段后处理器"""
    
    def __init__(self):
        """初始化后处理器"""
        pass
    
    def process_paper_folder(self, paper_folder: Path) -> Dict[str, Any]:
        """
        处理单个论文文件夹的后处理
        
        Args:
            paper_folder: 论文文件夹路径
            
        Returns:
            处理结果
        """
        paper_name = paper_folder.name
        print(f"\n开始第五阶段后处理: {paper_name}")
        print("=" * 60)
        
        result = {
            "paper_name": paper_name,
            "success": True,
            "cleaned_files": [],
            "renamed_files": [],
            "errors": []
        }
        
        try:
            # 1. 删除中间文件
            self._clean_intermediate_files(paper_folder, result)
            
            # 2. 重命名输出文件
            self._rename_output_files(paper_folder, result)
            
            print(f"✓ 第五阶段后处理完成")
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            print(f"✗ 第五阶段后处理失败: {e}")
        
        return result
    
    def _clean_intermediate_files(self, paper_folder: Path, result: Dict[str, Any]):
        """清理中间文件"""
        print("步骤1: 清理中间文件...")
        
        # 要删除的文件和文件夹
        items_to_delete = [
            # 前三页文件（用于元数据提取）
            f"{paper_folder.name}_first_three_pages.md",
            f"{paper_folder.name}_first_three_pages.pdf",
            
            # 中间输出文件夹
            "json",
            "pages", 
            "sections",
            
            # 中间输出文件
            "prompts.json",
            "pipeline_result.json"
        ]
        
        for item_name in items_to_delete:
            item_path = paper_folder / item_name
            
            if item_path.exists():
                try:
                    if item_path.is_file():
                        item_path.unlink()
                        result["cleaned_files"].append(str(item_path))
                        print(f"  ✓ 删除文件: {item_name}")
                    elif item_path.is_dir():
                        shutil.rmtree(item_path)
                        result["cleaned_files"].append(str(item_path))
                        print(f"  ✓ 删除文件夹: {item_name}")
                except Exception as e:
                    error_msg = f"删除 {item_name} 失败: {e}"
                    result["errors"].append(error_msg)
                    print(f"  ✗ {error_msg}")
    
    def _rename_output_files(self, paper_folder: Path, result: Dict[str, Any]):
        """重命名输出文件"""
        print("步骤2: 重命名输出文件...")
        
        paper_name = paper_folder.name
        
        # 文件重命名映射 (旧名 -> 新名)
        rename_mappings = [
            # 元数据文件
            (f"{paper_name}_metadata.json", f"metadata_{paper_name}.json"),
            
            # 全文文件
            (f"{paper_name}_full.md", f"full_{paper_name}.md"),
            ("complete.md", f"full_{paper_name}.md"),  # 备用映射
            
            # 分类结果
            (f"{paper_name}_classification.json", f"classification_{paper_name}.json"),
            
            # 属性树
            (f"{paper_name}_attribute_tree.json", f"attribute_tree_{paper_name}.json"),
            
            # 结构化数据
            ("paper_structure.json", f"structure_{paper_name}.json"),
            
            # 最终报告
            ("report_aer_quick_test.md", f"final_report_{paper_name}.md"),
            ("final_report.md", f"final_report_{paper_name}.md"),  # 备用映射
        ]
        
        for old_name, new_name in rename_mappings:
            old_path = paper_folder / old_name
            new_path = paper_folder / new_name
            
            if old_path.exists() and not new_path.exists():
                try:
                    old_path.rename(new_path)
                    result["renamed_files"].append(f"{old_name} -> {new_name}")
                    print(f"  ✓ 重命名: {old_name} -> {new_name}")
                except Exception as e:
                    error_msg = f"重命名 {old_name} 失败: {e}"
                    result["errors"].append(error_msg)
                    print(f"  ✗ {error_msg}")
    
    def process_all_papers(self, base_dir: str = "aer_quick_test") -> List[Dict[str, Any]]:
        """
        处理所有论文文件夹的后处理
        
        Args:
            base_dir: 包含论文文件夹的基础目录
            
        Returns:
            所有处理结果
        """
        base_path = Path(base_dir)
        
        if not base_path.exists():
            raise FileNotFoundError(f"基础目录不存在: {base_dir}")
        
        # 获取所有论文文件夹
        paper_folders = []
        for item in base_path.iterdir():
            if item.is_dir() and item.name.startswith("AER"):
                paper_folders.append(item)
        
        paper_folders = sorted(paper_folders)
        
        print(f"找到 {len(paper_folders)} 个论文文件夹")
        print(f"开始第五阶段后处理...")
        
        results = []
        
        for i, paper_folder in enumerate(paper_folders, 1):
            print(f"\n{'='*80}")
            print(f"处理论文 {i}/{len(paper_folders)}: {paper_folder.name}")
            print(f"{'='*80}")
            
            result = self.process_paper_folder(paper_folder)
            results.append(result)
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """打印处理结果摘要"""
        print(f"\n{'='*80}")
        print("第五阶段后处理结果摘要")
        print(f"{'='*80}")
        
        total = len(results)
        success_count = sum(1 for r in results if r["success"])
        
        print(f"总论文数: {total}")
        print(f"成功处理: {success_count}/{total} ({success_count/total*100:.1f}%)")
        
        # 统计清理和重命名的文件数
        total_cleaned = sum(len(r["cleaned_files"]) for r in results)
        total_renamed = sum(len(r["renamed_files"]) for r in results)
        
        print(f"清理文件数: {total_cleaned}")
        print(f"重命名文件数: {total_renamed}")
        
        # 详细结果
        print(f"\n详细结果:")
        print(f"{'序号':<4} {'论文名':<50} {'状态':<10} {'清理':<8} {'重命名':<8}")
        print("-" * 80)
        
        for i, result in enumerate(results, 1):
            paper_name = result["paper_name"][:47] + "..." if len(result["paper_name"]) > 50 else result["paper_name"]
            status = "成功" if result["success"] else "失败"
            cleaned_count = len(result["cleaned_files"])
            renamed_count = len(result["renamed_files"])
            
            print(f"{i:<4} {paper_name:<50} {status:<10} {cleaned_count:<8} {renamed_count:<8}")
        
        # 显示错误信息
        errors = [error for r in results for error in r["errors"]]
        if errors:
            print(f"\n错误信息:")
            for error in errors:
                print(f"  ✗ {error}")


def main():
    """主函数"""
    print("开始第五阶段后处理...")
    print("="*80)
    
    # 创建后处理器
    processor = Stage5PostProcessor()
    
    # 处理所有论文
    results = processor.process_all_papers()
    
    # 打印摘要
    processor.print_summary(results)
    
    print(f"\n第五阶段后处理完成！")


if __name__ == "__main__":
    main()
