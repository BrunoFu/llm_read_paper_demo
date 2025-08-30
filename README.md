# 🤖 LLM Read Paper - Intelligent Academic Paper Processing System

An intelligent academic paper processing system based on large language models, capable of automatically converting PDF academic papers into structured analysis reports.

## ✨ Core Features

- 🔍 **Intelligent OCR Processing**: Supports dual OCR engines with MinerU and Mistral AI
- 📊 **Four-Stage Pipeline**: Metadata extraction → Full-text OCR → Structured parsing → Report generation
- 🤖 **LLM Deep Analysis**: Intelligent content analysis based on large language models
- 🌐 **Web User Interface**: Friendly interactive interface based on Gradio
- ⚡ **Asynchronous Processing**: Efficient concurrent processing capabilities
- 🔄 **Resume Processing**: Supports continuing processing after interruption
- 📈 **Real-time Monitoring**: Complete progress monitoring and error handling

## 🏗️ System Architecture

### Four-Stage Processing Pipeline

```
PDF Input → Stage 1: Metadata Extraction → Stage 2: Full-text OCR → Stage 3: Structured Parsing → Stage 4: Report Generation → Final Output
```

1. **Stage 1: Metadata Extraction** (`crop_pdf_first_three_page/`)
   - PDF first three pages cropping and OCR
   - LLM-based metadata extraction
   - Paper basic information identification

2. **Stage 2: Full-text OCR** (`pdf_content_extractor/`)
   - Complete PDF document OCR processing
   - Image extraction and title standardization
   - Markdown format output

3. **Stage 3: Structured Parsing** (`section_data_extractor/`)
   - Paper framework recognition and content positioning
   - Chapter structured processing
   - Paper type classification

4. **Stage 4: Report Generation** (`report_generator/`)
   - LLM-based deep analysis
   - Intelligent report generation
   - Multi-format output support

## 🚀 Quick Start

### Requirements

- Python 3.8+
- Supported operating systems: macOS, Linux, Windows

### Install Dependencies

```bash
git clone https://github.com/Rostopher/llm_read_paper.git
cd llm_read_paper
pip install -r requirements.txt
```

### Configure API Keys

Configure your API keys in `utils/llm_config.py`:

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

### 🎯 Recommended Usage: Encapsulated Pipeline Service

```python
import asyncio
from tools.paper_processing_service import process_paper_pipeline

async def main():
    result = await process_paper_pipeline("your_paper.pdf")
    
    if result.success:
        print(f"✅ Processing successful! Report path: {result.final_report_path}")
    else:
        print(f"❌ Processing failed: {result.pipeline_error}")

asyncio.run(main())
```

### Web Interface Usage

```bash
cd frontend
python app.py
# Visit http://localhost:7860
```

## 📁 Project Structure

```
llm_read_paper/
├── tools/                          # 🎯 Core encapsulated services
│   ├── paper_processing_service.py # Complete four-stage pipeline encapsulation
│   ├── pipeline_models.py          # Data model definitions
│   └── example_usage.py            # Usage examples
├── crop_pdf_first_three_page/       # Stage 1: Metadata extraction
├── pdf_content_extractor/           # Stage 2: Full-text OCR
├── section_data_extractor/          # Stage 3: Structured parsing
├── report_generator/                # Stage 4: Report generation
├── frontend/                        # Web user interface
├── utils/                           # Utility functions
├── resources/                       # Prompt templates
└── example_pdfs/                    # Sample PDF files
```

## 📖 Detailed Documentation

- [New Engineer Quick Start Guide](新工程师快速入门指南.md)
- [Project Function Analysis Report](项目功能分析报告.md)
- [Project Summary Report](项目总结报告.md)

## 🔧 Advanced Usage

### Custom Configuration

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

### Batch Processing

```python
import asyncio
from pathlib import Path

async def batch_process():
    pdf_files = list(Path("papers/").glob("*.pdf"))
    
    for pdf_file in pdf_files:
        result = await process_paper_pipeline(str(pdf_file))
        print(f"Processing {pdf_file.name}: {'Success' if result.success else 'Failed'}")

asyncio.run(batch_process())
```

## 🤝 Contributing Guidelines

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [MinerU](https://github.com/opendatalab/MinerU) - High-quality PDF OCR service
- [Mistral AI](https://mistral.ai/) - Powerful LLM API service
- [Gradio](https://gradio.app/) - Simple and easy-to-use web interface framework

## 📞 Contact

If you have questions or suggestions, please contact us through:

- Submit an [Issue](https://github.com/Rostopher/llm_read_paper/issues)
- Start a [Discussion](https://github.com/Rostopher/llm_read_paper/discussions)

---

**Developed with assistance from Claude 4.0 Opus** 🤖
