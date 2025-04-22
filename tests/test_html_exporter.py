"""
HTML导出器测试模块
"""

import os
import unittest
import tempfile
from pathlib import Path

from docugen.core.exporter import HTMLExporter, DocumentExporter


class TestHTMLExporter(unittest.TestCase):
    """测试HTML导出器功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.exporter = HTMLExporter()
        self.doc_exporter = DocumentExporter()
        
        # 测试用Markdown内容
        self.test_content = """# 测试标题
        
## 次级标题

这是一段普通文本，包含**加粗**和*斜体*。

- 列表项1
- 列表项2
  - 子列表项

1. 有序列表项1
2. 有序列表项2

```python
def hello_world():
    print("Hello, World!")
```

> 这是一段引用文本

| 表头1 | 表头2 |
|-------|-------|
| 单元格1 | 单元格2 |
| 单元格3 | 单元格4 |
"""
        
        # 创建临时目录用于测试文件输出
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试过程中创建的临时文件
        for f in Path(self.temp_dir).glob("*.html"):
            try:
                f.unlink()
            except:
                pass
    
    def test_convert(self):
        """测试Markdown到HTML的转换"""
        html = self.exporter.convert(self.test_content)
        
        # 验证HTML基本结构
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html lang=\"zh-CN\">", html)
        self.assertIn("</html>", html)
        
        # 验证内容转换是否正确
        self.assertIn("<h1>测试标题</h1>", html)
        self.assertIn("<h2>次级标题</h2>", html)
        self.assertIn("<strong>加粗</strong>", html)
        self.assertIn("<em>斜体</em>", html)
        self.assertIn("<li>列表项1</li>", html)
        self.assertIn("<ol>", html)  # 有序列表
        self.assertIn("<pre>", html)  # 代码块
        self.assertIn("<blockquote>", html)  # 引用
        self.assertIn("<table>", html)  # 表格
    
    def test_convert_with_metadata(self):
        """测试带元数据的Markdown到HTML转换"""
        metadata = {
            "title": "HTML测试文档",
            "author": "DocuGen测试",
            "keywords": "测试,HTML,导出"
        }
        
        html = self.exporter.convert(self.test_content, metadata)
        
        # 验证元数据是否正确添加
        self.assertIn("<title>HTML测试文档</title>", html)
        self.assertIn("<meta name=\"author\" content=\"DocuGen测试\">", html)
        self.assertIn("<meta name=\"keywords\" content=\"测试,HTML,导出\">", html)
    
    def test_export(self):
        """测试HTML导出功能"""
        output_path = os.path.join(self.temp_dir, "test_output.html")
        result_path = self.exporter.export(self.test_content, output_path)
        
        # 验证文件是否成功创建
        self.assertTrue(os.path.exists(result_path))
        
        # 验证文件内容是否正确
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("<h1>测试标题</h1>", content)
    
    def test_custom_css(self):
        """测试自定义CSS功能"""
        custom_css = """
        body { 
            background-color: #f0f0f0; 
            font-family: Arial, sans-serif; 
        }
        h1 { color: #007bff; }
        """
        
        self.exporter.set_custom_css(custom_css)
        html = self.exporter.convert(self.test_content)
        
        # 验证自定义CSS是否应用
        self.assertIn("background-color: #f0f0f0;", html)
        self.assertIn("font-family: Arial, sans-serif;", html)
        self.assertIn("color: #007bff;", html)
    
    def test_document_exporter_html(self):
        """测试DocumentExporter的HTML导出功能"""
        output_path = os.path.join(self.temp_dir, "doc_exporter_test.html")
        metadata = {"title": "文档导出器HTML测试"}
        
        # 测试HTML转换功能
        html = self.doc_exporter.convert_to_html(self.test_content, metadata)
        self.assertIn("<title>文档导出器HTML测试</title>", html)
        self.assertIn("<h1>测试标题</h1>", html)
        
        # 测试HTML导出功能
        result_path = self.doc_exporter.export_html(self.test_content, output_path, metadata)
        self.assertTrue(os.path.exists(result_path))
        
        # 测试设置CSS功能
        custom_css = "body { color: #333; }"
        self.doc_exporter.set_html_css(custom_css)
        html = self.doc_exporter.convert_to_html(self.test_content)
        self.assertIn("body { color: #333; }", html)


if __name__ == "__main__":
    unittest.main() 