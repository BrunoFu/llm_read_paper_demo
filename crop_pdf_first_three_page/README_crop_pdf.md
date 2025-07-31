# 模块说明: crop_pdf_first_three_page

## 1. 模块概述

本模块是整个论文分析流水线的 **第一阶段：元数据提取**。

其核心职责是接收一篇完整的、原始的PDF格式的学术论文，并最终从中提取出结构化的元数据（如标题、作者、摘要、期刊等）。此阶段为后续的全文分析和报告生成提供了必要的基础信息。

## 2. 核心功能

- **PDF 页面裁剪**: 从输入的完整 PDF 中精确裁剪出前三页，以缩小初步分析的范围，节约后续 OCR 和 LLM 的处理成本。
- **调用外部 OCR 服务**: 与 **MinerU API** (`https://mineru.net`) 进行深度交互，完成文档的上传、OCR任务提交、状态轮询和结果下载。
- **版面分析与内容重组**: 解析 MinerU OCR 返回的、包含详细布局信息的核心产物 (`layout.json`)，能够区分页眉、页脚、脚注和正文，并将其智能地重组成一个可读的 Markdown 文件。
- **调用 LLM 提取元数据**: 将重组后的 Markdown 文本，结合 Prompt 模板，提交给大语言模型（LLM），以提取结构化的元数据。

## 3. 关键文件及其职责

- `ocr_processor_mineru.py`
  - **职责**: **本模块的核心调度器**。它编排了从裁剪、调用 MinerU API、解析结果到最后调用元数据提取的完整工作流程。当需要处理第一阶段任务时，应主要运行此脚本。

- `crop_pdf_first_page.py`
  - **职责**: 提供底层的 `crop_first_pages` 函数，负责执行具体的 PDF 页面裁剪操作。

- `ocr_processor.py`
  - **职责**: 这是一个**备用的、使用 Mistral AI OCR** 的处理器。在当前主流工作流中不直接使用，但可作为替代或对比方案。

## 4. 依赖关系

- **内部模块依赖**:
  - `meta_data_extractor.metadata_extractor`: 本模块在完成 OCR 和内容重组后，会调用此外部模块中的 `extract_metadata` 函数来执行最终的元数据提取。

- **配置文件依赖**:
  - **MinerU API Token**: 当前硬编码在 `ocr_processor_mineru.py` 中。按照 `ToDo.md` 的规划，未来应迁移至 `.env` 或 `config.py` 中进行管理。

- **资源文件依赖**:
  - **LLM Prompt 模板**: 在调用 `meta_data_extractor` 时，需要一个 Prompt 模板文件来指导 LLM 进行元数据提取。默认路径为 `resources/extract_metadata_from_face_page.md`。

## 5. 工作流程

1.  **输入**: 一份本地的 `.pdf` 文件路径。
2.  调用 `crop_first_pages` 函数，生成一份仅包含前三页的临时 PDF (`*_first_three_pages.pdf`)。
3.  调用 `process_pdf` (在 `ocr_processor_mineru.py` 中)，启动与 MinerU API 的交互。
    - a. 申请上传链接。
    - b. 上传裁剪后的临时 PDF。
    - c. 轮询任务状态，直到 OCR 处理完成。
    - d. 下载包含结果的 `.zip` 压缩包。
4.  解压 `.zip` 包，找到核心产物 `layout.json`。
5.  深度解析 `layout.json`，区分正文、页眉、脚注等，并重组成一个临时的 Markdown 文件 (`*_first_three_pages.md`)。
6.  调用 `meta_data_extractor.extract_metadata` 函数，将此 Markdown 文件提交给 LLM。
7.  LLM 返回结构化的元数据。
8.  脚本将元数据保存为最终产物，并清理所有临时的中间文件（如裁剪的PDF、zip包、解压目录等）。

## 6. 输出产物

- **主要产物**: 一个 `_metadata.json` 文件。
- **命名与位置**: 产物被存储在由 `--output` 参数指定的目录中，文件名与输入的 PDF 文件名相关。例如：`results/<pdf_file_name>/<pdf_file_name>_metadata.json`。
- **产物内容**: 包含从论文前三页提取出的、结构化的元数据信息。 