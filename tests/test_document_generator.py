import unittest
import os
import shutil
from pathlib import Path
import sys
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from docugen.core.generator import DocumentGenerator
from docugen.utils.file import FileManager
from docugen.config import Config
from tests.test_config import init_test_env, TEST_OUTPUT_DIR

class TestDocumentGenerator(unittest.TestCase):
    """测试基础文档生成器功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 初始化测试环境
        cls.config_path = init_test_env()
        # 设置日志
        cls.logger = logging.getLogger("tests.document_generator")
    
    def setUp(self):
        """测试前准备工作"""
        # 确保目录存在
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        
        # 加载配置
        self.config = Config(str(self.config_path))
        
        # 初始化文档生成器
        self.generator = DocumentGenerator()
        
        # 初始化文档集合（预先添加requirement_confirm文档）
        self.generator.pipeline.ai_client.initialize_documents()
        # 复制文档到pipeline的documents中
        if not hasattr(self.generator.pipeline, 'documents'):
            self.generator.pipeline.documents = {}
        self.generator.pipeline.documents['requirement_confirm'] = self.generator.pipeline.ai_client.documents['requirement_confirm']
    
    def tearDown(self):
        """测试后清理工作"""
        # 清理生成的文件（保留目录结构）
        for file in TEST_OUTPUT_DIR.glob("*.md"):
            if file.is_file():
                file.unlink()
    
    def test_generator_initialization(self):
        """测试生成器初始化"""
        self.assertIsNotNone(self.generator)
        self.assertIsNotNone(self.generator.pipeline)
        self.assertIsNotNone(self.generator.ai_client)
        self.assertIsNotNone(self.generator.prompt_manager)
        self.assertIsNotNone(self.generator.file_manager)
    
    def test_document_generation(self):
        """测试简单文档生成"""
        doc_type = "brainstorm"  # 构思梳理
        project_info = {
            "name": "测试项目",
            "description": "这是一个测试项目",
            "requirements": ["文档生成", "测试用例"]
        }
        
        # 生成测试文档
        content = self.generator.generate_document(project_info, doc_type)
        
        # 验证结果
        self.assertIsNotNone(content)
        self.assertIn("构思梳理", content)
        self.assertIn("测试项目", content)
        
        # 检查generator使用的输出目录
        output_dir = self.generator.file_manager.output_dir
        self.logger.info(f"文档输出目录: {output_dir}")
        
        # 验证文件是否已保存
        project_name = project_info["name"]
        
        # 检查项目子目录下的文件 (测试目录)
        test_project_dir = TEST_OUTPUT_DIR / project_name / "current"
        test_doc_files = list(test_project_dir.glob("*.md"))
        
        # 检查实际输出目录下的文件
        actual_project_dir = Path(output_dir) / project_name / "current"
        actual_doc_files = list(actual_project_dir.glob("*.md"))
        
        # 检查两个位置的文件，只要有一个位置有文件就通过测试
        self.assertTrue(
            len(test_doc_files) > 0 or len(actual_doc_files) > 0, 
            f"在目录 {test_project_dir} 或 {actual_project_dir} 中未找到生成的文档文件"
        )
    
    def test_document_pipeline(self):
        """测试文档生成管道"""
        project_info = {
            "name": "管道测试项目",
            "description": "测试文档生成流水线",
            "requirements": ["构思梳理", "需求文档", "流程文档"]
        }
        
        # 生成多个文档，按照依赖顺序生成
        content1 = self.generator.generate_document(project_info, "brainstorm")
        content2 = self.generator.generate_document(project_info, "prd")
        
        # 验证结果
        self.assertIsNotNone(content1)
        self.assertIsNotNone(content2)
        self.assertIn("核心功能", content1)
        self.assertIn("功能需求", content2)
    
    def test_pipeline_status(self):
        """测试文档生成状态管理"""
        # 获取初始状态
        initial_status = self.generator.get_generation_status()
        self.assertIn("status", initial_status)
        
        # 生成一个文档
        project_info = {
            "name": "状态测试项目",
            "description": "测试状态管理"
        }
        self.generator.generate_document(project_info, "brainstorm")
        
        # 检查状态更新
        updated_status = self.generator.get_generation_status()
        self.assertEqual(updated_status["status"]["brainstorm"], "completed")

if __name__ == "__main__":
    unittest.main() 