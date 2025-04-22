#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试运行器
运行所有单元测试并生成测试报告
"""

import os
import sys
import unittest
import logging
import json
from tests.test_config import init_test_env
from tests.mock_ai_client import MockAIClient
from tests.mock_prompt_manager import MockPromptManager
from docugen.api.client import AIClient
from docugen.utils.prompt import PromptManager

# 设置环境变量
os.environ["OPENAI_API_KEY"] = "sk-test-key"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 打补丁替换真实组件为模拟组件
def patch_components():
    """替换真实组件为模拟组件"""
    # 保存原始类
    global original_ai_client, original_prompt_manager
    original_ai_client = AIClient
    original_prompt_manager = PromptManager
    
    # 创建模拟AI客户端实例
    mock_client = MockAIClient()
    
    # 完全替换AIClient的generate_document方法
    def patched_generate_document(self, 
                                prompt: str, 
                                context=None,
                                model_name=None,
                                temperature=0.7,
                                max_tokens=4000):
        """
        模拟生成文档内容的补丁函数，处理pipeline发送的字符串格式context
        """
        if hasattr(self, 'logger') and hasattr(self.logger, 'logger'):
            self.logger.logger.debug("使用补丁版的generate_document")
        
        # 尝试解析上下文，适配字符串和字典两种情形
        try:
            if isinstance(context, str):
                context_data = json.loads(context)
                project_info = context_data.get("project_info", {})
            else:
                project_info = context.get("project_info", {}) if context else {}
            
            project_name = project_info.get("name", "未命名项目")
        except Exception as e:
            if hasattr(self, 'logger') and hasattr(self.logger, 'logger'):
                self.logger.logger.warning(f"解析上下文时出错: {str(e)}")
            project_name = "测试项目"
        
        # 根据提示词判断文档类型
        doc_type = None
        
        # 检查是哪种文档类型
        doc_type_mapping = {
            "brainstorm": ["构思", "brainstorm"],
            "requirement_confirm": ["需求确认", "requirement_confirm"],
            "prd": ["产品需求", "prd"],
            "workflow": ["应用流程", "workflow"],
            "tech_stack": ["技术栈", "tech_stack"],
            "frontend": ["前端设计", "frontend"],
            "backend": ["后端架构", "backend"],
            "dev_plan": ["开发计划", "dev_plan"]
        }
        
        for dtype, keywords in doc_type_mapping.items():
            for keyword in keywords:
                if keyword.lower() in prompt.lower():
                    doc_type = dtype
                    break
            if doc_type:
                break
        
        # 如果找到匹配的文档类型，则生成对应的文档
        if doc_type and hasattr(self, f"_generate_{doc_type}"):
            generator_func = getattr(self, f"_generate_{doc_type}")
            return generator_func(project_name)
        
        # 默认返回通用文档
        return f"# 模拟生成的文档\n\n这是为{project_name}项目生成的模拟文档内容。"
    
    # 将AIClient替换为MockAIClient
    for attr_name in dir(MockAIClient):
        # 排除特殊属性和私有属性
        if not attr_name.startswith('__') and not attr_name.startswith('_MockAIClient'):
            attr = getattr(MockAIClient, attr_name)
            if callable(attr) and attr_name != 'generate_document':  # 排除generate_document
                setattr(AIClient, attr_name, attr)
    
    # 特别处理generate_document方法
    AIClient.generate_document = patched_generate_document
    
    # 为AIClient添加生成文档的辅助方法
    for attr_name in dir(mock_client):
        if attr_name.startswith('_generate_'):
            setattr(AIClient, attr_name, getattr(mock_client, attr_name))
    
    # 为AIClient添加测试文档字典
    AIClient.test_documents = mock_client.test_documents
    
    # 将提示词管理器替换为模拟管理器
    PromptManager.__init__ = MockPromptManager.__init__
    PromptManager.get_prompt = MockPromptManager.get_prompt
    PromptManager.get_all_prompts = MockPromptManager.get_all_prompts
    PromptManager.list_available_doc_types = MockPromptManager.list_available_doc_types
    
    # 为测试预先添加requirement_confirm文档，解决依赖问题
    def initialize_documents(self):
        if not hasattr(self, 'documents'):
            self.documents = {}
        if not hasattr(self, 'status'):
            self.status = {}
        # 预先添加需求确认文档
        project_name = "测试项目"
        self.documents['requirement_confirm'] = self._generate_requirement_confirm(project_name)
        
    # 将初始化文档方法添加到AIClient
    AIClient.initialize_documents = initialize_documents
    
    print("已将真实组件替换为模拟组件")

def restore_components():
    """恢复真实组件"""
    global original_ai_client, original_prompt_manager
    
    # 恢复AI客户端
    if 'original_ai_client' in globals():
        # 获取所有当前AIClient中不是原始类的属性，将其删除
        for attr_name in list(vars(AIClient)):
            if not hasattr(original_ai_client, attr_name) or attr_name == '__init__':
                delattr(AIClient, attr_name)
        
        # 恢复原始方法
        for attr_name in dir(original_ai_client):
            if not attr_name.startswith('__') and callable(getattr(original_ai_client, attr_name)):
                setattr(AIClient, attr_name, getattr(original_ai_client, attr_name))
    
    # 恢复提示词管理器
    if 'original_prompt_manager' in globals():
        PromptManager.__init__ = original_prompt_manager.__init__
        PromptManager.get_prompt = original_prompt_manager.get_prompt
        PromptManager.get_all_prompts = original_prompt_manager.get_all_prompts
        PromptManager.list_available_doc_types = original_prompt_manager.list_available_doc_types
    
    print("已恢复真实组件")

if __name__ == "__main__":
    print("开始运行测试...")
    
    # 初始化测试环境
    print("初始化测试环境...")
    init_test_env()
    
    # 打补丁
    print("替换组件...")
    patch_components()
    
    try:
        # 导入测试用例
        from tests.test_document_generator import TestDocumentGenerator
        
        # 创建测试套件
        test_suite = unittest.TestLoader().loadTestsFromTestCase(TestDocumentGenerator)
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
        
        # 输出结果
        if result.wasSuccessful():
            print("所有测试通过!")
            sys.exit(0)
        else:
            print(f"测试失败: {len(result.errors)} 错误, {len(result.failures)} 失败")
            sys.exit(1)
    finally:
        # 恢复组件
        restore_components() 