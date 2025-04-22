"""
模拟提示词管理器
用于测试文档生成功能，返回预定义的提示词
"""

import logging
from typing import Dict, Optional, List

class MockPromptManager:
    """
    模拟提示词管理器
    返回预定义的提示词而不是从文件加载
    """
    
    def __init__(self, prompts_dir: str = ""):
        """初始化模拟提示词管理器"""
        self.logger = logging.getLogger("test.mock_prompt_manager")
        self.prompts_dir = prompts_dir
        
        # 预定义的提示词
        self.prompts = {
            "brainstorm": """# 构思梳理提示词
请为项目进行构思梳理，包括核心功能、用户需求和技术考量。

## 项目名称
{{project_name}}

## 输出要求
- 项目概述
- 核心功能
- 用户需求
- 技术考量
""",
            "requirement_confirm": """# 需求确认文档提示词
请为项目创建需求确认文档，确认项目需求范围和边界。

## 项目名称
{{project_name}}

## 输出要求
- 项目基本信息
- 确认的核心需求
- 用户期望
- 项目边界
""",
            "prd": """# 产品需求文档提示词
请为项目创建产品需求文档，详细描述功能和非功能需求。

## 项目名称
{{project_name}}

## 输出要求
- 产品概述
- 功能需求
- 非功能需求
""",
            "workflow": """# 应用流程文档提示词
请为项目设计应用流程，说明文档生成过程和用户交互方式。

## 项目名称
{{project_name}}

## 输出要求
- 文档生成流程
- 用户交互流程
- 错误处理流程
""",
            "tech_stack": """# 技术栈文档提示词
请为项目选择合适的技术栈并说明原因。

## 项目名称
{{project_name}}

## 输出要求
- 核心技术
- 依赖库
- 开发工具
""",
            "frontend": """# 前端设计指南提示词
请为项目设计用户界面和交互方式。

## 项目名称
{{project_name}}

## 输出要求
- 界面设计
- 交互流程
- 视觉风格
""",
            "backend": """# 后端架构设计提示词
请为项目设计后端架构和数据流。

## 项目名称
{{project_name}}

## 输出要求
- 模块结构
- 数据流
- 错误处理
""",
            "dev_plan": """# 开发计划提示词
请为项目制定开发计划和里程碑。

## 项目名称
{{project_name}}

## 输出要求
- 开发阶段
- 优先级规划
- 里程碑
"""
        }
    
    def get_prompt(self, doc_type: str) -> Optional[str]:
        """
        获取文档类型对应的提示词
        :param doc_type: 文档类型
        :return: 提示词内容，如果不存在则返回None
        """
        self.logger.info(f"获取提示词: {doc_type}")
        return self.prompts.get(doc_type)
    
    def get_all_prompts(self) -> Dict[str, str]:
        """
        获取所有提示词
        :return: 所有提示词的字典
        """
        return self.prompts.copy()
    
    def list_available_doc_types(self) -> List[str]:
        """
        列出所有可用的文档类型
        :return: 文档类型列表
        """
        return list(self.prompts.keys()) 