#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
流水线调试脚本 - 用于验证文档生成顺序和依赖关系
"""

import os
import sys
import logging
from docugen.utils.prompt import PromptManager
from docugen.core.pipeline import DocumentPipeline
from docugen.config import Config

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("debug_pipeline")

def check_pipeline_order():
    """检查文档生成顺序和依赖关系"""
    print("\n===== 文档生成流水线检查 =====\n")
    
    # 获取配置
    config = Config()
    prompts_dir = config.get("paths.prompts_dir") or "../文档提示词"
    
    # 创建模拟AI客户端
    class MockAIClient:
        def generate_document(self, *args, **kwargs):
            return "模拟文档内容"
    
    # 初始化流水线
    prompt_manager = PromptManager(prompts_dir)
    pipeline = DocumentPipeline(prompt_manager, MockAIClient())
    
    # 显示文档生成顺序
    print("文档生成顺序:")
    for i, doc_type in enumerate(pipeline.DOC_ORDER):
        print(f"  {i+1}. {doc_type} - {pipeline._get_document_title(doc_type)}")
    
    print("\n文档依赖关系:")
    for doc_type in pipeline.DOC_ORDER:
        if doc_type in pipeline.DOC_DEPENDENCIES:
            deps = pipeline.DOC_DEPENDENCIES[doc_type]
            print(f"  {doc_type} ({pipeline._get_document_title(doc_type)}) 依赖:")
            for dep in deps:
                print(f"    - {dep} ({pipeline._get_document_title(dep)})")
        else:
            print(f"  {doc_type} ({pipeline._get_document_title(doc_type)}) 无依赖")
    
    # 检查PromptManager中的文件映射
    print("\n提示词文件映射:")
    for doc_type, filename in sorted(prompt_manager.DEFAULT_PROMPT_FILES.items()):
        has_prompt = prompt_manager.is_prompt_available(doc_type)
        status = "✅" if has_prompt else "❌"
        print(f"  {status} {doc_type} -> {filename}")
    
    # 检查可用的提示词
    available_prompts = sorted(prompt_manager.get_available_prompts())
    print(f"\n可用的提示词类型: {', '.join(available_prompts)}")
    print(f"总数: {len(available_prompts)}")
    
    # 检查是否所有DOC_ORDER中的文档类型都有对应的提示词
    missing_prompts = [doc_type for doc_type in pipeline.DOC_ORDER if doc_type not in available_prompts]
    if missing_prompts:
        print(f"\n警告: 以下文档类型缺少提示词: {', '.join(missing_prompts)}")
    else:
        print("\n所有文档类型都有对应的提示词")
    
    # 检查依赖关系是否合理
    print("\n依赖关系检查:")
    for doc_type, deps in pipeline.DOC_DEPENDENCIES.items():
        for dep in deps:
            # 检查依赖是否在DOC_ORDER中
            if dep not in pipeline.DOC_ORDER:
                print(f"  错误: {doc_type} 依赖 {dep}，但 {dep} 不在文档生成顺序中")
            
            # 检查依赖是否在当前文档之前
            if pipeline.DOC_ORDER.index(dep) >= pipeline.DOC_ORDER.index(doc_type):
                print(f"  错误: {doc_type} 依赖 {dep}，但 {dep} 在生成顺序中排在 {doc_type} 之后或相同位置")

if __name__ == "__main__":
    check_pipeline_order() 