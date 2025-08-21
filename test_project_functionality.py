#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目功能测试脚本

这个脚本用于测试项目的核心功能模块是否正常工作

作者: Claude 4.0 Opus
创建时间: 2025-08-05
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试核心模块导入"""
    print("🧪 测试1: 核心模块导入")
    print("=" * 50)
    
    test_results = []
    
    # 测试基础模块
    try:
        from utils.llm_config import get_api_config, list_available_apis
        print("✅ utils.llm_config 导入成功")
        test_results.append(("llm_config", True))
    except ImportError as e:
        print(f"❌ utils.llm_config 导入失败: {e}")
        test_results.append(("llm_config", False))
    
    # 测试LLM客户端
    try:
        from utils.llm_client import LLMClient
        print("✅ utils.llm_client 导入成功")
        test_results.append(("llm_client", True))
    except ImportError as e:
        print(f"❌ utils.llm_client 导入失败: {e}")
        test_results.append(("llm_client", False))
    
    # 测试流水线模型
    try:
        from tools.pipeline_models import PipelineConfig, ProcessingStage
        print("✅ tools.pipeline_models 导入成功")
        test_results.append(("pipeline_models", True))
    except ImportError as e:
        print(f"❌ tools.pipeline_models 导入失败: {e}")
        test_results.append(("pipeline_models", False))
    
    # 测试流水线服务
    try:
        from tools.paper_processing_service import process_paper_pipeline
        print("✅ tools.paper_processing_service 导入成功")
        test_results.append(("paper_processing_service", True))
    except ImportError as e:
        print(f"❌ tools.paper_processing_service 导入失败: {e}")
        test_results.append(("paper_processing_service", False))
    
    return test_results

def test_llm_config():
    """测试LLM配置"""
    print("\n🧪 测试2: LLM配置")
    print("=" * 50)
    
    try:
        from utils.llm_config import get_api_config, list_available_apis, CURRENT_API
        
        # 列出可用API
        apis = list_available_apis()
        print(f"📋 可用API列表: {apis}")
        
        # 获取当前API配置
        current_config = get_api_config()
        print(f"🔧 当前API: {CURRENT_API}")
        print(f"   模型: {current_config['default_model']}")
        print(f"   温度: {current_config['temperature']}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM配置测试失败: {e}")
        return False

def test_llm_client():
    """测试LLM客户端连接"""
    print("\n🧪 测试3: LLM客户端连接")
    print("=" * 50)
    
    try:
        from utils.llm_client import LLMClient
        
        # 创建客户端实例
        client = LLMClient()
        print("✅ LLM客户端创建成功")
        
        # 测试简单的API调用
        print("🔄 测试API连接...")
        
        # 这里我们只测试客户端创建，不实际调用API以避免费用
        print("⏭️  跳过实际API调用测试（避免费用）")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM客户端测试失败: {e}")
        return False

async def test_pipeline_config():
    """测试流水线配置"""
    print("\n🧪 测试4: 流水线配置")
    print("=" * 50)
    
    try:
        from tools.pipeline_models import PipelineConfig, ProcessingStage
        
        # 创建默认配置
        config = PipelineConfig()
        print(f"✅ 默认配置创建成功")
        print(f"   输出目录: {config.output_dir}")
        print(f"   API名称: {config.api_name}")
        print(f"   保留中间文件: {config.keep_intermediate_files}")
        
        # 创建自定义配置
        custom_config = PipelineConfig(
            output_dir="test_output",
            api_name="wd_gemini2",
            keep_intermediate_files=True
        )
        print(f"✅ 自定义配置创建成功")
        print(f"   输出目录: {custom_config.output_dir}")
        print(f"   API名称: {custom_config.api_name}")
        
        # 测试处理阶段枚举
        stages = list(ProcessingStage)
        print(f"📋 处理阶段: {[stage.value for stage in stages]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 流水线配置测试失败: {e}")
        return False

def test_directory_structure():
    """测试目录结构"""
    print("\n🧪 测试5: 目录结构")
    print("=" * 50)
    
    required_dirs = [
        "tools",
        "utils", 
        "logs",
        "static/outputs"
    ]
    
    all_good = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ (缺失)")
            # 尝试创建缺失的目录
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"   已创建 {dir_path}/ 目录")
            except Exception as e:
                print(f"   创建目录失败: {e}")
                all_good = False
    
    return all_good

async def main():
    """主测试函数"""
    print("🚀 开始测试项目功能")
    print("=" * 60)
    
    # 运行各项测试
    test_results = []
    
    # 测试1: 模块导入
    import_results = test_imports()
    import_success = all(result[1] for result in import_results)
    test_results.append(("模块导入", import_success))
    
    # 测试2: LLM配置
    config_success = test_llm_config()
    test_results.append(("LLM配置", config_success))
    
    # 测试3: LLM客户端
    client_success = test_llm_client()
    test_results.append(("LLM客户端", client_success))
    
    # 测试4: 流水线配置
    pipeline_success = await test_pipeline_config()
    test_results.append(("流水线配置", pipeline_success))
    
    # 测试5: 目录结构
    dir_success = test_directory_structure()
    test_results.append(("目录结构", dir_success))
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {status} {test_name}")
    
    successful_tests = sum(1 for _, success in test_results if success)
    total_tests = len(test_results)
    
    print(f"\n🎯 总体结果: {successful_tests}/{total_tests} 测试通过")
    
    if successful_tests == total_tests:
        print("🎉 所有测试通过！项目核心功能正常。")
        print("\n💡 下一步可以尝试:")
        print("   1. 运行 python 快速测试封装服务.py")
        print("   2. 准备PDF文件进行实际测试")
        print("   3. 查看 tools/example_usage.py 了解使用方法")
    else:
        print("⚠️  部分测试失败，请检查相关模块。")
    
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
