"""
文档生成流水线模块
负责协调整个文档生成过程，管理生成顺序和依赖关系
"""

import json
import logging
import os
from enum import Enum
from typing import Dict, List, Optional, Any

from ..api.client import AIClient
from ..utils.prompt import PromptManager
from ..utils.file import FileManager
from ..utils.progress import ProgressManager  # 新增导入进度管理器
from ..config import Config


class DocumentStatus(Enum):
    """文档生成状态"""
    READY = "ready"            # 准备就绪
    GENERATING = "generating"  # 生成中
    PAUSED = "paused"          # 已暂停
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败


class DocumentPipeline:
    """
    文档生成流水线
    控制文档生成流程，确保按正确顺序生成文档并管理状态
    """
    
    # 文档生成顺序定义 - 修改顺序以匹配提示词文件编号
    DOC_ORDER = [
        'brainstorm',           # 构思梳理文档 (0.构思梳理文档提示词.md)
        'requirement_confirm',  # 需求确认文档 (1.需求确认文档提示词.md)
        'prd',                  # 产品需求文档 (2.产品需求文档（PRD）提示词.md)
        'workflow',             # 应用流程文档 (3.应用流程文档提示词.md)
        'tech_stack',           # 技术栈文档 (4.涉及技术栈文档提示词.md)
        'frontend',             # 前端设计指南 (5.前端设计文档提示词.md)
        'backend',              # 后端架构设计 (6.后端设计文档提示词.md)
        'dev_plan'              # 开发计划 (7.开发计划提示词.md)
    ]
    
    # 文档依赖关系定义 - 优化依赖关系，与生成顺序匹配
    DOC_DEPENDENCIES = {
        'requirement_confirm': ['brainstorm'],  # 需求确认依赖构思梳理
        'prd': ['brainstorm', 'requirement_confirm'],
        'workflow': ['brainstorm', 'requirement_confirm', 'prd'],
        'tech_stack': ['brainstorm', 'requirement_confirm', 'prd', 'workflow'],
        'frontend': ['brainstorm', 'requirement_confirm', 'prd', 'workflow', 'tech_stack'],
        'backend': ['brainstorm', 'requirement_confirm', 'prd', 'workflow', 'tech_stack'],
        'dev_plan': ['brainstorm', 'requirement_confirm', 'prd', 'workflow', 'tech_stack', 'frontend', 'backend']
    }
    
    def __init__(self, prompt_manager: PromptManager, ai_client: AIClient, model_name: Optional[str] = None, 
                 file_manager: Optional[FileManager] = None, progress_manager: Optional[ProgressManager] = None):
        """
        初始化文档生成流水线
        :param prompt_manager: 提示词管理器
        :param ai_client: AI客户端
        :param model_name: 自定义模型名称，如果为None则使用配置中的默认模型
        :param file_manager: 文件管理器，用于保存文档，如果为None则不保存到文件
        :param progress_manager: 进度管理器，用于更新生成进度，如果为None则不更新进度
        """
        self.prompt_manager = prompt_manager
        self.ai_client = ai_client
        self.model_name = model_name
        self.file_manager = file_manager  # 添加文件管理器
        self.progress_manager = progress_manager  # 添加进度管理器
        self.logger = logging.getLogger("docugen.pipeline")
        
        # 存储生成的文档内容
        self.documents: Dict[str, str] = {}
        # 跟踪文档状态
        self.status: Dict[str, DocumentStatus] = {
            doc_type: DocumentStatus.READY for doc_type in self.DOC_ORDER
        }
    
    def generate_document(self, doc_type: str, project_info: Dict[str, Any]) -> str:
        """
        生成单个文档
        :param doc_type: 文档类型
        :param project_info: 项目信息
        :return: 生成的文档内容
        """
        # 检查文档类型是否有效
        if doc_type not in self.DOC_ORDER:
            self.logger.error(f"无效的文档类型: {doc_type}")
            raise ValueError(f"无效的文档类型: {doc_type}")
        
        # 检查依赖是否已生成
        if doc_type in self.DOC_DEPENDENCIES:
            for dependency in self.DOC_DEPENDENCIES[doc_type]:
                if dependency not in self.documents:
                    self.logger.error(f"缺少依赖文档: {dependency}，无法生成{doc_type}")
                    raise ValueError(f"缺少依赖文档: {dependency}，无法生成{doc_type}")
        
        # 更新状态为生成中
        self.status[doc_type] = DocumentStatus.GENERATING
        self.logger.info(f"开始生成文档: {doc_type}")
        
        # 更新进度
        if self.progress_manager:
            self.progress_manager.update_current_task(f"生成{self._get_document_title(doc_type)}")
        
        try:
            # 获取提示词
            prompt = self.prompt_manager.get_prompt(doc_type)
            if not prompt:
                self.logger.error(f"未找到文档类型的提示词: {doc_type}")
                self.status[doc_type] = DocumentStatus.FAILED
                raise ValueError(f"未找到文档类型的提示词: {doc_type}")
            
            # 准备上下文信息
            context = self._prepare_context(doc_type, project_info)
            
            # 获取配置参数
            config = Config()
            temperature = config.get_temperature()
            max_tokens = config.get_max_tokens()
            
            # 获取正确的模型名称 - 确保使用环境变量中的值
            model_name = os.environ.get("OPENAI_MODEL_NAME") or self.model_name
            self.logger.debug(f"使用模型: {model_name}，来源: {'环境变量' if os.environ.get('OPENAI_MODEL_NAME') else '配置'}")
            
            # 调用API生成文档
            content = self.ai_client.generate_document(
                prompt=prompt, 
                context=context,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 更新状态和存储文档
            self.documents[doc_type] = content
            self.status[doc_type] = DocumentStatus.COMPLETED
            self.logger.info(f"文档生成成功: {doc_type}")
            
            # 实现单文档自动保存功能：每次生成一个文档后立即保存到本地
            if self.file_manager:
                project_name = project_info.get("name", project_info.get("project_name", "未命名项目"))
                file_path = self.file_manager.save_document(project_name, doc_type, content)
                self.logger.info(f"文档已保存: {file_path}")
                
                # 如果有进度管理器，更新保存状态
                if self.progress_manager:
                    self.progress_manager.update_save_status(doc_type, str(file_path))
            
            return content
            
        except Exception as e:
            self.status[doc_type] = DocumentStatus.FAILED
            self.logger.error(f"文档生成失败: {doc_type}, 错误: {str(e)}")
            
            # 更新进度
            if self.progress_manager:
                self.progress_manager.update_task_status(doc_type, "FAILED", str(e))
                
            raise
    
    def generate_all(self, project_info: Dict[str, Any]) -> Dict[str, str]:
        """
        按顺序生成所有文档
        :param project_info: 项目信息
        :return: 所有生成的文档内容
        """
        self.logger.info("开始生成所有文档")
        
        # 如果有进度管理器，初始化总进度
        if self.progress_manager:
            total_docs = len(self.DOC_ORDER)
            self.progress_manager.set_current_step(0, total_docs)
            self.progress_manager.update_status("GENERATING")
        
        for i, doc_type in enumerate(self.DOC_ORDER):
            # 更新总进度
            if self.progress_manager:
                self.progress_manager.set_current_step(i, len(self.DOC_ORDER))
            
            # 生成文档
            self.generate_document(doc_type, project_info)
        
        # 更新最终进度
        if self.progress_manager:
            self.progress_manager.set_current_step(len(self.DOC_ORDER), len(self.DOC_ORDER))
            self.progress_manager.update_status("COMPLETED")
        
        self.logger.info("所有文档生成完成")
        return self.documents
    
    def run(self, project_info: Dict[str, Any]) -> Dict[str, str]:
        """
        运行文档生成流水线
        :param project_info: 项目信息
        :return: 所有生成的文档内容
        """
        self.logger.info("开始运行文档生成流水线")
        
        # 重置已存在的文档和状态
        self.documents = {}
        self.status = {doc_type: DocumentStatus.READY for doc_type in self.DOC_ORDER}
        
        # 如果使用文件管理器，确保项目目录存在
        if self.file_manager:
            project_name = project_info.get("name", "未命名项目")
            self.file_manager.create_project_dir(project_name)
        
        # 调用generate_all方法生成所有文档
        result = self.generate_all(project_info)
        
        self.logger.info("文档生成流水线执行完成")
        return result
    
    def _prepare_context(self, doc_type: str, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备文档生成所需的上下文信息，优化后的版本会将前序文档完整内容附加到上下文中
        :param doc_type: 文档类型
        :param project_info: 项目信息
        :return: 上下文数据字典
        """
        context_data = {
            "project_info": project_info,
            "generated_docs": {},
            "document_chain": []  # 按顺序存储前序文档的内容
        }
        
        # 如果不是第一个文档类型，需要添加前序文档
        if doc_type in self.DOC_DEPENDENCIES:
            # 获取依赖文档并按照生成顺序排序
            dependencies = self.DOC_DEPENDENCIES[doc_type]
            for dependency in dependencies:
                if dependency in self.documents:
                    # 添加到文档链，包含文档类型和内容
                    context_data["document_chain"].append({
                        "type": dependency,
                        "title": self._get_document_title(dependency),
                        "content": self.documents[dependency]
                    })
                    
                    # 保持旧的存储方式兼容性
                    context_data["generated_docs"][dependency] = self.documents[dependency]
        
        # 记录日志
        dependency_count = len(context_data["document_chain"])
        self.logger.info(f"为文档 {doc_type} 准备了 {dependency_count} 个前序文档作为上下文")
        
        return context_data
    
    def _get_document_title(self, doc_type: str) -> str:
        """
        获取文档类型的可读标题
        :param doc_type: 文档类型
        :return: 文档标题
        """
        titles = {
            'requirement_confirm': '需求确认',
            'brainstorm': '构思梳理',
            'prd': '产品需求文档(PRD)',
            'workflow': '应用流程文档',
            'tech_stack': '技术栈',
            'frontend': '前端设计指南',
            'backend': '后端架构设计',
            'dev_plan': '项目开发计划'
        }
        return titles.get(doc_type, doc_type.replace('_', ' ').title())
    
    def get_status(self, doc_type: str) -> DocumentStatus:
        """
        获取文档生成状态
        :param doc_type: 文档类型
        :return: 文档状态
        """
        if doc_type not in self.status:
            raise ValueError(f"无效的文档类型: {doc_type}")
        return self.status[doc_type]
    
    def get_all_status(self) -> Dict[str, DocumentStatus]:
        """
        获取所有文档的状态
        :return: 文档状态字典
        """
        return self.status 