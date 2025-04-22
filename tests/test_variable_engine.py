"""
变量替换引擎测试模块
测试变量管理器和模板变量处理器功能
"""

import pytest
from docugen.utils.variable import VariableManager, TemplateVariableProcessor


class TestVariableManager:
    """测试变量管理器功能"""
    
    def test_extract_variables(self):
        """测试从内容中提取变量定义"""
        content = """# 测试文档

这是一个测试内容。

```variables
project_name = "DocuGen AI"
version = "1.0.0"
author = "开发团队"
```

文档的正文内容。
"""
        
        var_manager = VariableManager()
        cleaned_content, variables = var_manager.extract_variables(content)
        
        # 验证变量是否被正确提取
        assert "project_name" in variables
        assert variables["project_name"] == "DocuGen AI"
        assert variables["version"] == "1.0.0"
        assert variables["author"] == "开发团队"
        
        # 验证变量块是否从内容中移除
        assert "```variables" not in cleaned_content
        assert "project_name = " not in cleaned_content
        assert "文档的正文内容。" in cleaned_content
    
    def test_multiple_variable_blocks(self):
        """测试多个变量块的处理"""
        content = """# 测试文档

```variables
title = "测试标题"
author = "测试作者"
```

第一部分内容。

```variables
version = "1.0.0"
date = "2025-04-22"
```

第二部分内容。
"""
        
        var_manager = VariableManager()
        cleaned_content, variables = var_manager.extract_variables(content)
        
        # 验证所有变量块中的变量是否被正确提取
        assert len(variables) == 4
        assert variables["title"] == "测试标题"
        assert variables["author"] == "测试作者"
        assert variables["version"] == "1.0.0"
        assert variables["date"] == "2025-04-22"
        
        # 验证所有变量块是否从内容中移除
        assert "```variables" not in cleaned_content
        assert "第一部分内容。" in cleaned_content
        assert "第二部分内容。" in cleaned_content
    
    def test_replace_variables(self):
        """测试变量引用替换功能"""
        var_manager = VariableManager()
        var_manager.set_variable("project_name", "DocuGen AI")
        var_manager.set_variable("version", "1.0.0")
        
        content = """# ${project_name} 文档

这是 ${project_name} 的文档，版本 ${version}。

未定义的变量：${undefined:默认值}
"""
        
        result = var_manager.replace_variables(content)
        
        # 验证变量引用是否被正确替换
        assert "# DocuGen AI 文档" in result
        assert "这是 DocuGen AI 的文档，版本 1.0.0。" in result
        assert "未定义的变量：默认值" in result
    
    def test_find_undefined_variables(self):
        """测试查找未定义的变量"""
        var_manager = VariableManager()
        var_manager.set_variable("defined1", "值1")
        var_manager.set_variable("defined2", "值2")
        
        content = """这个文档引用了 ${defined1} 和 ${defined2}，
但也引用了未定义的 ${undefined1} 和 ${undefined2:默认值}。"""
        
        undefined = var_manager.find_undefined_variables(content)
        
        # 验证是否正确识别未定义的变量
        assert "undefined1" in undefined
        assert "undefined2" in undefined
        assert "defined1" not in undefined
        assert "defined2" not in undefined


class TestTemplateVariableProcessor:
    """测试模板变量处理器功能"""
    
    def test_process_content(self):
        """测试内容处理功能"""
        content = """# 测试文档

```variables
title = "变量测试"
version = "1.0.0"
```

这是 ${title} 文档，版本 ${version}。

也可以使用 ${undefined:默认值} 变量。
"""
        
        processor = TemplateVariableProcessor()
        processed_content, variables = processor.process_content(content)
        
        # 验证变量是否被正确提取和替换
        assert "```variables" not in processed_content
        assert "这是 变量测试 文档，版本 1.0.0。" in processed_content
        assert "也可以使用 默认值 变量。" in processed_content
        assert variables["title"] == "变量测试"
        assert variables["version"] == "1.0.0"
    
    def test_get_template_context(self):
        """测试获取模板上下文功能"""
        content = """```variables
base_title = "测试文档"
author = "测试作者"
```

内容不重要
"""
        
        processor = TemplateVariableProcessor()
        processor.process_content(content)
        
        # 添加额外的变量
        context = processor.get_template_context({
            "additional_var": "附加变量",
            "date": "2025-04-22"
        })
        
        # 验证上下文是否包含所有变量
        assert context["base_title"] == "测试文档"
        assert context["author"] == "测试作者"
        assert context["additional_var"] == "附加变量"
        assert context["date"] == "2025-04-22"
    
    def test_validate_content(self):
        """测试内容验证功能"""
        content = """# ${title} 文档

作者：${author}
版本：${version}

这里引用了未定义的变量：${undefined}
"""
        
        processor = TemplateVariableProcessor()
        processor.variable_manager.set_variable("title", "测试标题")
        processor.variable_manager.set_variable("author", "测试作者")
        # 注意没有设置version和undefined变量
        
        errors = processor.validate_content(content)
        
        # 验证是否正确识别所有未定义的变量
        assert len(errors) == 2
        assert any("version" in error for error in errors)
        assert any("undefined" in error for error in errors)
    
    def test_complex_scenario(self):
        """测试复杂场景：变量嵌套和多级处理"""
        content = """# 项目文档

```variables
project_name = "DocuGen"
full_title = "${project_name} AI 平台"
year = "2025"
version = "1.0.0"
copyright = "${project_name} © ${year}"
```

# ${full_title}

版本：${version}

${copyright} 保留所有权利。

负责人：${owner:未指定}
"""
        
        processor = TemplateVariableProcessor()
        
        # 第一次处理：提取和替换初始变量
        processed_content, _ = processor.process_content(content)
        
        # 第二次处理：处理嵌套变量
        final_content, _ = processor.process_content(processed_content)
        
        # 验证嵌套变量是否被正确解析
        assert "# DocuGen AI 平台" in final_content
        assert "版本：1.0.0" in final_content
        assert "DocuGen © 2025 保留所有权利。" in final_content
        assert "负责人：未指定" in final_content 