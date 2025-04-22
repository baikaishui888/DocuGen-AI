# DocuGen AI

DocuGen AI是一个智能文档生成工具，通过AI技术自动创建高质量的软件项目文档。

## 功能特点

- 自动生成完整的项目文档，包括PRD、技术架构、开发计划等
- 支持多种文档格式输出（Markdown、HTML、PDF）
- 完善的文档模板系统和变量替换功能
- 单文档自动保存功能，无需等待全部文档生成完成
- 文档版本控制和变更跟踪
- 中英文双语支持
- Web可视化界面，实时查看生成进度
- 模型调试功能，方便开发者调试提示词和输出效果

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/docugen-ai.git
cd docugen-ai

# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 设置API密钥
export OPENAI_API_KEY=your-api-key
# 或在Windows上
set OPENAI_API_KEY=your-api-key
```

## 使用方法

### 基本用法

```bash
python -m docugen --project "我的项目" --description "这是一个示例项目"
```

### 高级选项

```bash
# 使用Web界面
python -m docugen --project "我的项目" --web

# 指定模型
python -m docugen --project "我的项目" --model "gpt-4"

# 自定义API URL
python -m docugen --project "我的项目" --api-base "https://your-api-endpoint"

# 启用调试模式
python -m docugen --project "我的项目" --debug

# 启用模型输入输出调试
python -m docugen --project "我的项目" --debug-model
```

## 项目结构

```
docugen/
├── api/                # API通信模块
│   ├── client.py       # OpenAI客户端
│   └── error.py        # 错误处理
├── core/               # 核心功能模块
│   ├── pipeline.py     # 文档生成流水线
│   ├── generator.py    # 文档生成器
│   ├── validator.py    # 内容验证器
│   ├── version.py      # 版本管理器
│   ├── exporter.py     # 文档导出器
│   └── renderer.py     # 文档渲染器
├── utils/              # 工具函数
│   ├── prompt.py       # 提示词管理
│   ├── file.py         # 文件操作
│   ├── logger.py       # 日志工具
│   ├── template.py     # 模板系统
│   ├── variable.py     # 变量替换引擎
│   ├── cli.py          # 命令行界面
│   ├── web_server.py   # Web服务器
│   ├── progress.py     # 进度显示系统
│   ├── debug_tracer.py # 模型调试跟踪器
│   ├── i18n.py         # 国际化支持
│   ├── analyzer.py     # 文档结构分析器
│   ├── html_formatter.py # HTML格式化工具
│   └── pdf_generator.py  # PDF生成工具
├── web/                # Web前端
│   └── static/         # 静态资源文件
│       ├── css/        # 样式文件
│       └── js/         # JavaScript脚本
├── translations/       # 翻译文件
├── config.py           # 配置管理
└── main.py             # 入口文件
```

## 环境变量

- `OPENAI_API_KEY`: OpenAI API密钥
- `OPENAI_API_BASE`: 自定义API基础URL（可选）
- `OPENAI_MODEL_NAME`: 指定使用的模型名称（可选）
- `DOCUGEN_DEBUG`: 启用调试模式（设置为"true"启用）
- `DOCUGEN_DEBUG_MODEL`: 启用模型输入输出调试（设置为"true"启用）

## 已实现功能

- [x] 基础文档生成器
- [x] 文档生成流程优化
- [x] 提示词管理系统
- [x] 模板系统
- [x] 变量替换引擎
- [x] Markdown格式输出
- [x] HTML输出支持
- [x] PDF输出支持
- [x] 命令行交互界面
- [x] 命令行界面功能优化
- [x] 进度显示系统
- [x] Web可视化界面
- [x] Web可视化界面优化
- [x] 内容一致性检查
- [x] 版本控制系统
- [x] 多语言支持
- [x] 文档结构分析
- [x] 自定义API基础URL支持
- [x] 自定义模型名称支持
- [x] 模型调试功能
- [x] 错误处理系统
- [x] 配置管理
- [x] 文件管理器
- [x] AI接口客户端
- [x] 单文档自动保存功能

## 待开发功能

- [ ] 前端可视化界面
- [ ] 集成CI/CD流程
- [ ] 团队协作功能

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 最后更新

- 更新时间：[2025-04-22 14:39] 