"""
模拟AI客户端
用于测试文档生成功能，避免实际调用OpenAI API
"""

import json
import logging
from typing import Dict, Any, Optional

class MockAIClient:
    """
    模拟AI客户端
    返回预定义的响应而不是实际调用API
    """
    
    def __init__(self, api_key: str = "mock-key", base_url: Optional[str] = None):
        """初始化模拟AI客户端"""
        self.logger = logging.getLogger("test.mock_ai_client")
        self.api_key = api_key
        self.base_url = base_url
        
        # 测试用的文档内容
        self.test_documents = {
            "brainstorm": self._generate_brainstorm,
            "requirement_confirm": self._generate_requirement_confirm,
            "prd": self._generate_prd,
            "workflow": self._generate_workflow,
            "tech_stack": self._generate_tech_stack,
            "frontend": self._generate_frontend,
            "backend": self._generate_backend,
            "dev_plan": self._generate_dev_plan
        }
    
    def generate_document(self, 
                        prompt: str, 
                        context: str,
                        model_name: Optional[str] = None,
                        temperature: float = 0.7,
                        max_tokens: int = 4000) -> str:
        """
        模拟生成文档内容
        :param prompt: 提示词
        :param context: 上下文信息
        :param model_name: 要使用的模型名称
        :param temperature: 温度参数，控制输出的随机性
        :param max_tokens: 最大生成令牌数
        :return: 生成的文档内容
        """
        # 兼容真实AIClient的日志记录方式
        if hasattr(self, 'logger') and hasattr(self.logger, 'info'):
            self.logger.info("模拟AI客户端生成文档")
        elif hasattr(self, 'logger') and hasattr(self.logger, 'logger'):
            # 适配DebugLogger类
            self.logger.logger.info("模拟AI客户端生成文档")
        
        # 尝试解析上下文
        try:
            context_data = json.loads(context)
            project_info = context_data.get("project_info", {})
            project_name = project_info.get("name", "未命名项目")
        except Exception as e:
            if hasattr(self, 'logger') and hasattr(self.logger, 'warning'):
                self.logger.warning(f"解析上下文时出错: {str(e)}")
            elif hasattr(self, 'logger') and hasattr(self.logger, 'logger'):
                self.logger.logger.warning(f"解析上下文时出错: {str(e)}")
            project_name = "测试项目"
        
        # 尝试从上下文中获取文档类型
        doc_type = None
        
        # 直接判断文档类型
        for doc_key in self.test_documents.keys():
            if doc_key in prompt.lower():
                doc_type = doc_key
                break
        
        # 如果找到匹配的文档类型，则生成对应的文档
        if doc_type and doc_type in self.test_documents:
            generator_func = self.test_documents[doc_type]
            return generator_func(project_name)
        
        # 默认返回通用文档
        return f"# 模拟生成的文档\n\n这是为{project_name}项目生成的模拟文档内容。"
    
    def _generate_brainstorm(self, project_name: str) -> str:
        """生成构思梳理文档"""
        return f"""# {project_name} 构思梳理

## 项目概述

本文档为{project_name}项目的构思梳理，包含关键功能点、用户需求和技术考量。

## 核心功能

1. 文档自动生成
2. 多格式支持
3. 模板定制

## 用户需求

- 简化文档生成流程
- 保持文档一致性
- 提高文档质量

## 技术考量

- 使用Python开发
- 集成OpenAI API
- 模块化设计
"""
    
    def _generate_requirement_confirm(self, project_name: str) -> str:
        """生成需求确认文档"""
        return f"""# {project_name} 需求确认

## 项目基本信息

- 项目名称：{project_name}
- 项目类型：文档生成工具
- 预计周期：6周

## 需求确认

### 确认的核心需求

1. 自动生成多种类型文档
2. 支持多种输出格式
3. 提供版本控制功能

### 用户期望

- 简单易用的界面
- 高质量文档输出
- 灵活的定制选项

## 项目边界

### 包含内容

- 基础文档生成功能
- 常用文档模板
- 版本历史记录

### 排除内容

- 复杂图表生成
- 第三方系统集成
- 实时协作编辑
"""
    
    def _generate_prd(self, project_name: str) -> str:
        """生成产品需求文档"""
        return f"""# {project_name} 产品需求文档

## 产品概述

{project_name}是一个智能文档生成工具，旨在简化软件开发流程中的文档创建过程。

## 功能需求

### 1. 文档生成

- 支持基于模板的文档生成
- 支持多种文档类型
- 文档内容智能填充

### 2. 格式转换

- 支持Markdown、HTML和PDF输出
- 支持自定义样式

### 3. 版本管理

- 自动保存文档历史版本
- 支持版本比较和回滚

## 非功能需求

- 性能：文档生成时间不超过30秒
- 安全：API密钥安全存储
- 可靠性：系统稳定性99.9%
"""
    
    def _generate_workflow(self, project_name: str) -> str:
        """生成应用流程文档"""
        return f"""# {project_name} 应用流程文档

## 文档生成流程

1. 项目信息收集
2. 提示词准备
3. API调用生成内容
4. 内容验证
5. 格式化输出
6. 版本存储

## 用户交互流程

1. 用户输入项目信息
2. 选择文档类型
3. 等待生成过程
4. 查看和导出结果

## 错误处理流程

1. 输入验证
2. API错误重试
3. 内容验证失败处理
4. 用户反馈机制
"""
    
    def _generate_tech_stack(self, project_name: str) -> str:
        """生成技术栈文档"""
        return f"""# {project_name} 技术栈文档

## 核心技术

- 编程语言：Python 3.10
- API集成：OpenAI API
- 文档处理：Markdown, Jinja2

## 依赖库

- openai：API交互
- python-dotenv：环境变量管理
- rich：终端UI增强
- tqdm：进度显示

## 开发工具

- IDE：VS Code
- 版本控制：Git
- 测试框架：pytest
"""
    
    def _generate_frontend(self, project_name: str) -> str:
        """生成前端设计文档"""
        return f"""# {project_name} 前端设计指南

## 界面设计

- 命令行界面
- 简洁明了的交互方式
- 进度实时显示

## 交互流程

1. 命令行参数设计
2. 交互式问答
3. 结果展示

## 视觉风格

- 使用rich库增强终端输出
- 文字颜色编码：成功(绿)、警告(黄)、错误(红)
- 进度条使用tqdm实现
"""
    
    def _generate_backend(self, project_name: str) -> str:
        """生成后端架构文档"""
        return f"""# {project_name} 后端架构设计

## 模块结构

- api：API交互
- core：核心逻辑
- utils：工具函数
- config：配置管理

## 数据流

1. 用户输入 -> 配置解析
2. 提示词加载 -> API调用
3. 内容处理 -> 文档生成
4. 结果存储 -> 版本管理

## 错误处理

- 异常捕获和处理
- 日志记录
- 重试机制
"""
    
    def _generate_dev_plan(self, project_name: str) -> str:
        """生成开发计划文档"""
        return f"""# {project_name} 开发计划

## 开发阶段

1. 需求分析和设计 (1周)
2. 核心功能开发 (2周)
3. UI实现 (1周)
4. 测试和修复 (1周)
5. 文档和部署 (1周)

## 优先级规划

- P0：核心文档生成功能
- P1：多格式支持、版本控制
- P2：高级特性、多语言支持

## 里程碑

1. Alpha版：基础文档生成 (第3周)
2. Beta版：完整功能集 (第5周)
3. 正式版：稳定可靠 (第6周)
""" 