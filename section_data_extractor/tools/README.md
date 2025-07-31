# PDF结构提取工具

这个工具集用于从PDF提取的Markdown文本中解析论文结构，并提取各个部分的内容。

## 功能

- 从Markdown文本中提取论文标题和章节结构
- 为每个标题添加行号信息
- 展平论文结构
- 为每个部分添加文本内容
- 检查并提取Abstract和Introduction
- 将缺失的Abstract和Introduction插入到结构中
- 生成各个章节的独立文件

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 完整处理流程

使用`process_paper_structure.py`脚本可以一次性完成所有处理步骤：

```bash
python process_paper_structure.py input.json paper_content.md --output-dir ./output
python process_paper_structure.py input.json /Users/fro/Library/CloudStorage/OneDrive-个人/code/OCR_api_test/ocr_results_Hvidkjaer-2008-Small_Trades_and_the_Cross-Section_of_Stock_Return/complete.md  --output-dir ./output
```

参数说明：
- `input.json`: 包含论文结构的JSON文件（如果不存在，会自动从Markdown中提取）
- `paper_content.md`: 论文的Markdown内容文件
- `--output-dir`: 输出目录（可选，默认为./output）

### 单独运行各步骤

也可以单独运行各个步骤：

1. 提取论文结构：
```bash
python extract_paper_structure.py --markdown paper_content.md --output input.json
```

2. 提取标题行号：
```bash
python extract_title_lines.py --input input.json --markdown paper_content.md --output input_with_row_num.json
```

3. 验证标题行号：
```bash
python verify_title_lines.py --input input_with_row_num.json --markdown paper_content.md
```

4. 展平结构：
```bash
python flatten_structure.py --input input_with_row_num.json --output flattened_structure.json
```

5. 添加文本内容：
```bash
python add_text_content.py --input flattened_structure.json --markdown paper_content.md --output structure_with_content.json
```

6. 检查并提取Abstract和Introduction：
```bash
python check_abstract_intro.py
```

7. 插入缺失的Abstract和Introduction：
```bash
python insert_abstract_intro.py
```

8. 提取各节内容：
```bash
python extract_section_content.py --input structure_with_content_updated.json --output-dir ./output
```

## 输出文件

处理完成后，将在输出目录中生成以下文件：

- `input.json`: 初始的论文结构JSON
- `input_with_row_num.json`: 添加了行号的结构
- `flattened_structure.json`: 展平后的结构
- `structure_with_content.json`: 添加了文本内容的结构
- `abstract_intro.json`: Abstract和Introduction的提取结果
- `structure_with_content_updated.json`: 插入了缺失的Abstract和Introduction后的结构
- `sections/`: 包含各个章节内容的目录

## 工作流程

1. 从Markdown文本中提取论文结构（如果input.json不存在）
2. 提取标题行号
3. 验证标题行号
4. 展平结构
5. 添加文本内容
6. 检查并提取Abstract和Introduction
7. 插入缺失的Abstract和Introduction
8. 提取各节内容

## 注意事项

- 确保Markdown文件使用UTF-8编码
- 对于大型论文，处理可能需要一些时间，特别是在使用大模型提取结构时
- 如果遇到问题，可以尝试单独运行各个步骤，以便更好地定位问题 