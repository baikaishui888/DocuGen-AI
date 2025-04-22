#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文档生成测试脚本 - 测试文档生成流程
"""

import os
import sys
import logging
import json
from docugen.core.generator import DocumentGenerator
from docugen.utils.prompt import PromptManager
from docugen.core.pipeline import DocumentPipeline, DocumentStatus
from docugen.config import Config

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("test_docgen")

class MockAIClient:
    """模拟AI客户端，用于测试"""
    
    def __init__(self):
        self.current_doc_type = None
    
    def set_current_doc_type(self, doc_type):
        """设置当前文档类型"""
        self.current_doc_type = doc_type
    
    def generate_document(self, prompt, context=None, model_name=None, temperature=0.7, max_tokens=4000):
        """模拟生成文档内容"""
        # 获取项目名称
        project_name = context.get("project_info", {}).get("name", "测试项目") if context else "测试项目"
        
        doc_type = self.current_doc_type or "unknown"
        logger.info(f"模拟生成文档: {doc_type} (项目: {project_name})")
        
        # 根据文档类型返回不同的模拟内容
        if doc_type == "requirement_confirm":
            return f"# 需求确认文档\n\n这是为项目 **{project_name}** 生成的需求确认文档模拟内容。\n\n## 项目信息\n\n- 项目名称: {project_name}\n- 项目目标: 实现智能文档生成系统\n\n## 功能需求\n\n1. 自动生成多种项目文档\n2. 支持多种输出格式\n3. 版本控制和历史记录"
        
        elif doc_type == "brainstorm":
            return f"# 构思梳理文档\n\n这是为项目 **{project_name}** 生成的构思梳理文档模拟内容。\n\n## 核心理念\n\n使用AI自动化生成高质量项目文档，减少手动编写文档的工作量。"
        
        elif doc_type == "prd":
            return f"# 产品需求文档(PRD)\n\n这是为项目 **{project_name}** 生成的PRD模拟内容。\n\n## 产品概述\n\n智能文档生成工具，简化项目文档的创建和管理。"
        
        elif doc_type == "workflow":
            return f"# 应用流程文档\n\n这是为项目 **{project_name}** 生成的应用流程文档模拟内容。\n\n## 主要流程\n\n1. 用户输入项目信息\n2. 系统调用AI生成文档\n3. 保存并展示生成的文档"
        
        elif doc_type == "tech_stack":
            return f"# 技术栈文档\n\n这是为项目 **{project_name}** 生成的技术栈文档模拟内容。\n\n## 后端技术\n\n- Python 3.10\n- OpenAI API\n\n## 前端技术\n\n- HTML/CSS/JavaScript"
        
        elif doc_type == "frontend":
            return f"# 前端设计指南\n\n这是为项目 **{project_name}** 生成的前端设计指南模拟内容。\n\n## 设计原则\n\n简洁、直观、高效的用户界面设计。"
        
        elif doc_type == "backend":
            return f"# 后端架构设计\n\n这是为项目 **{project_name}** 生成的后端架构设计模拟内容。\n\n## 核心模块\n\n1. 文档生成引擎\n2. 提示词管理\n3. 文件操作工具"
        
        elif doc_type == "dev_plan":
            return f"# 项目开发计划\n\n这是为项目 **{project_name}** 生成的开发计划模拟内容。\n\n## 开发阶段\n\n1. 需求分析 (1周)\n2. 设计 (2周)\n3. 开发 (4周)\n4. 测试 (2周)\n5. 部署 (1周)"
        
        else:
            return f"# 通用文档\n\n这是为项目 **{project_name}** 生成的通用文档模拟内容。"

class TestDocumentPipeline(DocumentPipeline):
    """测试用的文档生成流水线，增加了设置当前文档类型的功能"""
    
    def generate_document(self, doc_type, project_info):
        """重写generate_document方法，增加设置当前文档类型的步骤"""
        # 设置当前文档类型
        if hasattr(self.ai_client, 'set_current_doc_type'):
            self.ai_client.set_current_doc_type(doc_type)
        
        # 调用父类方法生成文档
        return super().generate_document(doc_type, project_info)

def test_generate_all_documents():
    """测试生成所有文档"""
    logger.info("开始测试生成所有文档...")
    
    # 获取配置
    config = Config()
    prompts_dir = config.get("paths.prompts_dir") or "../文档提示词"
    
    # 初始化组件
    prompt_manager = PromptManager(prompts_dir)
    mock_ai_client = MockAIClient()
    
    # 使用测试版本的流水线
    pipeline = TestDocumentPipeline(prompt_manager, mock_ai_client)
    
    # 项目信息
    project_info = {
        "name": "DocuGen测试项目",
        "description": "这是一个用于测试文档生成流程的项目"
    }
    
    # 生成所有文档
    try:
        logger.info("开始生成所有文档...")
        documents = pipeline.run(project_info)
        
        # 显示生成结果
        logger.info("\n生成结果:")
        for i, doc_type in enumerate(pipeline.DOC_ORDER):
            if doc_type in documents:
                content = documents[doc_type]
                status = pipeline.get_status(doc_type)
                status_str = "✅" if status == DocumentStatus.COMPLETED else "❌"
                logger.info(f"{i+1}. {status_str} {doc_type}: {len(content)} 字符")
                # 显示文档前几行
                preview = "\n   ".join(content.split("\n")[:3])
                logger.info(f"   预览: {preview}")
            else:
                logger.info(f"{i+1}. ❌ {doc_type}: 未生成")
        
        logger.info("所有文档生成完成")
        return True
    except Exception as e:
        logger.error(f"生成文档失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_generate_all_documents() 