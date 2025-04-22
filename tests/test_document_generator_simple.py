"""
测试基础文档生成器
"""

import unittest
import os
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MockConfig:
    """模拟配置"""
    def __init__(self):
        self.config = {
            "api": {
                "model": "gpt-4",
                "max_tokens": 1000,
                "temperature": 0.5,
            },
            "paths": {
                "output_dir": "tests/test_output"
            }
        }
    
    def get(self, path, default=None):
        """获取配置"""
        parts = path.split('.')
        config = self.config
        for part in parts:
            if part in config:
                config = config[part]
            else:
                return default
        return config
    
    def get_api_key(self):
        """获取API密钥"""
        return "sk-test-key"

class MockAIClient:
    """模拟AI客户端"""
    def __init__(self, api_key):
        self.api_key = api_key
    
    def generate_document(self, prompt, context):
        """生成文档"""
        return f"""# 测试文档

## 测试标题

这是一个测试生成的文档内容。

## 测试列表

- 项目1
- 项目2
- 项目3
"""

class MockPromptManager:
    """模拟提示词管理器"""
    def __init__(self, prompts_dir):
        self.prompts_dir = prompts_dir
    
    def get_prompt(self, doc_type):
        """获取提示词"""
        return f"测试提示词：{doc_type}"
    
    def list_available_doc_types(self):
        """获取可用文档类型"""
        return ["brainstorm", "prd", "workflow"]

class MockFileManager:
    """模拟文件管理器"""
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def save_document(self, project_name, doc_type, content):
        """保存文档"""
        folder = self.output_dir / project_name / "current"
        os.makedirs(folder, exist_ok=True)
        filename = f"{doc_type}.md"
        with open(folder / filename, "w", encoding="utf-8") as f:
            f.write(content)
        return str(folder / filename)

class MockDocumentPipeline:
    """模拟文档生成流水线"""
    def __init__(self, prompt_manager, ai_client):
        self.prompt_manager = prompt_manager
        self.ai_client = ai_client
        self.documents = {}
        self.status = {}
    
    def generate_document(self, doc_type, project_info):
        """生成文档"""
        prompt = self.prompt_manager.get_prompt(doc_type)
        content = self.ai_client.generate_document(prompt, "{}")
        self.documents[doc_type] = content
        self.status[doc_type] = "completed"
        return content
    
    def get_all_status(self):
        """获取所有状态"""
        return self.status

class MockDocumentGenerator:
    """
    模拟文档生成器
    用于测试基础文档生成功能
    """
    def __init__(self):
        # 测试组件
        self.config = MockConfig()
        self.prompt_manager = MockPromptManager("tests/test_prompts")
        self.ai_client = MockAIClient(self.config.get_api_key())
        self.file_manager = MockFileManager(self.config.get("paths.output_dir"))
        self.pipeline = MockDocumentPipeline(self.prompt_manager, self.ai_client)
    
    def generate_document(self, project_info, doc_type):
        """生成文档"""
        content = self.pipeline.generate_document(doc_type, project_info)
        self.file_manager.save_document(
            project_info.get("name", "未命名项目"), 
            doc_type, 
            content
        )
        return content
    
    def get_generation_status(self):
        """获取生成状态"""
        return {
            "status": self.pipeline.get_all_status(),
            "timestamp": "2025-04-21T22:22:22"
        }

class TestDocumentGenerator(unittest.TestCase):
    """测试基础文档生成器功能"""
    
    def setUp(self):
        """测试前准备工作"""
        # 创建测试输出目录
        self.test_output_dir = Path("tests/test_output")
        os.makedirs(self.test_output_dir, exist_ok=True)
        
        # 初始化文档生成器
        self.generator = MockDocumentGenerator()
    
    def tearDown(self):
        """测试后清理工作"""
        # 清理生成的文件
        for file in self.test_output_dir.glob("**/*.md"):
            if file.is_file():
                os.remove(file)
    
    def test_generator_initialization(self):
        """测试生成器初始化"""
        self.assertIsNotNone(self.generator)
        self.assertIsNotNone(self.generator.pipeline)
        self.assertIsNotNone(self.generator.ai_client)
        self.assertIsNotNone(self.generator.prompt_manager)
        self.assertIsNotNone(self.generator.file_manager)
    
    def test_document_generation(self):
        """测试文档生成"""
        doc_type = "brainstorm"
        project_info = {
            "name": "测试项目",
            "description": "这是一个测试项目",
            "requirements": ["文档生成", "测试用例"]
        }
        
        # 生成文档
        content = self.generator.generate_document(project_info, doc_type)
        
        # 验证文档内容
        self.assertIsNotNone(content)
        self.assertIn("测试文档", content)
        
        # 验证文件是否已保存
        expected_file = self.test_output_dir / "测试项目" / "current" / f"{doc_type}.md"
        self.assertTrue(expected_file.exists())
    
    def test_generation_status(self):
        """测试生成状态"""
        # 初始状态
        status = self.generator.get_generation_status()
        self.assertIsNotNone(status)
        
        # 生成文档后的状态
        self.generator.generate_document({"name": "状态测试"}, "brainstorm")
        updated_status = self.generator.get_generation_status()
        self.assertEqual(updated_status["status"].get("brainstorm"), "completed")

if __name__ == "__main__":
    unittest.main() 