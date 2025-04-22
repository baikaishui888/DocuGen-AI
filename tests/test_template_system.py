"""
模板系统测试模块
测试模板管理器和文档渲染器功能
"""

import os
import pytest
import tempfile
from pathlib import Path

from docugen.utils.template import TemplateManager
from docugen.core.renderer import DocumentRenderer


class TestTemplateManager:
    """测试模板管理器功能"""
    
    @pytest.fixture
    def setup_templates_dir(self):
        """创建临时模板目录并添加测试模板"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一个测试模板文件
            template_path = Path(temp_dir) / "test_template.j2"
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write("# {{ title }}\n\n{{ content }}\n\n作者: {{ author }}")
            
            # 创建对应的元数据文件
            metadata_path = template_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write("""{
                    "name": "test_template.j2",
                    "description": "用于测试的模板",
                    "version": "1.0.0",
                    "required_variables": ["title", "content"],
                    "optional_variables": ["author"]
                }""")
                
            yield temp_dir
    
    def test_template_loading(self, setup_templates_dir):
        """测试模板加载功能"""
        template_manager = TemplateManager(setup_templates_dir)
        
        # 测试模板是否被正确加载
        assert "test_template.j2" in template_manager.template_metadata
        
        # 测试元数据是否正确
        metadata = template_manager.get_template_metadata("test_template.j2")
        assert metadata["name"] == "test_template.j2"
        assert metadata["description"] == "用于测试的模板"
        assert "title" in metadata["required_variables"]
        assert "author" in metadata["optional_variables"]
    
    def test_template_rendering(self, setup_templates_dir):
        """测试模板渲染功能"""
        template_manager = TemplateManager(setup_templates_dir)
        
        # 渲染模板
        result = template_manager.render_template("test_template.j2", {
            "title": "测试标题",
            "content": "这是测试内容",
            "author": "测试作者"
        })
        
        # 验证渲染结果
        assert "# 测试标题" in result
        assert "这是测试内容" in result
        assert "作者: 测试作者" in result
    
    def test_missing_required_variables(self, setup_templates_dir):
        """测试缺少必要变量的情况"""
        template_manager = TemplateManager(setup_templates_dir)
        
        # 没有提供必要变量title，应该抛出异常
        with pytest.raises(ValueError) as exc_info:
            template_manager.render_template("test_template.j2", {
                "content": "这是测试内容"
            })
        
        assert "缺少必要变量" in str(exc_info.value)
    
    def test_create_template(self, setup_templates_dir):
        """测试创建模板功能"""
        template_manager = TemplateManager(setup_templates_dir)
        
        # 创建新模板
        template_content = "# {{ title }}\n\n{{ content }}\n\n版本: {{ version }}"
        metadata = {
            "description": "新创建的测试模板",
            "required_variables": ["title", "content"],
            "optional_variables": ["version"]
        }
        
        template_manager.create_template("new_template.j2", template_content, metadata)
        
        # 验证模板是否创建成功
        assert "new_template.j2" in template_manager.template_metadata
        assert template_manager.template_metadata["new_template.j2"]["description"] == "新创建的测试模板"
        
        # 测试渲染新模板
        result = template_manager.render_template("new_template.j2", {
            "title": "新模板测试",
            "content": "这是新模板的内容",
            "version": "1.0.0"
        })
        
        assert "# 新模板测试" in result
        assert "这是新模板的内容" in result
        assert "版本: 1.0.0" in result


class TestDocumentRenderer:
    """测试文档渲染器功能"""
    
    @pytest.fixture
    def setup_renderer(self):
        """创建临时模板目录并初始化渲染器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一个测试模板文件
            template_path = Path(temp_dir) / "doc_template.j2"
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write("""# {{ title | default('默认标题') }}

{{ content }}

{% if items is defined %}
## 项目列表

{% for item in items %}
- {{ item.name }}: {{ item.description }}
{% endfor %}
{% endif %}

文档创建时间: {{ creation_date | default('N/A') | format_date }}
""")
            
            # 创建对应的元数据文件
            metadata_path = template_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write("""{
                    "name": "doc_template.j2",
                    "description": "文档测试模板",
                    "version": "1.0.0",
                    "required_variables": ["content"],
                    "optional_variables": ["title", "items", "creation_date"]
                }""")
                
            # 初始化渲染器
            renderer = DocumentRenderer(temp_dir)
            yield renderer
    
    def test_render_document(self, setup_renderer):
        """测试渲染文档功能"""
        renderer = setup_renderer
        
        # 创建上下文
        context = {
            "title": "测试文档",
            "content": "这是文档内容",
            "creation_date": "2025-04-20T12:00:00"
        }
        
        # 渲染文档
        result = renderer.render_document("doc_template.j2", context)
        
        # 验证结果
        assert "# 测试文档" in result
        assert "这是文档内容" in result
        assert "文档创建时间: 2025-04-20" in result
    
    def test_default_values(self, setup_renderer):
        """测试默认值功能"""
        renderer = setup_renderer
        
        # 只提供必要的content
        result = renderer.render_document("doc_template.j2", {"content": "只有内容"})
        
        # 验证结果使用了默认值
        assert "# 默认标题" in result
        assert "只有内容" in result
        assert "文档创建时间: N/A" in result
    
    def test_complex_context(self, setup_renderer):
        """测试复杂上下文渲染"""
        renderer = setup_renderer
        
        # 创建包含列表的上下文
        context = {
            "title": "项目文档",
            "content": "这里有一个项目列表",
            "items": [
                {"name": "项目1", "description": "这是第一个项目"},
                {"name": "项目2", "description": "这是第二个项目"},
                {"name": "项目3", "description": "这是第三个项目"}
            ],
            "creation_date": "2025-04-20T15:30:00"
        }
        
        # 渲染文档
        result = renderer.render_document("doc_template.j2", context)
        
        # 验证结果
        assert "# 项目文档" in result
        assert "这里有一个项目列表" in result
        assert "## 项目列表" in result
        assert "- 项目1: 这是第一个项目" in result
        assert "- 项目2: 这是第二个项目" in result
        assert "- 项目3: 这是第三个项目" in result
        assert "文档创建时间: 2025-04-20" in result
    
    def test_create_document_from_content(self, setup_renderer):
        """测试从内容创建文档功能"""
        renderer = setup_renderer
        
        # 创建内容和附加上下文
        content = "这是通过API生成的文档内容"
        context = {
            "title": "生成的文档",
            "creation_date": "2025-04-20T18:00:00"
        }
        
        # 从内容创建文档
        result = renderer.create_document_from_content(content, "doc_template.j2", context)
        
        # 验证结果
        assert "# 生成的文档" in result
        assert "这是通过API生成的文档内容" in result
        assert "文档创建时间: 2025-04-20" in result
    
    def test_create_default_template(self, setup_renderer):
        """测试创建默认模板功能"""
        renderer = setup_renderer
        
        # 创建prd类型的默认模板
        template_name = renderer.create_default_template("prd_default.j2", "prd")
        
        # 验证模板是否创建成功
        assert template_name == "prd_default.j2"
        
        # 获取模板变量
        variables = renderer.get_template_variables("prd_default.j2")
        assert "content" in variables["required"]
        assert "title" in variables["optional"]
        
        # 测试渲染默认模板
        result = renderer.render_document("prd_default.j2", {
            "content": "PRD文档内容",
            "title": "产品需求",
            "creation_date": "2025-04-20T10:00:00"
        })
        
        assert "# 产品需求" in result
        assert "PRD文档内容" in result 