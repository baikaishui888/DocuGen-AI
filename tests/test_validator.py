"""
测试内容验证器模块
验证文档内容验证功能的正确性
"""

import pytest
import tempfile
import os
from pathlib import Path
import shutil

from docugen.core.validator import ContentValidator


class TestContentValidator:
    """测试内容验证器"""
    
    def setup_method(self):
        """初始化测试环境"""
        self.validator = ContentValidator()
        
        # 创建临时测试目录和文件
        self.test_dir = tempfile.mkdtemp()
        
        # 创建测试文档
        self.test_docs = {
            'prd': self._create_test_prd(),
            'dev_plan': self._create_test_dev_plan(),
            'tech_stack': self._create_test_tech_stack(),
            'backend': self._create_test_backend(),
            'workflow': self._create_test_workflow()
        }
    
    def teardown_method(self):
        """清理测试环境"""
        shutil.rmtree(self.test_dir)
    
    def _create_test_prd(self):
        """创建测试用PRD文档"""
        return """# 产品需求文档

## 需求背景
本项目旨在开发一个文档生成系统。

## 核心功能

- **文档生成模块**: 根据用户输入生成标准化文档
- **内容验证模块**: 确保生成的文档内容符合规范
- **版本控制功能**: 管理文档版本历史

### 具体需求
1. 支持多种文档格式输出
2. 提供模板自定义功能
3. 实现自动内容校验

## 图表说明

![图 1：系统架构图](images/architecture.png)

如图 1所示，系统分为三层架构。

## 参考资料
详见[技术栈文档](tech_stack.md#框架选择)
"""
    
    def _create_test_dev_plan(self):
        """创建测试用开发计划文档"""
        return """# 开发计划

## 开发阶段

1. 基础框架搭建
2. 文档生成模块开发
3. 内容验证模块实现
4. 版本控制功能集成

## 功能实现计划

- 版本控制功能：使用文件系统存储历史版本
- 内容验证模块：实现格式检查和一致性验证

## 开发任务

| 任务 | 负责人 | 时间 |
| 文档生成 | 张三 | 1周 |

"""
    
    def _create_test_tech_stack(self):
        """创建测试用技术栈文档"""
        return """# 技术栈

## 后端技术
- **Python 3.10** - 主要开发语言
- **OpenAI API** - AI内容生成
- `pytest` - 单元测试框架

## 框架选择
- Flask - Web框架（如需构建Web应用）
"""
    
    def _create_test_backend(self):
        """创建测试用后端设计文档"""
        return """# 后端设计

## 整体架构
采用模块化设计，使用Python 3.10实现核心功能。

## 关键模块
- 文档生成器 - 使用OpenAI API实现
- 内容检验器 - 正则表达式实现格式检查

## 单元测试
使用pytest进行测试
"""
    
    def _create_test_workflow(self):
        """创建测试用流程文档"""
        return """# 应用流程

## 文档生成模块
1. 接收用户输入
2. 调用AI生成内容
3. 格式化输出结果

## 内容验证流程
1. 检查文档格式合规性
2. 验证内容一致性
3. 生成检查报告
"""
    
    def test_validate_document_format(self):
        """测试文档格式验证功能"""
        # 测试标题层级跳跃
        content_with_heading_jump = """# 一级标题
### 三级标题（跳过二级）
#### 四级标题
"""
        issues = self.validator.validate_document_format(content_with_heading_jump)
        assert any(issue["type"] == "heading_level_jump" for issue in issues)
        
        # 测试表格格式错误
        content_with_table_error = """# 表格测试
| 列1 | 列2 |
表格内容行缺少分隔符
"""
        issues = self.validator.validate_document_format(content_with_table_error)
        assert any(issue["type"] == "table_format_error" for issue in issues)
        
        # 测试代码块缺少语言标识
        content_with_code_block = """# 代码测试
```
def test():
    pass
```
"""
        issues = self.validator.validate_document_format(content_with_code_block)
        assert any(issue["type"] == "code_block_no_language" for issue in issues)
        
        # 测试格式正确的文档
        valid_content = """# 一级标题
## 二级标题
### 三级标题

这是正确格式的文档。

| 列1 | 列2 |
|-----|-----|
| 内容1 | 内容2 |

```python
def test():
    pass
```
"""
        issues = self.validator.validate_document_format(valid_content)
        assert len(issues) == 0
    
    def test_check_consistency(self):
        """测试文档一致性检查功能"""
        # 测试文档间引用一致性
        docs = {
            'prd': """# 产品需求
## 功能：文档对比
应实现文档版本对比功能
""",
            'dev_plan': """# 开发计划
## 开发任务
实现基础功能，不包含文档对比
"""
        }
        
        issues = self.validator.check_consistency(docs)
        assert any("文档对比" in str(issue) for issue in issues)
        
        # 测试测试文档集的一致性
        issues = self.validator.check_consistency(self.test_docs)
        # PRD和开发计划的任务应大致一致
        assert not any(issue["type"] == "missing_reference" and "版本控制" in issue["element"] for issue in issues)
    
    def test_check_figure_references(self):
        """测试图表引用检查功能"""
        # 测试缺失图表引用
        content_with_missing_figure = """# 图表测试
如图 2所示，这是系统架构。

![图 1：系统流程图](images/flow.png)
"""
        issues = self.validator._check_figure_references(content_with_missing_figure, "test_doc")
        assert any(issue["type"] == "invalid_figure_reference" and "图 2" in issue["reference"] for issue in issues)
        
        # 测试图片格式检查
        content_with_invalid_image = """# 图片格式测试
![图 1：无效格式](images/invalid.txt)
"""
        issues = self.validator._check_figure_references(content_with_invalid_image, "test_doc")
        assert any(issue["type"] == "invalid_image_format" for issue in issues)
        
        # 测试正确的图表引用
        valid_content = """# 图表测试
如图 1所示，这是系统架构。

![图 1：系统架构图](images/architecture.png)
"""
        issues = self.validator._check_figure_references(valid_content, "test_doc")
        assert not any(issue["type"] == "invalid_figure_reference" for issue in issues)
    
    def test_check_link_integrity(self):
        """测试链接完整性检查功能"""
        # 测试无效URL格式
        content_with_invalid_url = """# 链接测试
请参考[官方文档](http://example.com/with spaces)
"""
        issues = self.validator._check_link_integrity(content_with_invalid_url, "test_doc")
        assert any(issue["type"] == "invalid_url_format" for issue in issues)
        
        # 测试原始URL作为链接文本
        content_with_raw_url = """# 链接测试
请参考[http://example.com/api/docs](http://example.com/api/docs)
"""
        issues = self.validator._check_link_integrity(content_with_raw_url, "test_doc")
        assert any(issue["type"] == "raw_url_as_text" for issue in issues)
        
        # 测试无效文件路径
        content_with_invalid_path = """# 链接测试
请参考[文档](file:///C:\\docs|invalid.md)
"""
        issues = self.validator._check_link_integrity(content_with_invalid_path, "test_doc")
        assert any(issue["type"] == "invalid_file_path" for issue in issues)
        
        # 测试有效链接
        valid_content = """# 链接测试
请参考[官方文档](https://example.com/api/docs)
"""
        issues = self.validator._check_link_integrity(valid_content, "test_doc")
        assert not any(issue["type"].startswith("invalid") for issue in issues)
    
    def test_check_all_documents(self):
        """测试全面文档检查功能"""
        # 添加一些格式问题的文档
        problematic_docs = self.test_docs.copy()
        problematic_docs['prd'] += "\n参考[无效链接](http://bad url)"
        problematic_docs['dev_plan'] = """# 开发计划
### 任务列表（跳过二级标题）
| 任务 | 负责人
缺少表格分隔行
"""
        
        results = self.validator.check_all_documents(problematic_docs)
        
        # 验证检查结果分类正确
        assert 'prd' in results  # PRD中有链接问题
        assert 'dev_plan' in results  # 开发计划中有格式问题
        
        # 验证问题分类正确
        prd_issues = results.get('prd', [])
        dev_plan_issues = results.get('dev_plan', [])
        
        assert any(issue["type"] == "invalid_url_format" for issue in prd_issues)
        assert any(issue["type"] == "heading_level_jump" for issue in dev_plan_issues)
        assert any(issue["type"] == "table_format_error" for issue in dev_plan_issues) 