# -*- coding: utf-8 -*-
"""
测试优化后的文档生成流程，验证基于前序文档的文档生成功能
"""

import unittest
from unittest.mock import MagicMock
import json
from pathlib import Path


class MockPromptManager:
    """模拟提示词管理器"""
    
    def __init__(self):
        self.prompts = {
            'requirement_confirm': '# 需求确认文档提示词\n请生成需求确认文档',
            'prd': '# 产品需求文档(PRD)提示词\n请生成PRD文档',
            'workflow': '# 应用流程文档提示词\n请生成应用流程文档',
            'tech_stack': '# 技术栈文档提示词\n请生成技术栈文档',
            'frontend': '# 前端设计指南提示词\n请生成前端设计文档',
            'backend': '# 后端架构设计提示词\n请生成后端设计文档',
            'dev_plan': '# 项目开发计划提示词\n请生成开发计划文档'
        }
    
    def get_prompt(self, doc_type):
        return self.prompts.get(doc_type)
    
    def is_prompt_available(self, doc_type):
        return doc_type in self.prompts


class MockAIClient:
    """模拟AI客户端"""
    
    def __init__(self):
        self.generated_docs = {
            'requirement_confirm': '# 需求确认文档\n这是需求确认文档内容',
            'prd': '# 产品需求文档(PRD)\n这是PRD文档内容',
            'workflow': '# 应用流程文档\n这是应用流程文档内容',
            'tech_stack': '# 技术栈文档\n这是技术栈文档内容',
            'frontend': '# 前端设计指南\n这是前端设计文档内容',
            'backend': '# 后端架构设计\n这是后端设计文档内容',
            'dev_plan': '# 项目开发计划\n这是开发计划文档内容'
        }
        self.call_history = []
    
    def generate_document(self, prompt, context=None, model_name=None, temperature=0.7, max_tokens=4000):
        # 记录调用历史，用于检查上下文传递
        if context:
            self.call_history.append({
                'doc_type': self._get_doc_type_from_prompt(prompt),
                'context': context
            })
        
        # 从预设响应中返回文档内容
        doc_type = self._get_doc_type_from_prompt(prompt)
        return self.generated_docs.get(doc_type, "未知文档类型")
    
    def _get_doc_type_from_prompt(self, prompt):
        """从提示词中提取文档类型"""
        if "需求确认文档提示词" in prompt:
            return 'requirement_confirm'
        elif "产品需求文档(PRD)提示词" in prompt:
            return 'prd'
        elif "应用流程文档提示词" in prompt:
            return 'workflow'
        elif "技术栈文档提示词" in prompt:
            return 'tech_stack'
        elif "前端设计指南提示词" in prompt:
            return 'frontend'
        elif "后端架构设计提示词" in prompt:
            return 'backend'
        elif "项目开发计划提示词" in prompt:
            return 'dev_plan'
        return 'unknown'


class TestDocumentContextChain(unittest.TestCase):
    """测试文档链上下文传递功能"""
    
    def test_document_context_chain(self):
        """测试文档链上下文传递，验证优化后的文档生成流程"""
        # 导入DocumentPipeline
        from docugen.core.pipeline import DocumentPipeline
        
        # 创建模拟对象
        mock_prompt_manager = MockPromptManager()
        mock_ai_client = MockAIClient()
        
        # 创建文档生成流水线
        pipeline = DocumentPipeline(mock_prompt_manager, mock_ai_client)
        
        # 设置测试项目信息
        project_info = {
            "name": "测试项目",
            "description": "这是一个测试项目，用于验证优化后的文档生成流程。"
        }
        
        # 生成所有文档
        documents = pipeline.run(project_info)
        
        # 验证生成了正确数量的文档
        self.assertEqual(len(documents), 7, "应该生成7个文档")
        
        # 验证所有文档类型都已生成
        expected_doc_types = [
            'requirement_confirm', 'prd', 'workflow', 
            'tech_stack', 'frontend', 'backend', 'dev_plan'
        ]
        for doc_type in expected_doc_types:
            self.assertIn(doc_type, documents, f"应该生成{doc_type}文档")
        
        # 验证上下文链接
        call_history = mock_ai_client.call_history
        
        # PRD文档应该收到需求确认文档作为上下文
        prd_call = next((call for call in call_history if call['doc_type'] == 'prd'), None)
        self.assertIsNotNone(prd_call, "应该有PRD文档的调用记录")
        self.assertIn('document_chain', prd_call['context'], "PRD文档上下文应包含document_chain")
        self.assertEqual(len(prd_call['context']['document_chain']), 1, "PRD文档应该有1个前序文档")
        self.assertEqual(prd_call['context']['document_chain'][0]['type'], 'requirement_confirm', 
                         "PRD的前序文档应该是需求确认文档")
        
        # 流程文档应该收到两个前序文档
        workflow_call = next((call for call in call_history if call['doc_type'] == 'workflow'), None)
        self.assertIsNotNone(workflow_call, "应该有流程文档的调用记录")
        self.assertIn('document_chain', workflow_call['context'], "流程文档上下文应包含document_chain")
        self.assertEqual(len(workflow_call['context']['document_chain']), 2, 
                       "流程文档应该有2个前序文档")
        
        # 技术栈文档应该收到三个前序文档
        tech_stack_call = next((call for call in call_history if call['doc_type'] == 'tech_stack'), None)
        self.assertIsNotNone(tech_stack_call, "应该有技术栈文档的调用记录")
        self.assertIn('document_chain', tech_stack_call['context'], "技术栈文档上下文应包含document_chain")
        self.assertEqual(len(tech_stack_call['context']['document_chain']), 3, 
                       "技术栈文档应该有3个前序文档")
        
        # 前端设计文档应该收到四个前序文档
        frontend_call = next((call for call in call_history if call['doc_type'] == 'frontend'), None)
        self.assertIsNotNone(frontend_call, "应该有前端设计文档的调用记录")
        self.assertIn('document_chain', frontend_call['context'], "前端设计文档上下文应包含document_chain")
        self.assertEqual(len(frontend_call['context']['document_chain']), 4, 
                       "前端设计文档应该有4个前序文档")
        
        # 后端设计文档应该收到四个前序文档
        backend_call = next((call for call in call_history if call['doc_type'] == 'backend'), None)
        self.assertIsNotNone(backend_call, "应该有后端设计文档的调用记录")
        self.assertIn('document_chain', backend_call['context'], "后端设计文档上下文应包含document_chain")
        self.assertEqual(len(backend_call['context']['document_chain']), 4, 
                       "后端设计文档应该有4个前序文档")
        
        # 开发计划文档应该收到所有前面的文档作为上下文
        dev_plan_call = next((call for call in call_history if call['doc_type'] == 'dev_plan'), None)
        self.assertIsNotNone(dev_plan_call, "应该有开发计划文档的调用记录")
        self.assertIn('document_chain', dev_plan_call['context'], "开发计划文档上下文应包含document_chain")
        self.assertEqual(len(dev_plan_call['context']['document_chain']), 6, 
                       "开发计划文档应该有6个前序文档")


if __name__ == '__main__':
    unittest.main() 