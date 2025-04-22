#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试运行器
运行所有单元测试并生成测试报告
"""

import unittest
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置环境变量（测试环境）
os.environ["OPENAI_API_KEY"] = "sk-test-key"  # 测试用假密钥

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入测试配置
from tests.test_config import init_test_env

# 导入模拟组件
from tests.mock_ai_client import MockAIClient
from tests.mock_prompt_manager import MockPromptManager

# 导入需要替换的模块
from docugen.api.client import AIClient
from docugen.utils.prompt import PromptManager

# 使用补丁替换真实组件为模拟组件
def patch_components():
    """用模拟组件替换真实组件"""
    # 保存原始类
    global original_ai_client, original_prompt_manager
    original_ai_client = AIClient
    original_prompt_manager = PromptManager
    
    # 将AI客户端替换为模拟客户端
    AIClient.__init__ = MockAIClient.__init__
    AIClient.generate_document = MockAIClient.generate_document
    
    # 将提示词管理器替换为模拟管理器
    PromptManager.__init__ = MockPromptManager.__init__
    PromptManager.get_prompt = MockPromptManager.get_prompt
    PromptManager.get_all_prompts = MockPromptManager.get_all_prompts
    PromptManager.list_available_doc_types = MockPromptManager.list_available_doc_types
    
    print("已将真实组件替换为模拟组件")

def restore_components():
    """恢复真实组件"""
    global original_ai_client, original_prompt_manager
    
    # 恢复AI客户端
    if 'original_ai_client' in globals():
        AIClient.__init__ = original_ai_client.__init__
        AIClient.generate_document = original_ai_client.generate_document
    
    # 恢复提示词管理器
    if 'original_prompt_manager' in globals():
        PromptManager.__init__ = original_prompt_manager.__init__
        PromptManager.get_prompt = original_prompt_manager.get_prompt
        PromptManager.get_all_prompts = original_prompt_manager.get_all_prompts
        PromptManager.list_available_doc_types = original_prompt_manager.list_available_doc_types
    
    print("已恢复真实组件")

def run_tests():
    """运行所有测试"""
    print("初始化测试环境...")
    # 初始化测试环境
    init_test_env()
    
    print("替换组件...")
    # 替换组件
    patch_components()
    
    try:
        print("开始运行测试...")
        # 发现并运行所有测试
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover(start_dir="tests", pattern="test_*.py")
        
        # 运行测试
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        
        # 返回测试结果
        return result.wasSuccessful()
    finally:
        # 恢复组件
        restore_components()

if __name__ == "__main__":
    print("开始运行 DocuGen AI 测试...")
    success = run_tests()
    sys.exit(0 if success else 1) 