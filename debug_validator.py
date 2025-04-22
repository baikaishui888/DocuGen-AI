#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
调试验证模块 - 用于验证提示词加载和文档生成顺序
"""

import os
import sys
import logging
from docugen.utils.prompt import PromptManager
from docugen.core.pipeline import DocumentPipeline
from docugen.api.client import AIClient
from docugen.config import Config

# 设置日志配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("debug_validator")

def validate_prompt_loading():
    """验证提示词加载"""
    logger.info("开始验证提示词加载...")
    
    # 获取配置
    config = Config()
    prompts_dir = config.get("paths.prompts_dir")
    
    if not prompts_dir:
        prompts_dir = "./文档提示词"  # 使用默认目录
    
    logger.info(f"提示词目录: {prompts_dir}")
    
    try:
        # 创建提示词管理器
        prompt_manager = PromptManager(prompts_dir)
        
        # 获取可用的提示词类型
        available_prompts = prompt_manager.get_available_prompts()
        logger.info(f"可用的提示词类型: {available_prompts}")
        
        # 获取提示词详情
        prompt_details = prompt_manager.get_prompt_details()
        
        # 显示每个提示词的详细信息
        for doc_type, details in prompt_details.items():
            logger.info(f"\n文档类型: {doc_type}")
            logger.info(f"文件名: {details['filename']}")
            logger.info(f"单词数: {details['word_count']}")
            logger.info(f"标题数: {details['header_count']}")
            logger.info(f"段落数: {details['paragraph_count']}")
            logger.info(f"首标题: {details['first_header']}")
        
        logger.info("提示词加载验证完成")
        return True
        
    except Exception as e:
        logger.error(f"提示词加载验证失败: {str(e)}")
        return False

def validate_document_pipeline():
    """验证文档生成流水线顺序"""
    logger.info("开始验证文档生成流水线...")
    
    # 获取配置
    config = Config()
    prompts_dir = config.get("paths.prompts_dir")
    
    if not prompts_dir:
        prompts_dir = "./文档提示词"  # 使用默认目录
    
    # 创建提示词管理器
    prompt_manager = PromptManager(prompts_dir)
    
    # 创建模拟AI客户端 - 不实际调用API
    class MockAIClient:
        def generate_document(self, prompt, context=None, model_name=None, temperature=0.7, max_tokens=4000):
            return f"模拟生成的文档内容 - {context.get('project_info', {}).get('name', '未命名项目')}"
    
    mock_ai_client = MockAIClient()
    
    # 创建流水线
    pipeline = DocumentPipeline(prompt_manager, mock_ai_client)
    
    # 显示文档生成顺序
    logger.info(f"文档生成顺序: {pipeline.DOC_ORDER}")
    
    # 显示文档依赖关系
    logger.info("文档依赖关系:")
    for doc_type, dependencies in pipeline.DOC_DEPENDENCIES.items():
        logger.info(f"  {doc_type} 依赖: {dependencies}")
    
    # 验证流水线状态初始化
    logger.info("初始文档状态:")
    for doc_type, status in pipeline.status.items():
        logger.info(f"  {doc_type}: {status.value}")
    
    logger.info("文档生成流水线验证完成")
    return True

if __name__ == "__main__":
    logger.info("开始验证程序...")
    
    validate_prompt_loading()
    validate_document_pipeline()
    
    logger.info("验证完成!") 