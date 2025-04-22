"""
Markdown导出器测试模块
"""

import os
import unittest
import tempfile
from pathlib import Path

from docugen.core.exporter import MarkdownExporter, DocumentExporter


class TestMarkdownExporter(unittest.TestCase):
    """测试Markdown导出器功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.exporter = MarkdownExporter()
        self.doc_exporter = DocumentExporter()
        
        # 测试用Markdown内容
        self.test_content = """#标题一
##标题二
- 无空格列表项
*无空格列表项
1.无空格有序列表

###标题三
```python
def test():
    pass
```
"""
        
        # 创建临时目录用于测试文件输出
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试过程中创建的临时文件
        for f in Path(self.temp_dir).glob("*.md"):
            try:
                f.unlink()
            except:
                pass
    
    def test_normalize_content(self):
        """测试Markdown内容标准化"""
        normalized = self.exporter._normalize_content(self.test_content)
        
        # 验证标题格式化是否正确
        self.assertIn("# 标题一", normalized)
        self.assertIn("## 标题二", normalized)
        self.assertIn("### 标题三", normalized)
        
        # 验证列表格式化是否正确
        self.assertIn("- 无空格列表项", normalized)
        self.assertIn("* 无空格列表项", normalized)
        self.assertIn("1. 无空格有序列表", normalized)
    
    def test_add_metadata(self):
        """测试添加元数据"""
        metadata = {
            "title": "测试文档",
            "author": "DocuGen AI",
            "date": "2025-04-21",
            "tags": ["测试", "Markdown", "导出器"],
            "version": {
                "major": 1,
                "minor": 0
            }
        }
        
        content = "# 测试内容"
        result = self.exporter._add_metadata(content, metadata)
        
        # 验证元数据是否正确添加
        self.assertIn("---", result)
        self.assertIn("title: 测试文档", result)
        self.assertIn("author: DocuGen AI", result)
        self.assertIn("tags:", result)
        self.assertIn("  - 测试", result)
        self.assertIn("version:", result)
        self.assertIn("  major: 1", result)
    
    def test_format(self):
        """测试格式化功能"""
        metadata = {"title": "测试格式化"}
        formatted = self.exporter.format(self.test_content, metadata)
        
        # 验证基本格式是否正确
        self.assertIn("title: 测试格式化", formatted)
        self.assertIn("# 标题一", formatted)
        self.assertIn("- 无空格列表项", formatted)
    
    def test_export(self):
        """测试导出功能"""
        output_path = os.path.join(self.temp_dir, "test_output.md")
        result_path = self.exporter.export(self.test_content, output_path)
        
        # 验证文件是否成功创建
        self.assertTrue(os.path.exists(result_path))
        
        # 验证文件内容是否正确
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("# 标题一", content)
        self.assertIn("## 标题二", content)
    
    def test_document_exporter(self):
        """测试文档导出器封装类"""
        output_path = os.path.join(self.temp_dir, "doc_exporter_test.md")
        metadata = {"title": "文档导出器测试"}
        
        # 测试格式化功能
        formatted = self.doc_exporter.format_markdown(self.test_content, metadata)
        self.assertIn("title: 文档导出器测试", formatted)
        
        # 测试导出功能
        result_path = self.doc_exporter.export_markdown(self.test_content, output_path, metadata)
        self.assertTrue(os.path.exists(result_path))


if __name__ == "__main__":
    unittest.main() 