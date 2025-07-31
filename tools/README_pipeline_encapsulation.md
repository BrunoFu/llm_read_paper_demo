# 论文处理流水线封装服务

## 概述

这是一个完整封装的四阶段论文处理流水线，将原本分散的处理模块统一为易于使用的函数式接口。

**核心工作流程：研究 → 架构 → 计划 → 执行 → 测评**

## 架构设计

### 四阶段流水线

1. **第一阶段：元数据提取** (`crop_pdf_first_three_page`)
   - PDF裁剪前三页
   - MinerU OCR处理
   - LLM提取元数据

2. **第二阶段：全文OCR** (`pdf_content_extractor`)
   - Mistral AI全文OCR
   - 标题标准化
   - 生成完整Markdown

3. **第三阶段：结构化解析** (`section_data_extractor`)
   - 论文框架提取
   - 内容定位填充
   - 章节补全

4. **第四阶段：报告生成** (`report_generator`)
   - 深度分析
   - 智能报告生成

## 核心文件

- `pipeline_models.py` - 数据模型定义
- `paper_processing_service.py` - 核心服务类
- `test_pipeline_service.py` - 测试脚本
- `example_usage.py` - 使用示例

## 快速开始

### 基础使用

```python
import asyncio
from tools.paper_processing_service import process_paper_pipeline

async def main():
    result = await process_paper_pipeline("your_paper.pdf")
    
    if result.success:
        print(f"处理成功！报告路径: {result.final_report_path}")
    else:
        print(f"处理失败: {result.pipeline_error}")

asyncio.run(main())
```

### 自定义配置

```python
from tools.pipeline_models import PipelineConfig
from tools.paper_processing_service import process_paper_pipeline

config = PipelineConfig(
    output_dir="my_output",
    api_name="deepseek",
    llm_config={"temperature": 0.2},
    keep_intermediate_files=True
)

result = await process_paper_pipeline(
    pdf_path="paper.pdf",
    config=config
)
```

### 进度监控

```python
def progress_callback(progress_info):
    print(f"进度: {progress_info.overall_progress:.1%} - {progress_info.message}")

result = await process_paper_pipeline(
    pdf_path="paper.pdf",
    progress_callback=progress_callback
)
```

## 配置选项

### PipelineConfig 参数

- `output_dir`: 输出目录（默认: "output"）
- `api_name`: LLM API名称（如: "deepseek"）
- `template_paths`: 模板文件路径字典
- `llm_config`: LLM配置参数
- `crop_params`: PDF裁剪参数
- `keep_intermediate_files`: 是否保留中间文件
- `max_retry_attempts`: 最大重试次数

## 返回结果

### PipelineResult 属性

- `success`: 是否成功
- `overall_status`: 整体状态
- `total_processing_time`: 总处理时间
- `final_report_path`: 最终报告路径
- `metadata_path`: 元数据文件路径
- `structure_path`: 结构文件路径
- `stages`: 各阶段详细结果

## 错误处理

```python
def error_callback(stage, error):
    print(f"阶段 {stage.value} 发生错误: {error}")

result = await process_paper_pipeline(
    pdf_path="paper.pdf",
    error_callback=error_callback
)

if not result.success:
    failed_stages = result.get_failed_stages()
    print(f"失败的阶段: {[s.value for s in failed_stages]}")
```

## 测试

运行测试脚本：

```bash
python tools/test_pipeline_service.py
```

查看使用示例：

```bash
python tools/example_usage.py
```

## 封装优势

1. **函数式调用**: 完全避免命令行调用，便于调试
2. **类型安全**: 使用dataclass定义清晰的数据结构
3. **错误处理**: 每个阶段独立的异常捕获和报告
4. **进度跟踪**: 支持自定义进度回调函数
5. **配置集中**: 统一的配置管理
6. **可测试性**: 独立的测试脚本

## 依赖关系

确保以下模块可用：
- `crop_pdf_first_three_page`
- `pdf_content_extractor`
- `section_data_extractor`
- `report_generator`
- `utils.llm_client`

## 注意事项

1. 确保API密钥正确配置
2. 检查模板文件路径
3. 输出目录需要有写权限
4. 大文件处理可能需要较长时间

## 扩展性

这个封装设计支持：
- 添加新的处理阶段
- 自定义进度和错误回调
- 不同的LLM API提供商
- 批量处理功能

---

**你作为 Claude 4.0 Opus** 的专业建议：这种封装完全满足您的需求，提供了清晰的函数式接口，便于调试和测试，同时保持了良好的可扩展性。
