# 论文OCR解析系统 - 前端演示

这是一个基于Gradio的前端演示应用，用于展示论文OCR解析系统的功能。

## 功能特点

- 上传PDF论文并进行OCR解析
- 将PDF转换为高质量Markdown格式
- 识别论文的章节结构和层级关系
- 提取论文中的图表、公式等特殊元素
- 生成中文解读报告

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
cd frontend
python app.py
```

应用将在本地启动，通常可以通过浏览器访问 http://127.0.0.1:7860 来使用。

## 使用方法

1. 上传PDF论文文件
2. 点击"开始处理"按钮
3. 等待处理完成后查看生成的中文解读报告

## 注意事项

- 处理大型PDF文件可能需要较长时间，请耐心等待
- 系统会自动保存处理结果到 `static/outputs/` 目录

## 目录结构

```
frontend/
├── app.py          # 主应用文件
├── requirements.txt # 依赖项列表
├── README.md       # 说明文档
└── static/         # 静态资源目录
    ├── images/     # 图片资源
    └── outputs/    # 输出结果目录
``` 