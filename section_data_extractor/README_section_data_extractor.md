# 模块说明: section_data_extractor

## 1. 模块概述

本模块是整个论文分析流水线的 **第二阶段（第二部分）：章节结构化解析**。

它在整个流程中扮演着至关重要的**“承上启下”**角色。其核心职责是接收由 `pdf_content_extractor` 模块生成的、非结构化的全文 Markdown 文件，并通过一系列精心设计的 LLM 调用，将其解析为一份包含完整章节层级、标题和内容的结构化 JSON 文件。这份 JSON 是第三阶段 `report_generator` 模块进行精读分析的直接输入。

## 2. 核心功能

- **论文框架提取**: 调用 LLM，使用 `extract_frame_and_tabs_figs.md` Prompt 模板，从纯文本中识别出论文的章节标题和层级关系，形成初步的结构框架。
- **内容定位与填充**: 将识别出的章节标题与原文的行号进行精确匹配，然后将每个章节下的文本内容填充到对应的结构中。
- **关键章节补全**: 通过独立的 LLM 调用，专门识别并补全论文中可能缺失或格式不规范的**摘要 (Abstract)** 和**引言 (Introduction)** 部分，极大地增强了输出结果的完整性和规范性。
- **中间产物管理**: 在处理过程中，会将每一步的结果（如初始框架、填充内容后的版本等）保存为中间的 `.json` 文件，并最终将所有结果合并，生成最终产物。

## 3. 关键文件及其职责

- `integrated_processor.py`:
  - **职责**: **本模块的核心调度器**。它编排了从加载 Markdown、调用 LLM 提取框架、填充内容，到最后补全关键章节的完整工作流程。是第二阶段结构化处理的**主入口**。

- `extract_sections.py`:
  - **职责**: 提供了 `SectionExtractor` 类，封装了具体实现章节提取和内容填充的底层逻辑，被 `integrated_processor.py` 所调用。

## 4. 依赖关系

- **上游模块依赖**:
  - `pdf_content_extractor`: 本模块的输入完全依赖于此模块生成的 `complete.md` 文件。

- **下游模块依赖**:
  - `report_generator`: 本模块的输出是此模块的直接输入。

- **配置文件依赖**:
  - **环境变量**: 脚本运行时，需要能够访问到配置好的 LLM API 密钥（如 `OPENAI_API_KEY`）。
  - `resources/prompts/extract_paper_structure/`: 本模块的 LLM 调用逻辑，强依赖于此目录下的 Prompt 模板文件。

## 5. 工作流程

1.  **输入**: 一个由 `pdf_content_extractor` 生成的 `_complete.md` 文件路径。
2.  **创建输出目录**: 以当前时间戳在 `output_path` 下创建一个唯一的文件夹，用于存放本次任务的所有产物。
3.  **提取框架**: 调用 LLM，生成包含章节标题和层级结构的 `_frame.json`。
4.  **填充内容**: 将 Markdown 文本按章节填充，生成 `_content.json`。
5.  **补全摘要/引言**: 再次调用 LLM，生成 `_abstract_introduction_section.json`。
6.  **合并与输出**: 将上述所有 JSON 文件合并，生成最终的、完整的 `_paper_structure.json` 文件。同时，会将每个章节的文本内容单独存放在 `sections/` 子目录中。

## 6. 输出产物

- **最终产物**:
  - `[timestamp]_paper_structure.json`: 描述整篇论文完整结构的 JSON 文件，是本模块最重要的输出。
- **中间产物**:
  - 位于以时间戳命名的输出文件夹内，记录了处理过程的每一步。
- **存储位置**:
  - 所有输出都位于由 `config.py` 中 `output_path` 指定的目录下，并按时间戳分子文件夹存放。 