"""
文件管理器测试
测试文件和目录操作功能
"""

import os
import tempfile
import pytest
import shutil
from pathlib import Path
from docugen.utils.file import FileManager


class TestFileManager:
    """文件管理器测试类"""
    
    def setup_method(self):
        """测试前准备工作"""
        # 创建临时输出目录
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # 创建文件管理器
        self.file_manager = FileManager(str(self.output_dir))
        
        # 测试项目名称
        self.project_name = "test_project"
    
    def teardown_method(self):
        """测试后清理工作"""
        self.temp_dir.cleanup()
    
    def test_create_project_dir(self):
        """测试创建项目目录"""
        project_dir = self.file_manager.create_project_dir(self.project_name)
        
        # 验证项目目录结构
        assert project_dir.exists()
        assert project_dir.is_dir()
        assert (project_dir / "current").exists()
        assert (project_dir / "versions").exists()
    
    def test_save_document(self):
        """测试保存文档"""
        doc_type = "prd"
        content = "# 测试文档\n这是一个测试文档内容"
        
        # 保存文档
        file_path = self.file_manager.save_document(self.project_name, doc_type, content)
        
        # 验证文件是否正确保存
        assert file_path.exists()
        assert file_path.is_file()
        
        # 验证文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        assert saved_content == content
    
    def test_get_filename_for_doc_type(self):
        """测试文档类型到文件名的映射"""
        # 测试已知的文档类型
        assert self.file_manager._get_filename_for_doc_type("brainstorm") == "构思梳理.md"
        assert self.file_manager._get_filename_for_doc_type("prd") == "产品需求文档(PRD).md"
        assert self.file_manager._get_filename_for_doc_type("workflow") == "应用流程文档.md"
        
        # 测试未知的文档类型
        assert self.file_manager._get_filename_for_doc_type("unknown") == "unknown.md"
    
    def test_create_version_snapshot(self):
        """测试创建版本快照"""
        # 准备测试文档
        doc_types = ["brainstorm", "prd", "tech_stack"]
        for doc_type in doc_types:
            content = f"# {doc_type}测试文档\n这是{doc_type}的测试内容"
            self.file_manager.save_document(self.project_name, doc_type, content)
        
        # 创建版本快照
        version_id = "20240315_123456"
        version_dir = self.file_manager.create_version_snapshot(self.project_name, version_id)
        
        # 验证版本目录
        assert version_dir is not None
        assert version_dir.exists()
        assert version_dir.is_dir()
        
        # 验证版本中的文件
        for doc_type in doc_types:
            filename = self.file_manager._get_filename_for_doc_type(doc_type)
            assert (version_dir / filename).exists()
    
    def test_list_versions(self):
        """测试列出版本"""
        # 创建多个版本
        version_ids = ["20240315_123456", "20240316_123456", "20240317_123456"]
        
        # 准备测试文档
        doc_type = "prd"
        content = "# 测试文档\n这是一个测试文档内容"
        self.file_manager.save_document(self.project_name, doc_type, content)
        
        # 创建版本快照
        for version_id in version_ids:
            self.file_manager.create_version_snapshot(self.project_name, version_id)
        
        # 列出版本
        versions = self.file_manager.list_versions(self.project_name)
        
        # 验证版本列表
        assert len(versions) == 3
        assert set(versions) == set(version_ids)
    
    def test_load_version(self):
        """测试加载版本"""
        # 准备测试文档
        doc_types = ["brainstorm", "prd"]
        contents = {}
        for doc_type in doc_types:
            content = f"# {doc_type}测试文档\n这是{doc_type}的测试内容"
            contents[doc_type] = content
            self.file_manager.save_document(self.project_name, doc_type, content)
        
        # 创建版本快照
        version_id = "20240315_123456"
        self.file_manager.create_version_snapshot(self.project_name, version_id)
        
        # 加载版本
        loaded_docs = self.file_manager.load_version(self.project_name, version_id)
        
        # 验证加载的文档
        assert len(loaded_docs) == 2
        for doc_type in doc_types:
            assert doc_type in loaded_docs
            assert loaded_docs[doc_type] == contents[doc_type] 