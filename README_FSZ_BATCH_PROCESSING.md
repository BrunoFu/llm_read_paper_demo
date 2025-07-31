# 罗斯福新政相关文献批量处理系统

## 概述

这个系统将对指定文件夹中的所有PDF文献运行完整的四阶段处理流程：

1. **阶段1：元数据提取** - 提取PDF前三页并进行OCR，获取基本元数据
2. **阶段2：全文OCR** - 对整个PDF进行OCR处理，生成完整的Markdown文档  
3. **阶段3：结构化解析** - 提取论文结构、分类论文类型、生成属性树
4. **阶段4：报告生成** - 基于结构化数据生成深度分析报告

## 文件说明

- `tools/batch_process_fsz_papers.py` - 核心批量处理脚本
- `run_fsz_batch_processing.py` - 简化启动脚本
- `check_fsz_dependencies.py` - 依赖检查脚本

## 配置信息

- **输入目录**: `/Users/fro/Library/CloudStorage/OneDrive-个人/code/fszRA/policy_paper_extract/罗斯福新政影响相关文献`
- **输出目录**: `/Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/fsz_ra_papers`
- **LLM配置**: 使用默认的 `utils/llm_config.py` 配置

## 使用方法

### 方法1：直接运行启动脚本（推荐）

```bash
cd /Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test
python run_fsz_batch_processing.py
```

### 方法2：直接调用批量处理脚本

```bash
cd /Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test
python tools/batch_process_fsz_papers.py
```

### 方法3：在Python中调用

```python
import asyncio
from tools.batch_process_fsz_papers import FSZPaperBatchProcessor

async def main():
    input_dir = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/fszRA/policy_paper_extract/罗斯福新政影响相关文献"
    output_dir = "/Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/fsz_ra_papers"
    
    processor = FSZPaperBatchProcessor(input_dir, output_dir)
    await processor.process_all_papers()

asyncio.run(main())
```

## 输出结果

处理完成后，每个PDF文件会在输出目录中生成一个以论文名称命名的子文件夹，包含：

### 阶段1输出
- `{论文名}_metadata.json` - 提取的元数据
- `{论文名}_first_three_pages.md` - 前三页内容
- `{论文名}_first_three_pages.pdf` - 前三页PDF

### 阶段2输出  
- `complete.md` - 完整论文的Markdown版本
- `content_list.json` - 内容列表

### 阶段3输出
- `{论文名}_classification.json` - 论文类型分类结果
- `{论文名}_attribute_tree.json` - 论文属性树
- `paper_structure.json` - 论文结构化数据

### 阶段4输出
- `final_report.md` - 最终的深度分析报告
- `section_reports/` - 各章节的详细分析报告

### 批量处理结果
- `batch_processing_results.json` - 整个批量处理的统计结果

## 进度监控

系统会实时显示处理进度，包括：
- 当前处理的论文
- 各阶段的进度百分比
- 整体进度
- 处理统计信息

## 错误处理

- 如果某个论文处理失败，系统会继续处理下一个
- 所有错误信息会记录在日志文件中：`logs/batch_process_fsz.log`
- 最终会生成详细的处理报告，包括成功和失败的统计

## 注意事项

1. **确保输入目录存在**：请确认文献文件夹路径正确
2. **检查磁盘空间**：处理过程会生成大量中间文件，请确保有足够的磁盘空间
3. **网络连接**：某些阶段需要调用在线API，请确保网络连接正常
4. **处理时间**：根据PDF文件大小和数量，整个处理过程可能需要较长时间

## 故障排除

### 如果遇到导入错误
1. 确保在正确的目录中运行脚本
2. 检查Python环境是否正确配置
3. 确保所有必要的依赖模块都已安装

### 如果处理失败
1. 查看日志文件 `logs/batch_process_fsz.log`
2. 检查输入PDF文件是否损坏
3. 确认API配置是否正确

### 如果输出目录权限问题
```bash
chmod 755 /Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/fsz_ra_papers
```

## 技术支持

如有问题，请检查：
1. 日志文件中的详细错误信息
2. 确认所有依赖模块是否正确安装
3. 验证输入和输出路径是否正确

---

**作者**: Claude 4.0 Opus  
**创建时间**: 2025-01-29
