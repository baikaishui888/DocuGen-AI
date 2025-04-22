"""
版本管理器测试模块
"""

import os
import json
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from docugen.utils.file import FileManager
from docugen.core.version import VersionManager


class TestVersionManager(unittest.TestCase):
    """测试版本管理器功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录作为测试输出目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 初始化文件管理器和版本管理器
        self.file_manager = FileManager(self.temp_dir)
        self.version_manager = VersionManager(self.file_manager)
        
        # 测试项目名称
        self.project_name = "测试项目"
        self.version_manager.set_project(self.project_name)
        
        # 测试文档
        self.test_docs = {
            "prd": "# 产品需求文档\n\n这是一个测试PRD文档。",
            "backend": "# 后端架构设计\n\n这是一个测试的后端架构文档。",
            "frontend": "# 前端设计指南\n\n这是一个测试的前端设计文档。"
        }
        
        # 添加测试文档
        for doc_type, content in self.test_docs.items():
            self.version_manager.add_document(doc_type, content)
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_set_project(self):
        """测试设置项目"""
        # 重新设置项目名称
        new_project_name = "新测试项目"
        self.version_manager.set_project(new_project_name)
        
        # 验证项目名称是否正确设置
        self.assertEqual(self.version_manager.project_name, new_project_name)
    
    def test_add_document(self):
        """测试添加文档"""
        # 添加一个新文档
        doc_type = "workflow"
        content = "# 应用流程文档\n\n这是一个测试的流程文档。"
        self.version_manager.add_document(doc_type, content)
        
        # 验证文档是否正确添加到当前文档中
        self.assertIn(doc_type, self.version_manager.current_docs)
        self.assertEqual(self.version_manager.current_docs[doc_type], content)
    
    def test_create_checkpoint(self):
        """测试创建版本快照"""
        # 创建版本快照
        version_id = self.version_manager.create_checkpoint()
        
        # 验证版本ID是否有效
        self.assertTrue(version_id)
        
        # 验证版本目录是否创建
        version_dir = Path(self.temp_dir) / self.project_name / "versions" / version_id
        self.assertTrue(version_dir.exists())
        self.assertTrue(version_dir.is_dir())
        
        # 验证版本目录中是否包含所有文档
        doc_files = list(version_dir.glob("*.md"))
        self.assertEqual(len(doc_files), len(self.test_docs))
        
        # 验证元数据文件是否创建
        metadata_file = version_dir / "metadata.json"
        self.assertTrue(metadata_file.exists())
        
        # 验证元数据内容
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        self.assertEqual(metadata["version_id"], version_id)
        self.assertEqual(metadata["project_name"], self.project_name)
        self.assertEqual(set(metadata["doc_types"]), set(self.test_docs.keys()))
    
    def test_list_versions(self):
        """测试列出版本"""
        # 创建多个版本
        version_ids = []
        for i in range(3):
            # 对文档做一些修改
            self.version_manager.add_document("prd", f"# 产品需求文档\n\n这是第{i+1}个版本的PRD文档。")
            version_id = self.version_manager.create_checkpoint()
            version_ids.append(version_id)
        
        # 列出版本
        versions = self.version_manager.list_versions()
        
        # 验证版本列表
        self.assertEqual(len(versions), len(version_ids))
        for version in versions:
            self.assertIn(version["version_id"], version_ids)
    
    def test_load_version(self):
        """测试加载版本"""
        # 创建版本
        version_id = self.version_manager.create_checkpoint()
        
        # 修改当前文档
        modified_content = "# 修改后的PRD\n\n这是修改后的PRD文档。"
        self.version_manager.add_document("prd", modified_content)
        
        # 加载之前的版本
        loaded_docs = self.version_manager.load_version(version_id)
        
        # 验证加载的文档内容是否正确
        self.assertEqual(loaded_docs["prd"], self.test_docs["prd"])
        
        # 验证当前文档是否已更新为加载的版本
        self.assertEqual(self.version_manager.current_docs["prd"], self.test_docs["prd"])
    
    def test_compare_versions(self):
        """测试比较版本"""
        # 创建第一个版本
        version_id1 = self.version_manager.create_checkpoint()
        
        # 修改文档并创建第二个版本
        self.version_manager.add_document("prd", "# 产品需求文档 V2\n\n这是修改后的PRD文档。\n新增一行内容。")
        # 添加新文档
        self.version_manager.add_document("dev_plan", "# 项目开发计划\n\n这是一个测试的开发计划。")
        version_id2 = self.version_manager.create_checkpoint()
        
        # 比较两个版本
        comparison = self.version_manager.compare_versions(version_id1, version_id2)
        
        # 验证比较结果
        self.assertIn("prd", comparison)
        self.assertTrue(comparison["prd"]["exists_in_both"])
        self.assertTrue(comparison["prd"]["line_diff"] > 0)  # 行数增加
        
        self.assertIn("dev_plan", comparison)
        self.assertFalse(comparison["dev_plan"]["exists_in_both"])  # 仅在第二个版本中存在
    
    def test_create_version_with_label(self):
        """测试创建带标签的版本"""
        # 创建带标签的版本
        label = "初始版本"
        comments = "这是项目的初始版本"
        version_id = self.version_manager.create_checkpoint(label=label, comments=comments)
        
        # 验证版本元数据中是否包含标签和备注
        versions = self.version_manager.list_versions()
        version_info = next((v for v in versions if v["version_id"] == version_id), None)
        
        self.assertIsNotNone(version_info)
        self.assertEqual(version_info["label"], label)
        self.assertEqual(version_info["comments"], comments)
    
    def test_revert_to_version(self):
        """测试回滚到指定版本"""
        # 创建初始版本
        initial_version_id = self.version_manager.create_checkpoint()
        
        # 修改并创建新版本
        self.version_manager.add_document("prd", "# 修改后的PRD\n\n这是修改后的PRD文档。")
        new_version_id = self.version_manager.create_checkpoint()
        
        # 回滚到初始版本
        result = self.version_manager.revert_to_version(initial_version_id)
        self.assertTrue(result)
        
        # 验证当前文档是否回滚成功
        self.assertEqual(self.version_manager.current_docs["prd"], self.test_docs["prd"])
        
        # 验证在回滚后创建的快照是否反映了回滚的内容
        revert_version_id = self.version_manager.create_checkpoint(label="回滚版本")
        loaded_docs = self.version_manager.load_version(revert_version_id)
        self.assertEqual(loaded_docs["prd"], self.test_docs["prd"])
    
    def test_generate_version_report(self):
        """测试生成版本历史报告"""
        # 创建多个版本
        version_ids = []
        labels = ["初始版本", "功能增强", "Bug修复"]
        
        for i in range(3):
            # 对文档做一些修改
            self.version_manager.add_document("prd", f"# 产品需求文档\n\n这是第{i+1}个版本的PRD文档。")
            version_id = self.version_manager.create_checkpoint(label=labels[i])
            version_ids.append(version_id)
        
        # 生成版本报告
        report = self.version_manager.generate_version_report()
        
        # 验证报告内容
        self.assertIsInstance(report, str)
        for label in labels:
            self.assertIn(label, report)


if __name__ == "__main__":
    unittest.main() 