"""
提示词管理器测试
测试提示词加载和管理功能
"""

import os
import tempfile
import pytest
from pathlib import Path
from docugen.utils.prompt import PromptManager


class TestPromptManager:
    """提示词管理器测试类"""
    
    def setup_method(self):
        """测试前准备工作"""
        # 创建临时提示词目录
        self.temp_dir = tempfile.TemporaryDirectory()
        self.prompt_dir = Path(self.temp_dir.name)
        
        # 创建测试提示词文件
        self._create_test_prompts()
    
    def teardown_method(self):
        """测试后清理工作"""
        self.temp_dir.cleanup()
    
    def _create_test_prompts(self):
        """创建测试提示词文件"""
        # 创建与PromptManager.DEFAULT_PROMPT_FILES中一致的提示词文件
        prompts = {
            "1.构思梳理文档提示词.md": "# 构思梳理提示词\n\n这是测试用的构思梳理提示词内容，这里包含了足够的内容来通过验证检查。\n\n## 二级标题\n\n这是另一个段落，确保内容长度足够。这个提示词用于指导AI生成构思梳理文档。\n\n## 使用方法\n\n在使用此提示词时，请确保提供足够的上下文信息，以便AI能够生成高质量的构思梳理文档。\n\n构思梳理文档应该包含项目概述、目标用户、主要功能等内容。\n",
            "2.产品需求文档（PRD）提示词.md": "# PRD提示词标题\n\n这是测试用的PRD提示词内容，需要确保内容足够详细。\n\n## 文档结构\n\n产品需求文档应该包含以下内容：\n\n1. 产品概述\n2. 用户需求\n3. 功能规格\n4. 非功能性需求\n\n## 示例内容\n\n这里是一些示例内容，用于说明如何编写高质量的PRD文档。请确保文档内容清晰、结构化，并且包含足够的细节。",
            "3.应用流程文档提示词.md": "# 流程文档提示词\n\n这是测试用的流程文档提示词内容，需要确保内容足够详细。\n\n## 文档结构\n\n应用流程文档应该包含以下内容：\n\n1. 业务流程概述\n2. 流程图\n3. 流程步骤详解\n4. 异常处理\n\n## 示例内容\n\n这里是一些示例内容，用于说明如何编写高质量的应用流程文档。请确保文档内容清晰、结构化，并且包含足够的流程细节。"
        }
        
        # 写入文件
        for filename, content in prompts.items():
            with open(self.prompt_dir / filename, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def test_prompt_loading(self):
        """测试提示词加载功能"""
        # 创建提示词管理器
        manager = PromptManager(str(self.prompt_dir))
        
        # 验证提示词是否正确加载
        assert manager.is_prompt_available("brainstorm")
        assert manager.is_prompt_available("prd")
        assert manager.is_prompt_available("workflow")
        assert not manager.is_prompt_available("nonexistent")
    
    def test_get_prompt(self):
        """测试获取提示词功能"""
        manager = PromptManager(str(self.prompt_dir))
        
        # 验证提示词内容
        assert "构思梳理提示词" in manager.get_prompt("brainstorm")
        assert "PRD提示词标题" in manager.get_prompt("prd")
        assert "流程文档提示词" in manager.get_prompt("workflow")
        assert manager.get_prompt("nonexistent") is None
    
    def test_available_prompts(self):
        """测试获取可用提示词列表"""
        manager = PromptManager(str(self.prompt_dir))
        
        available = manager.get_available_prompts()
        assert len(available) == 3
        assert "brainstorm" in available
        assert "prd" in available
        assert "workflow" in available
    
    def test_reload_prompt(self):
        """测试重新加载提示词功能"""
        manager = PromptManager(str(self.prompt_dir))
        
        # 修改提示词内容
        with open(self.prompt_dir / "2.产品需求文档（PRD）提示词.md", 'w', encoding='utf-8') as f:
            f.write("""# 更新后的PRD提示词

这是更新后的测试内容，确保内容长度足够通过验证。

## 文档结构
这是更新后的文档结构部分。

1. 产品概述
2. 用户需求
3. 功能规格
            
## 示例
这是一些示例内容。""")
        
        # 重新加载提示词
        assert manager.reload_prompt("prd")
        
        # 验证内容是否更新
        assert "更新后的PRD提示词" in manager.get_prompt("prd")
    
    def test_invalid_prompt_dir(self):
        """测试无效提示词目录"""
        with pytest.raises(FileNotFoundError):
            PromptManager("/nonexistent/directory")

    def test_validate_prompt_content(self):
        """测试提示词内容验证功能"""
        manager = PromptManager(str(self.prompt_dir))
        
        # 测试有效内容
        valid_content = """# 测试提示词标题

这是一个足够长的测试内容，用于验证提示词验证功能。

## 子标题

这是另一个段落，确保内容长度超过最小要求。这个内容应该能通过验证。

### 详细内容

- 项目一
- 项目二
- 项目三
"""
        is_valid, issues = manager._validate_prompt_content(valid_content, "test.md")
        assert is_valid
        assert len(issues) == 0
        
        # 测试无效内容 - 内容太短
        invalid_content_short = "# 标题太短"
        is_valid, issues = manager._validate_prompt_content(invalid_content_short, "test.md")
        assert not is_valid
        assert any("长度不足" in issue for issue in issues)
        
        # 测试无效内容 - 缺少标题
        invalid_content_no_header = """这是没有标题的内容。

但内容足够长，应该能满足长度要求。这只是为了测试标题验证功能。

这是另一个段落，确保内容长度超过最小要求。这个内容应该不能通过验证，因为缺少标题。"""
        is_valid, issues = manager._validate_prompt_content(invalid_content_no_header, "test.md")
        assert not is_valid
        assert any("标题数量不足" in issue for issue in issues)
        
        # 测试无效内容 - 包含禁止内容
        invalid_content_script = """# 测试标题

这是一个包含脚本标签的内容。

<script>alert('这是不允许的');</script>

这是另一个段落。"""
        is_valid, issues = manager._validate_prompt_content(invalid_content_script, "test.md")
        assert not is_valid
        assert any("禁止内容模式" in issue for issue in issues)

    def test_get_prompt_details(self):
        """测试获取提示词详情功能"""
        manager = PromptManager(str(self.prompt_dir))
        
        details = manager.get_prompt_details()
        
        # 验证返回的详情信息
        assert "brainstorm" in details
        assert "prd" in details
        assert "workflow" in details
        
        # 验证详情内容
        assert details["brainstorm"]["filename"] == "1.构思梳理文档提示词.md"
        assert details["brainstorm"]["word_count"] > 0
        assert details["brainstorm"]["header_count"] >= 3  # 至少包含1个h1和2个h2
        assert details["brainstorm"]["paragraph_count"] > 1
        assert "构思梳理提示词" in details["brainstorm"]["first_header"]
        
    def test_update_prompt_file(self):
        """测试更新提示词文件功能"""
        manager = PromptManager(str(self.prompt_dir))
        
        # 创建新的有效提示词内容
        new_content = """# 新的流程文档提示词

这是更新后的流程文档提示词内容，确保内容足够长以通过验证。

## 更新的文档结构

1. 新的业务流程概述
2. 更新的流程图
3. 新的流程步骤详解

## 示例内容

这里是更新后的示例内容，用于说明如何编写高质量的应用流程文档。"""
        
        # 更新提示词文件
        assert manager.update_prompt_file("workflow", new_content)
        
        # 验证文件是否已更新
        with open(self.prompt_dir / "3.应用流程文档提示词.md", 'r', encoding='utf-8') as f:
            file_content = f.read()
            assert "新的流程文档提示词" in file_content
        
        # 验证内存中的提示词是否已更新
        assert "新的流程文档提示词" in manager.get_prompt("workflow")
        
        # 测试无效内容更新
        invalid_content = "# 标题太短"
        assert not manager.update_prompt_file("workflow", invalid_content)
        
        # 验证内容未被更新
        assert "新的流程文档提示词" in manager.get_prompt("workflow") 