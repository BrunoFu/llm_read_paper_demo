# 项目工程化待办事项 (ToDo)

本文档旨在规划项目从当前原型阶段向更健壮、可维护的工程级服务演进的关键任务。

---

## Part 1: 增强系统健壮性与错误处理 (Robustness & Error Handling)

此部分任务专注于加固现有的处理流水线，提高其在异常情况下的稳定性和可追踪性。

### 关键任务 (High Priority)

- [ ] **配置中心化**:
  - [ ] 将所有硬编码的 API Key、Token、以及文件路径等配置，全部移出代码。
  - [ ] 创建一个 `.env` 文件和配套的 `config.py` 来统一管理所有配置项。

- [ ] **统一日志系统**:
  - [ ] 引入 `logging` 模块到所有核心脚本中。
  - [ ] 实现结构化日志，确保每一条日志都包含时间戳、日志级别、模块名，以及最重要的 **任务标识符 (如 `pdf_filename` 或未来的 `task_id`)**。
  - [ ] 所有日志统一输出到 `logs/` 目录下，按日期或任务ID进行分割。

- [ ] **Token/Key 失效管理**:
  - [ ] 为 MinerU 和 Mistral AI 的 API 调用增加特定的异常捕获，当识别到 `401 Unauthorized` 或 `403 Forbidden` 错误时，记录明确的“认证失败”日志。
  - [ ] (进阶) 设立一个告警机制（如邮件、钉钉/Slack机器人），在认证失败时立即通知管理员。

### 中等任务 (Medium Priority)

- [ ] **完善文件处理逻辑**:
  - [ ] 在 `crop_pdf_first_three_page` 模块中，增加对加密或损坏PDF的异常捕获。
  - [ ] 优雅地处理页数不足3页的PDF，应视为正常情况继续处理，而不是报错中止。

- [ ] **数据校验 (Pydantic)**:
  - [ ] 为 MinerU API 返回的 `layout.json` 和 LLM 返回的 `metadata.json` 定义 Pydantic 模型。
  - [ ] 在解析这些JSON数据前，先进行数据模型校验，确保字段和类型符合预期，对于不匹配的情况进行捕获和记录。

- [ ] **死信队列机制**:
  - [ ] 对于 MinerU API 轮询超时的任务，应将其 `batch_id` 和原始文件信息记录到一个专门的失败日志文件（如 `logs/dead_letter_tasks.log`）中，便于人工排查和重试。

### 长期优化 (Low Priority)

- [ ] **引入规则辅助校验**:
  - [ ] 在第二阶段 LLM 识别章节框架后，加入简单的规则校验，例如检查“参考文献”章节是否在“结论”之后，以初步判断章节划分的逻辑合理性。
- [ ] **提升报告连贯性**:
  - [ ] 在第三阶段报告合成时，尝试为每个章节的分析之间增加由 LLM 生成的过渡性语句，使最终报告读起来更自然。

---

## Part 2: 后端 API 化与服务封装 (API & Service Wrapper)

此部分任务专注于将现有的流水线包装成一个标准的、异步的后端服务。

### 核心架构搭建 (High Priority)

- [ ] **选择并搭建 Web 框架**:
  - [ ] 选择一个异步 Web 框架（如 `FastAPI`, `Quart`）。
  - [ ] 搭建项目的基础目录结构。

- [ ] **设计并实现核心 API 端点**:
  - [ ] `POST /api/v1/papers`: 用于上传PDF文件，接收文件后立即创建一个任务并返回 `task_id`。
  - [ ] `GET /api/v1/tasks/{task_id}`: 用于客户端轮询任务处理状态。
  - [ ] `GET /api/v1/papers/{paper_id}/report`: 用于在任务完成后获取最终结果的链接。

- [ ] **引入异步任务队列**:
  - [ ] 选择并集成一个任务队列系统（如 `Celery` with `Redis` or `RabbitMQ`）。
  - [ ] 这是实现异步处理、解耦HTTP请求和后台重度计算的关键。

- [ ] **代码逻辑重构**:
  - [ ] **（核心）** 将所有 `.py` 脚本的核心处理逻辑，重构为可被导入和调用的函数。**坚决避免**在 API 代码中通过 `subprocess` 调用命令行。
  - [ ] 每个 Worker 任务应该直接调用这些重构后的函数。

### 数据库与存储 (Medium Priority)

- [ ] **设计数据库模型**:
  - [ ] 使用 `SQLAlchemy` 或类似的 ORM，设计 `Task` 和 `Paper` 的数据表模型。
  - [ ] `Task` 表应至少包含 `task_id`, `status`, `error_message`, `created_at`, `updated_at`, `result_paper_id` 等字段。
- [ ] **集成对象存储**:
  - [ ] 选择一个对象存储方案（如 `MinIO` 用于本地部署，或 `AWS S3` 用于云端）。
  - [ ] 将所有持久化产物（如最终的JSON和Markdown报告）根据其ID存入对象存储，而不是本地文件系统。

### 部署与运维 (Low Priority)

- [ ] **编写 Dockerfile**:
  - [ ] 为 API 服务和 Worker 进程分别创建 `Dockerfile`，实现容器化部署。
  - [ ] 使用 `docker-compose` 编排整个服务栈（API, Worker, Redis, 数据库等）。
- [ ] **建立CI/CD流程**:
  - [ ] 配置 GitHub Actions 或 Jenkins，实现代码提交后自动测试和部署。

---
你作为 **Claude 4.0 Opus** 