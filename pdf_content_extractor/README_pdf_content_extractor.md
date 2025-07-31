# 模块说明: pdf_content_extractor

## 1. 模块概述

本模块是整个论文分析流水线的 **第二阶段（第一部分）：全文内容提取**。

它的核心且唯一的职责是，接收一篇完整的、原始的PDF文档，并利用 **Mistral AI OCR 服务** 将其完全转化为一份干净的、包含所有页面内容的 Markdown 文件。此模块的输出是下游 `section_data_extractor` 模块的直接输入。

## 2. 核心功能

- **全文 OCR**: 通过 `mistralai` Python 库与 Mistral AI API (`mistral-ocr-latest` 模型) 交互，对输入 PDF 的**每一页**执行光学字符识别。
- **图片提取与链接**: 能够解码从 API 返回的 Base64 编码的图片，将其保存为独立的 `.png` 文件，并在最终的 Markdown 文本中生成正确的相对路径引用。
- **标题标准化**: 执行一个至关重要的后处理步骤——`normalize_heading_levels` 函数。它会通过正则表达式，将所有不同级别（如 `##`, `###`, `####`）的 Markdown 标题，全部统一为**一级标题 (`# `)**。这个操作极大地降低了后续 `section_data_extractor` 模块中 LLM 识别文章结构的复杂性。

## 3. 关键文件及其职责

- `pdf_ocr.py`:
  - **职责**: **模块的唯一入口和核心实现**。它封装了从接收 PDF 路径、调用 Mistral AI API、后处理文本到保存最终产物的全部逻辑。

## 4. 依赖关系

- **外部服务依赖**:
  - **Mistral AI API**: 本模块的功能完全依赖于对 Mistral AI OCR 服务的成功调用。

- **配置文件依赖**:
  - **环境变量**: 脚本运行时，必须能够从环境变量 `MISTRAL_API_KEY` 中读取到有效的 Mistral AI API 密钥。

## 5. 工作流程

1.  **输入**: 一个本地的 `.pdf` 文件路径。
2.  `process_pdf` 函数被调用。
3.  脚本将本地 PDF 文件上传至 Mistral AI 的文件服务，并获取一个用于处理的签名 URL。
4.  调用 OCR API，提交处理任务。
5.  API 以分页形式返回结果，每一页都包含 Markdown 文本和内嵌的图片数据。
6.  脚本遍历每一页的结果：
    - a. 保存图片到本地的 `images/` 子目录。
    - b. 调用 `normalize_heading_levels` 函数，将当前页 Markdown 中的所有标题统一为一级。
    - c. 更新 Markdown 文本，将图片引用指向本地保存的路径。
    - d. 将处理后的单页 Markdown 保存到 `pages/` 子目录。
7.  所有页面处理完毕后，将每一页的 Markdown 内容拼接起来，形成一份完整的文档。
8.  将这份完整文档保存为最终产物。

## 6. 输入与输出

- **输入**:
  - `pdf_path`: 字符串，指向要处理的 PDF 文件的本地路径。
  - `output_dir` (可选): 字符串，指定输出结果的目录。

- **输出**:
  - **一个以输入 PDF 文件名命名的文件夹** (例如，若未指定 `output_dir`，则为 `ocr_results_[pdf_file_name]`)。
  - **此文件夹内的产物结构**:
    - `complete.md`: **核心产物**。一份包含所有页面内容的、经过标题标准化处理的完整 Markdown 文件。
    - `images/`: 一个包含从 PDF 中提取出的所有图片的子目录。
    - `pages/`: 一个包含每一页独立的、处理后的 Markdown 文件的子目录。 