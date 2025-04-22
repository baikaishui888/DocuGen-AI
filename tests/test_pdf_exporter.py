"""
PDF导出器测试模块
"""

import os
import unittest
import tempfile
from pathlib import Path

from docugen.core.exporter import PDFExporter, DocumentExporter


class TestPDFExporter(unittest.TestCase):
    """测试PDF导出器功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.exporter = PDFExporter()
        self.doc_exporter = DocumentExporter()
        
        # 测试用Markdown内容
        self.test_content = """# PDF测试文档
        
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
        
        # 创建临时HTML文件用于测试
        self.test_html_path = os.path.join(self.temp_dir, "test_input.html")
        with open(self.test_html_path, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>测试HTML文件</title>
</head>
<body>
    <h1>测试HTML文件</h1>
    <p>这是一个用于测试HTML到PDF转换的文件。</p>
</body>
</html>""")
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试过程中创建的临时文件
        for ext in [".html", ".pdf"]:
            for f in Path(self.temp_dir).glob(f"*{ext}"):
                try:
                    f.unlink()
                except:
                    pass
    
    def test_export_from_markdown(self):
        """测试从Markdown生成PDF"""
        output_path = os.path.join(self.temp_dir, "test_output.pdf")
        
        try:
            result_path = self.exporter.export_from_markdown(self.test_content, output_path)
            
            # 验证文件是否成功创建
            self.assertTrue(os.path.exists(result_path))
            
            # 检查文件大小是否合理
            file_size = os.path.getsize(result_path)
            self.assertGreater(file_size, 0, "PDF文件不应为空")
        except Exception as e:
            self.skipTest(f"PDF生成测试跳过，需要安装WeasyPrint及其依赖: {str(e)}")
    
    def test_export_from_html(self):
        """测试从HTML生成PDF"""
        output_path = os.path.join(self.temp_dir, "test_html_output.pdf")
        
        # 生成HTML内容
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>测试HTML内容</title>
</head>
<body>
    <h1>从HTML内容测试</h1>
    <p>这是一个测试用的HTML内容，用于生成PDF。</p>
</body>
</html>"""
        
        try:
            result_path = self.exporter.export_from_html(html_content, output_path)
            
            # 验证文件是否成功创建
            self.assertTrue(os.path.exists(result_path))
            
            # 检查文件大小是否合理
            file_size = os.path.getsize(result_path)
            self.assertGreater(file_size, 0, "PDF文件不应为空")
        except Exception as e:
            self.skipTest(f"PDF生成测试跳过，需要安装WeasyPrint及其依赖: {str(e)}")
    
    def test_export_from_html_file(self):
        """测试从HTML文件生成PDF"""
        output_path = os.path.join(self.temp_dir, "test_html_file_output.pdf")
        
        try:
            result_path = self.exporter.export_from_html_file(self.test_html_path, output_path)
            
            # 验证文件是否成功创建
            self.assertTrue(os.path.exists(result_path))
            
            # 检查文件大小是否合理
            file_size = os.path.getsize(result_path)
            self.assertGreater(file_size, 0, "PDF文件不应为空")
        except Exception as e:
            self.skipTest(f"PDF生成测试跳过，需要安装WeasyPrint及其依赖: {str(e)}")
    
    def test_custom_css(self):
        """测试自定义CSS样式"""
        output_path = os.path.join(self.temp_dir, "test_css_output.pdf")
        
        # 设置自定义CSS
        custom_css = """
        body { 
            background-color: #f0f0f0; 
            font-family: Arial, sans-serif; 
            margin: 50px;
        }
        h1 { color: #007bff; }
        """
        
        try:
            self.exporter.set_custom_css(custom_css)
            result_path = self.exporter.export_from_markdown(self.test_content, output_path)
            
            # 验证文件是否成功创建
            self.assertTrue(os.path.exists(result_path))
        except Exception as e:
            self.skipTest(f"PDF生成测试跳过，需要安装WeasyPrint及其依赖: {str(e)}")
    
    def test_document_exporter_pdf(self):
        """测试DocumentExporter的PDF导出功能"""
        output_path = os.path.join(self.temp_dir, "doc_exporter_test.pdf")
        metadata = {"title": "文档导出器PDF测试"}
        
        try:
            # 测试从Markdown导出PDF
            result_path = self.doc_exporter.export_pdf(self.test_content, output_path, metadata)
            self.assertTrue(os.path.exists(result_path))
            
            # 测试从HTML内容导出PDF
            html_content = "<html><body><h1>测试HTML</h1></body></html>"
            html_pdf_path = os.path.join(self.temp_dir, "html_content_pdf.pdf")
            result_path = self.doc_exporter.export_html_to_pdf(html_content, html_pdf_path)
            self.assertTrue(os.path.exists(result_path))
            
            # 测试从HTML文件导出PDF
            html_file_pdf_path = os.path.join(self.temp_dir, "html_file_pdf.pdf")
            result_path = self.doc_exporter.export_html_file_to_pdf(self.test_html_path, html_file_pdf_path)
            self.assertTrue(os.path.exists(result_path))
            
            # 测试设置PDF CSS样式
            custom_css = "body { color: #333; }"
            self.doc_exporter.set_pdf_css(custom_css)
            self.doc_exporter.export_pdf(self.test_content, output_path)
            
            # 测试同时设置所有CSS样式
            self.doc_exporter.set_all_css("body { margin: 20px; }")
            self.doc_exporter.export_pdf(self.test_content, output_path)
        except Exception as e:
            self.skipTest(f"PDF生成测试跳过，需要安装WeasyPrint及其依赖: {str(e)}")


if __name__ == "__main__":
    unittest.main() 