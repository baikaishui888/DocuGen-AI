"""
测试文档分析器的功能，包括文档结构分析、目录生成和索引生成

本测试模块验证DocumentAnalyzer类的所有功能，确保其能正确分析Markdown文档结构，
提取标题层级、关键概念、链接等元素，并生成目录和索引
"""

import re
import pytest
from docugen.utils.analyzer import DocumentAnalyzer

# 测试用Markdown文档
TEST_DOCUMENT = """# 测试文档标题

这是一个用于测试的Markdown文档，包含多种文档元素。

## 第一章 {#chapter-1}

这里是**第一个重要概念**的介绍。*斜体文本*表示次要概念。

### 1.1 小节标题

这里有一个[外部链接](https://example.com)和一个[内部链接](#chapter-1)。

## 第二章

这里是**另一个重要概念**和**第一个重要概念**的再次出现。

这里有一个图片：

![示例图片](images/example.png)

### 2.1 代码示例

下面是一段代码:

```python
def hello_world():
    print("Hello, World!")
```

### 2.2 表格示例

下面是一个表格:

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |
| 数据4 | 数据5 | 数据6 |

## 第三章

这章没有太多内容。
"""

class TestDocumentAnalyzer:
    """文档分析器测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.analyzer = DocumentAnalyzer()
        self.analysis_result = self.analyzer.analyze_document(TEST_DOCUMENT)
    
    def test_title_extraction(self):
        """测试标题提取功能"""
        title = self.analyzer._extract_title(TEST_DOCUMENT)
        assert title == "测试文档标题"
        assert self.analysis_result["title"] == "测试文档标题"
    
    def test_headings_extraction(self):
        """测试标题层级提取功能"""
        headings = self.analyzer._extract_headings(TEST_DOCUMENT)
        
        # 检查提取的标题数量
        assert len(headings) == 6
        
        # 检查标题层级是否正确
        assert headings[0]["level"] == 1
        assert headings[0]["text"] == "测试文档标题"
        
        assert headings[1]["level"] == 2
        assert headings[1]["text"] == "第一章"
        assert headings[1]["id"] == "chapter-1"  # 自定义ID
        
        assert headings[2]["level"] == 3
        assert headings[2]["text"] == "1.1 小节标题"
        
        # 验证分析结果中的标题
        assert len(self.analysis_result["headings"]) == 6
    
    def test_key_concepts_extraction(self):
        """测试关键概念提取"""
        key_concepts = self.analyzer._extract_key_concepts(TEST_DOCUMENT)
        
        # 检查是否提取了所有加粗和斜体文本
        assert "第一个重要概念" in key_concepts
        assert "另一个重要概念" in key_concepts
        assert "斜体文本" in key_concepts
        
        # 检查出现次数统计
        assert key_concepts["第一个重要概念"] == 2  # 出现两次
        assert key_concepts["另一个重要概念"] == 1
        
        # 验证分析结果中的关键概念
        concepts_in_result = self.analysis_result["key_concepts"]
        assert len(concepts_in_result) >= 3
    
    def test_links_extraction(self):
        """测试链接提取"""
        links = self.analyzer._extract_links(TEST_DOCUMENT)
        
        # 检查提取的链接数量
        assert len(links) == 2
        
        # 检查外部链接
        external_link = next(link for link in links if link["is_external"])
        assert external_link["text"] == "外部链接"
        assert external_link["url"] == "https://example.com"
        
        # 检查内部链接
        internal_link = next(link for link in links if not link["is_external"])
        assert internal_link["text"] == "内部链接"
        assert internal_link["url"] == "#chapter-1"
        
        # 验证分析结果中的链接
        assert len(self.analysis_result["links"]) == 2
    
    def test_images_extraction(self):
        """测试图片提取"""
        images = self.analyzer._extract_images(TEST_DOCUMENT)
        
        # 检查提取的图片数量
        assert len(images) == 1
        
        # 检查图片信息
        assert images[0]["alt_text"] == "示例图片"
        assert images[0]["url"] == "images/example.png"
        
        # 验证分析结果中的图片
        assert len(self.analysis_result["images"]) == 1
    
    def test_tables_extraction(self):
        """测试表格提取"""
        tables = self.analyzer._extract_tables(TEST_DOCUMENT)
        
        # 检查提取的表格数量
        assert len(tables) == 1
        
        # 检查表格头
        assert "列1" in tables[0]["headers"]
        assert "列2" in tables[0]["headers"]
        assert "列3" in tables[0]["headers"]
        
        # 检查表格数据行
        assert len(tables[0]["rows"]) == 2
        assert "数据1" in tables[0]["rows"][0]
        assert "数据6" in tables[0]["rows"][1]
        
        # 验证分析结果中的表格
        assert len(self.analysis_result["tables"]) == 1
    
    def test_code_blocks_extraction(self):
        """测试代码块提取"""
        code_blocks = self.analyzer._extract_code_blocks(TEST_DOCUMENT)
        
        # 检查提取的代码块数量
        assert len(code_blocks) == 1
        
        # 检查代码块语言和内容
        assert code_blocks[0]["language"] == "python"
        assert "def hello_world()" in code_blocks[0]["code"]
        assert 'print("Hello, World!")' in code_blocks[0]["code"]
        
        # 验证分析结果中的代码块
        assert len(self.analysis_result["code_blocks"]) == 1
    
    def test_word_count(self):
        """测试单词计数功能"""
        count = self.analyzer._count_words(TEST_DOCUMENT)
        
        # 单词数应该大于0
        assert count > 0
        assert self.analysis_result["word_count"] > 0
    
    def test_generate_toc(self):
        """测试目录生成功能"""
        headings = self.analyzer._extract_headings(TEST_DOCUMENT)
        toc = self.analyzer.generate_toc(headings)
        
        # 检查目录格式
        assert "- [第一章](#chapter-1)" in toc
        assert "  - [1.1 小节标题]" in toc
        assert "- [第二章]" in toc
        assert "  - [2.1 代码示例]" in toc
        assert "  - [2.2 表格示例]" in toc
        assert "- [第三章]" in toc
        
        # 检查目录不包含文档标题
        assert "- [测试文档标题]" not in toc
    
    def test_generate_index(self):
        """测试索引生成功能"""
        key_concepts = self.analyzer._extract_key_concepts(TEST_DOCUMENT)
        index = self.analyzer.generate_index(key_concepts, TEST_DOCUMENT)
        
        # 检查索引项
        assert "**第一个重要概念** (2次):" in index
        assert "**另一个重要概念** (1次):" in index
        assert "**斜体文本** (1次):" in index
        
        # 检查包含章节引用
        assert "[第一章](#chapter-1)" in index
        assert "[第二章]" in index
    
    def test_add_toc_to_document(self):
        """测试向文档添加目录"""
        enhanced = self.analyzer.add_toc_to_document(TEST_DOCUMENT)
        
        # 检查是否添加了目录标题
        assert "## 目录\n\n" in enhanced
        
        # 检查目录是否添加在文档标题之后
        title_pos = enhanced.find("# 测试文档标题")
        toc_pos = enhanced.find("## 目录")
        assert title_pos < toc_pos
    
    def test_add_index_to_document(self):
        """测试向文档添加索引"""
        enhanced = self.analyzer.add_index_to_document(TEST_DOCUMENT)
        
        # 检查是否添加了索引标题
        assert "## 索引\n\n" in enhanced
        
        # 检查索引是否添加在文档末尾
        index_pos = enhanced.find("## 索引")
        assert index_pos > enhanced.find("## 第三章")
    
    def test_enhance_document(self):
        """测试文档增强功能（添加目录和索引）"""
        enhanced = self.analyzer.enhance_document(TEST_DOCUMENT)
        
        # 检查是否同时包含目录和索引
        assert "## 目录\n\n" in enhanced
        assert "## 索引\n\n" in enhanced
        
        # 检查目录在索引之前
        toc_pos = enhanced.find("## 目录")
        index_pos = enhanced.find("## 索引")
        assert toc_pos < index_pos 