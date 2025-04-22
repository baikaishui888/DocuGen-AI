"""
模板渲染器模块
负责处理文档模板的渲染，将生成的内容与模板结合
"""

import logging
from typing import Dict, Any, Optional, List

from ..utils.template import TemplateManager


class DocumentRenderer:
    """
    文档渲染器
    负责处理文档模板的渲染，管理模板变量和格式
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        初始化文档渲染器
        
        Args:
            templates_dir: 模板目录路径，如未提供则使用默认路径
        """
        self.logger = logging.getLogger("docugen.renderer")
        self.template_manager = TemplateManager(templates_dir)
        
        # 注册自定义过滤器
        self._register_custom_filters()
    
    def _register_custom_filters(self):
        """注册所有自定义过滤器"""
        self.register_custom_filter("format_date", self._format_date)
        self.register_custom_filter("is_empty", self._is_empty)
    
    def render_document(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        渲染文档
        
        Args:
            template_name: 模板名称
            context: 渲染上下文（变量）
            
        Returns:
            渲染后的文档内容
            
        Raises:
            ValueError: 如果模板不存在或渲染失败
        """
        self.logger.info(f"渲染文档: {template_name}")
        
        try:
            # 处理上下文变量
            processed_context = self._process_context(context)
            
            # 渲染模板
            return self.template_manager.render_template(template_name, processed_context)
        
        except Exception as e:
            self.logger.error(f"渲染文档失败: {str(e)}")
            raise ValueError(f"渲染文档失败: {str(e)}")
    
    def _process_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理渲染上下文
        添加辅助函数和过滤器
        
        Args:
            context: 原始上下文
            
        Returns:
            处理后的上下文
        """
        # 创建上下文副本
        processed = context.copy()
        
        return processed
    
    def _format_date(self, date_str: str, format_str: str = "%Y-%m-%d") -> str:
        """
        格式化日期的辅助函数
        可以在模板中使用
        
        Args:
            date_str: 日期字符串
            format_str: 格式化模式
            
        Returns:
            格式化后的日期字符串
        """
        from datetime import datetime
        
        try:
            if isinstance(date_str, str):
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return date_obj.strftime(format_str)
            return str(date_str)
        except Exception:
            return date_str
    
    def _is_empty(self, value: Any) -> bool:
        """
        检查值是否为空的辅助函数
        可以在模板中使用
        
        Args:
            value: 要检查的值
            
        Returns:
            值是否为空
        """
        if value is None:
            return True
        if isinstance(value, (str, list, dict)) and not value:
            return True
        return False
    
    def get_template_variables(self, template_name: str) -> Dict[str, List[str]]:
        """
        获取模板所需的变量
        
        Args:
            template_name: 模板名称
            
        Returns:
            包含必需和可选变量的字典
            
        Raises:
            ValueError: 如果模板不存在
        """
        metadata = self.template_manager.get_template_metadata(template_name)
        
        return {
            "required": metadata.get("required_variables", []),
            "optional": metadata.get("optional_variables", [])
        }
    
    def list_available_templates(self, doc_type: Optional[str] = None) -> List[str]:
        """
        列出可用的模板
        
        Args:
            doc_type: 可选的文档类型过滤
            
        Returns:
            模板名称列表
        """
        return self.template_manager.list_templates(doc_type)
    
    def create_document_from_content(self, content: str, template_name: str, 
                                   context: Optional[Dict[str, Any]] = None) -> str:
        """
        将生成的内容应用到模板中
        
        Args:
            content: 生成的文档内容
            template_name: 模板名称
            context: 附加的上下文变量
            
        Returns:
            最终的文档内容
            
        Raises:
            ValueError: 如果模板不存在或渲染失败
        """
        if context is None:
            context = {}
        
        # 将内容添加到上下文中
        context["content"] = content
        
        # 渲染模板
        return self.render_document(template_name, context)
    
    def register_custom_filter(self, name: str, filter_func: callable) -> None:
        """
        注册自定义过滤器
        
        Args:
            name: 过滤器名称
            filter_func: 过滤器函数
        """
        self.template_manager.env.filters[name] = filter_func
        self.logger.info(f"注册自定义过滤器: {name}")
    
    def register_custom_function(self, name: str, func: callable) -> None:
        """
        注册自定义函数
        
        Args:
            name: 函数名称
            func: 函数
        """
        self.template_manager.env.globals[name] = func
        self.logger.info(f"注册自定义函数: {name}")
    
    def create_default_template(self, template_name: str, doc_type: str) -> str:
        """
        创建默认模板
        
        Args:
            template_name: 模板名称
            doc_type: 文档类型
            
        Returns:
            创建的模板名称
            
        Raises:
            ValueError: 如果模板已存在
        """
        # 根据文档类型创建适当的默认模板
        templates = {
            "prd": """# {{ title | default('产品需求文档') }}

## 1. 项目概述

{{ content }}

## 2. 功能需求

{% if requirements is defined %}
{% for req in requirements %}
### 2.{{ loop.index }}. {{ req.title }}

{{ req.description }}

{% endfor %}
{% endif %}

## 3. 非功能需求

{% if non_functional_requirements is defined %}
{% for req in non_functional_requirements %}
### 3.{{ loop.index }}. {{ req.title }}

{{ req.description }}

{% endfor %}
{% endif %}

## 4. 项目计划

{% if project_timeline is defined %}
| 阶段 | 开始日期 | 结束日期 | 状态 |
|-----|---------|---------|------|
{% for phase in project_timeline %}
| {{ phase.name }} | {{ phase.start_date | format_date }} | {{ phase.end_date | format_date }} | {{ phase.status }} |
{% endfor %}
{% endif %}

## 5. 附录

文档创建时间: {{ creation_date | default('N/A') }}
""",
            "workflow": """# {{ title | default('流程文档') }}

## 流程概述

{{ content }}

{% if workflows is defined %}
{% for workflow in workflows %}
## {{ workflow.name }}

{% if workflow.description is defined %}
{{ workflow.description }}
{% endif %}

{% if workflow.steps is defined %}
### 步骤

{% for step in workflow.steps %}
1. {{ step }}
{% endfor %}
{% endif %}

{% endfor %}
{% endif %}

---
文档创建时间: {{ creation_date | default('N/A') }}
""",
            "tech_stack": """# {{ title | default('技术栈文档') }}

## 技术选型

{{ content }}

{% if technologies is defined %}
## 核心技术

{% for tech in technologies %}
### {{ tech.name }}

- 版本: {{ tech.version }}
- 用途: {{ tech.purpose }}
{% if tech.description is defined %}
- 说明: {{ tech.description }}
{% endif %}

{% endfor %}
{% endif %}

{% if dependencies is defined %}
## 依赖列表

| 依赖 | 版本 | 用途 |
|-----|------|-----|
{% for dep in dependencies %}
| {{ dep.name }} | {{ dep.version }} | {{ dep.purpose }} |
{% endfor %}
{% endif %}

---
文档创建时间: {{ creation_date | default('N/A') }}
"""
        }
        
        # 如果没有对应的默认模板，使用通用模板
        if doc_type not in templates:
            template_content = """# {{ title | default('文档') }}

{{ content }}

---
文档创建时间: {{ creation_date | default('N/A') }}
"""
        else:
            template_content = templates[doc_type]
        
        # 确定元数据
        metadata = {
            "name": template_name,
            "description": f"{doc_type.upper()}文档默认模板",
            "version": "1.0.0",
            "required_variables": ["content"],
            "optional_variables": ["title", "creation_date"]
        }
        
        # 创建模板
        self.template_manager.create_template(template_name, template_content, metadata)
        
        # 创建新模板后确保过滤器已注册
        self._register_custom_filters()
        
        return template_name 