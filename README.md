# 🤖 LLM Read Paper - 智能学术论文处理系统

一个基于大语言模型的智能学术论文处理系统，能够自动将PDF学术论文转换为结构化分析报告。

## ✨ 核心特性

- 🔍 **智能OCR处理**：支持MinerU和Mistral AI双OCR引擎
- 📊 **四阶段流水线**：元数据提取 → 全文OCR → 结构化解析 → 报告生成
- 🤖 **LLM深度分析**：基于大语言模型的智能内容分析
- 🌐 **Web用户界面**：基于Gradio的友好交互界面
- ⚡ **异步处理**：高效的并发处理能力
- 🔄 **断点续传**：支持中断后继续处理
- 📈 **实时监控**：完整的进度监控和错误处理

## 🏗️ 系统架构

### 四阶段处理流水线

```
PDF输入 → 阶段1：元数据提取 → 阶段2：全文OCR → 阶段3：结构化解析 → 阶段4：报告生成 → 最终输出
```

1. **阶段1：元数据提取** (`crop_pdf_first_three_page/`)
   - PDF前三页裁剪和OCR
   - 基于LLM的元数据提取
   - 论文基本信息识别

2. **阶段2：全文OCR** (`pdf_content_extractor/`)
   - 完整PDF文档OCR处理
   - 图片提取和标题标准化
   - Markdown格式输出

3. **阶段3：结构化解析** (`section_data_extractor/`)
   - 论文框架识别和内容定位
   - 章节结构化处理
   - 论文类型分类

4. **阶段4：报告生成** (`report_generator/`)
   - 基于LLM的深度分析
   - 智能报告生成
   - 多格式输出支持

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 支持的操作系统：macOS, Linux, Windows

### 安装依赖

```bash
git clone https://github.com/Rostopher/llm_read_paper.git
cd llm_read_paper
pip install -r requirements.txt
```

### 配置API密钥

在 `utils/llm_config.py` 中配置您的API密钥：

```python
LLM_CONFIG = {
    "openai": {
        "api_key": "your-openai-key"
    },
    "mistral": {
        "api_key": "your-mistral-key"
    }
}
```

### 🎯 推荐使用方式：封装的流水线服务

```python
import asyncio
from tools.paper_processing_service import process_paper_pipeline

async def main():
    result = await process_paper_pipeline("your_paper.pdf")
    
    if result.success:
        print(f"✅ 处理成功！报告路径: {result.final_report_path}")
    else:
        print(f"❌ 处理失败: {result.pipeline_error}")

asyncio.run(main())
```

### Web界面使用

```bash
cd frontend
python app.py
# 访问 http://localhost:7860
```

## 📁 项目结构

```
llm_read_paper/
├── tools/                          # 🎯 核心封装服务
│   ├── paper_processing_service.py # 完整四阶段流水线封装
│   ├── pipeline_models.py          # 数据模型定义
│   └── example_usage.py            # 使用示例
├── crop_pdf_first_three_page/       # 阶段1：元数据提取
├── pdf_content_extractor/           # 阶段2：全文OCR
├── section_data_extractor/          # 阶段3：结构化解析
├── report_generator/                # 阶段4：报告生成
├── frontend/                        # Web用户界面
├── utils/                           # 工具函数
├── resources/                       # Prompt模板
└── example_pdfs/                    # 示例PDF文件
```

## 📖 详细文档

- [新工程师快速入门指南](新工程师快速入门指南.md)
- [项目功能分析报告](项目功能分析报告.md)
- [项目总结报告](项目总结报告.md)

## 🔧 高级用法

### 自定义配置

```python
from tools.paper_processing_service import process_paper_pipeline
from tools.pipeline_models import PipelineConfig

config = PipelineConfig(
    output_dir="custom_output",
    api_name="openai",
    llm_config={"temperature": 0.1},
    keep_intermediate_files=True
)

result = await process_paper_pipeline("paper.pdf", config=config)
```

### 批量处理

```python
import asyncio
from pathlib import Path

async def batch_process():
    pdf_files = list(Path("papers/").glob("*.pdf"))
    
    for pdf_file in pdf_files:
        result = await process_paper_pipeline(str(pdf_file))
        print(f"处理 {pdf_file.name}: {'成功' if result.success else '失败'}")

asyncio.run(batch_process())
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [MinerU](https://github.com/opendatalab/MinerU) - 高质量PDF OCR服务
- [Mistral AI](https://mistral.ai/) - 强大的LLM API服务
- [Gradio](https://gradio.app/) - 简单易用的Web界面框架

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/Rostopher/llm_read_paper/issues)
- 发起 [Discussion](https://github.com/Rostopher/llm_read_paper/discussions)

---

**由 Claude 4.0 Opus 协助开发** 🤖
