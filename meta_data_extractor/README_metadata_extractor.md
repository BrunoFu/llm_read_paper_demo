# 模块说明: meta_data_extractor

## 1. 模块概述

本模块是一个专门的 **LLM 调用与元数据提取器**。

它在整个流水线中扮演一个**核心服务提供者**的角色，被第一阶段的 `crop_pdf_first_three_page` 模块所调用。其核心职责是接收由 OCR 生成的论文前几页的纯文本内容，并通过大语言模型（LLM）将其转化为结构化的元数据 JSON。

## 2. 核心功能

- **Prompt 动态构建**: 读取指定的 Prompt 模板文件，并将输入的论文文本动态填充进去，构建一个完整的、用于指导 LLM 的请求。
- **调用通用 LLM 客户端**: 与底层的 `utils.llm_client` 模块交互，能够根据配置调用不同的 LLM API 服务（如 OpenAI, Mistral 等）。
- **JSON 响应修复**: 在接收到 LLM 返回的 JSON 字符串后，会使用 `json-repair` 库进行一次健壮性修复，以处理 LLM 可能返回的、格式不完全规范的 JSON，显著提高了流程的稳定性。
- **结构化数据输出**: 将最终清洗和修复后的元数据保存为格式化的 `.json` 文件。

## 3. 关键文件及其职责

- `metadata_extractor.py`:
  - **职责**: **模块主入口**。提供了 `extract_metadata_from_pdf_first_pages` 和 `extract_metadata` 两个核心函数，封装了从读取文件、调用 LLM 到保存结果的完整逻辑。
- `llm_config.py`:
  - **职责**: (当前) 用于定义和管理不同 LLM 服务提供商的配置信息，如 API 地址、模型名称等。根据 `ToDo.md` 的规划，此功能未来将被整合到项目级的统一配置中。

## 4. 依赖关系

- **内部模块依赖**:
  - `utils.llm_client`: 实际执行与 LLM API 通信的底层客户端。
  - `utils.prompt_utils`: 提供填充 Prompt 模板的工具函数。
- **资源文件依赖**:
  - **LLM Prompt 模板**: 模块的执行**强依赖**一个 Prompt 模板文件，该文件定义了如何指示 LLM 从文本中提取所需的元数据字段。调用方（如 `crop_pdf_first_three_page` 模块）必须提供此模板的路径，通常是 `resources/extract_metadata_from_face_page.md`。

## 5. 工作流程

1.  **输入**: 由上游模块提供一个包含论文前几页 OCR 内容的 `.md` 文件路径，以及一个 Prompt 模板路径。
2.  `extract_metadata_from_pdf_first_pages` 函数被调用。
3.  函数读取 `.md` 文件和模板文件的内容。
4.  调用 `utils.prompt_utils.fill_prompt_with_document`，将论文文本填充到 Prompt 模板中。
5.  调用 `utils.llm_client.get_metadata_from_text`，将构建好的 Prompt 发送给配置好的 LLM API。
6.  接收 LLM 返回的 JSON 字符串。
7.  使用 `json_repair.repair_json` 对返回的字符串进行清洗和修复。
8.  将修复后的字符串解析为 Python 字典。
9.  将该字典保存为格式化的 `.json` 文件。
10. 返回提取出的元数据字典给上游调用者。

## 6. 输入与输出

- **输入**:
  - `first_pages_path`: 包含论文前几页 OCR 文本的 `.md` 文件路径。
  - `template_path`: 指导 LLM 提取元数据的 Prompt 模板文件路径。
- **输出**:
  - **主要产物**: 一个包含结构化元数据的 `.json` 文件。
  - **存储与返回**: 模块会将 JSON 文件保存到指定的 `output_path`，同时也会将提取出的元数据字典作为函数返回值，供调用方直接使用。 