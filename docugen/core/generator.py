"""
文档生成器模块
实现文档生成的核心逻辑
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..api.client import AIClient
from ..core.pipeline import DocumentPipeline
from ..utils.prompt import PromptManager
from ..utils.file import FileManager
from ..utils.progress import ProgressManager
from ..config import Config


class DocumentGenerator:
    """
    文档生成器
    文档生成系统的主要组件，协调文档生成流程
    """
    
    def __init__(self, model_name: Optional[str] = None, debug_mode: bool = False, 
                 progress_manager: Optional[ProgressManager] = None):
        """
        初始化文档生成器
        :param model_name: 自定义模型名称，如果为None则使用配置中的默认模型
        :param debug_mode: 是否启用调试模式，显示模型输入输出详情
        :param progress_manager: 进度管理器，如果为None将创建新实例
        """
        self.logger = logging.getLogger("docugen.generator")
        self.config = Config()
        self.debug_mode = debug_mode
        
        # 获取配置
        api_key = self.config.get_api_key()
        if not api_key:
            self.logger.error("未设置API密钥")
            raise ValueError("未设置API密钥，请设置OPENAI_API_KEY环境变量")
        
        # 获取API基础URL
        api_base_url = self.config.get_api_base_url()
        if api_base_url:
            self.logger.info(f"使用自定义API基础URL: {api_base_url}")
        
        # 获取模型名称
        self.model_name = model_name or self.config.get_model_name()
        if self.model_name != self.config.get("api.model"):
            self.logger.info(f"使用自定义模型: {self.model_name}")
        
        prompts_dir = self.config.get("paths.prompts_dir")
        output_dir = self.config.get("paths.output_dir")
        
        # 初始化组件
        self.ai_client = AIClient(api_key, api_base_url, debug_mode=debug_mode)
        self.prompt_manager = PromptManager(prompts_dir)
        self.file_manager = FileManager(output_dir)
        self.progress_manager = progress_manager or ProgressManager()
        
        # 创建pipeline时传入file_manager和progress_manager
        self.pipeline = DocumentPipeline(
            self.prompt_manager, 
            self.ai_client, 
            self.model_name,
            file_manager=self.file_manager,
            progress_manager=self.progress_manager
        )
        
        # 记录初始化信息
        if debug_mode:
            self.logger.info("文档生成器已初始化，调试模式已启用")
    
    def generate_document(self, project_info: Dict[str, Any], doc_type: str) -> str:
        """
        生成单个文档
        :param project_info: 项目信息
        :param doc_type: 文档类型
        :return: 生成的文档内容
        """
        self.logger.info(f"开始生成文档: {doc_type}")
        
        try:
            # 确保项目目录存在 - 为单文档自动保存做准备
            project_name = project_info.get("name", project_info.get("project_name", "未命名项目"))
            self.file_manager.create_project_dir(project_name)
            
            # 通过流水线生成文档 - 现在pipeline会自动保存文档
            content = self.pipeline.generate_document(doc_type, project_info)
            
            # 注意：不再需要手动保存文档，因为pipeline已经在generate_document中自动保存了
            self.logger.info(f"文档生成成功: {doc_type}")
            
            # 如果需要，可以获取保存路径并记录
            if self.progress_manager:
                save_path = self.progress_manager.get_save_path(doc_type)
                if save_path:
                    self.logger.info(f"文档已保存到: {save_path}")
            
            return content
            
        except Exception as e:
            self.logger.error(f"生成文档失败 {doc_type}: {str(e)}")
            raise
    
    def generate_all_documents(self, project_info: Dict[str, Any]) -> Dict[str, str]:
        """
        生成所有文档
        :param project_info: 项目信息
        :return: 生成的所有文档内容
        """
        self.logger.info("开始生成所有文档")
        project_name = project_info.get("name", "未命名项目")
        
        try:
            # 重置进度管理器
            self.progress_manager.reset()
            
            # 启动进度显示
            self.progress_manager.start()
            
            # 通过流水线生成所有文档 - 现在pipeline会自动保存每个文档
            documents = self.pipeline.generate_all(project_info)
            
            # 创建版本快照
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.file_manager.create_version_snapshot(project_name, timestamp)
            
            # 停止进度显示
            self.progress_manager.stop()
            
            # 显示保存摘要
            self.logger.info(f"所有文档生成成功，版本: {timestamp}")
            if self.progress_manager:
                summary_table = self.progress_manager.get_summary_table()
                self.logger.info("文档保存摘要:")
                for doc_type, save_path in self.progress_manager.get_all_save_paths().items():
                    self.logger.info(f"  - {doc_type}: {save_path}")
            
            return documents
            
        except Exception as e:
            self.logger.error(f"生成所有文档失败: {str(e)}")
            # 停止进度显示
            if self.progress_manager:
                self.progress_manager.stop()
            raise
    
    def load_version(self, project_name: str, version_id: str) -> Dict[str, str]:
        """
        加载指定版本的文档
        :param project_name: 项目名称
        :param version_id: 版本ID
        :return: 加载的文档内容
        """
        self.logger.info(f"加载版本: {version_id}")
        return self.file_manager.load_version(project_name, version_id)
    
    def list_versions(self, project_name: str) -> List[str]:
        """
        列出项目的所有版本
        :param project_name: 项目名称
        :return: 版本ID列表
        """
        return self.file_manager.list_versions(project_name)
    
    def get_generation_status(self) -> Dict[str, Any]:
        """
        获取文档生成状态
        :return: 状态信息
        """
        statuses = self.pipeline.get_all_status()
        return {
            "status": {doc_type: status.value for doc_type, status in statuses.items()},
            "timestamp": datetime.now().isoformat()
        }

    def generate_documents(self, project_name: str, project_description: str) -> Dict[str, str]:
        """
        生成一套完整的文档，优化版将基于项目名称和描述，按照依赖关系自动生成完整文档集
        :param project_name: 项目名称
        :param project_description: 项目描述
        :return: 生成的文档内容字典
        """
        self.logger.info(f"开始为项目 '{project_name}' 生成文档")
        
        try:
            # 重置进度管理器
            self.progress_manager.reset()
            
            # 启动进度显示
            self.progress_manager.start()
            
            # 创建项目信息对象
            project_info = {
                "name": project_name,  # 确保使用"name"键
                "description": project_description,
                "created_at": datetime.now().isoformat()
            }
            
            # 创建项目目录
            project_dir = self.file_manager.create_project_dir(project_name)
            
            # 生成文档
            start_time = time.time()
            
            # 使用优化后的流水线运行文档生成流程 - 现在pipeline会自动保存每个文档
            documents = self.pipeline.run(project_info)
            
            end_time = time.time()
            
            # 计算生成时间
            generation_time = end_time - start_time
            self.logger.info(f"文档生成完成，耗时 {generation_time:.2f} 秒")
            
            # 创建版本快照
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.file_manager.create_version_snapshot(project_name, timestamp)
            
            # 停止进度显示
            self.progress_manager.stop()
            
            # 显示文档摘要
            if self.progress_manager:
                self.logger.info("生成文档摘要：")
                for doc_type, save_path in self.progress_manager.get_all_save_paths().items():
                    self.logger.info(f"  - {doc_type}: {save_path}")
            
            return documents
            
        except Exception as e:
            self.logger.error(f"文档生成失败: {str(e)}")
            # 停止进度显示
            if self.progress_manager:
                self.progress_manager.stop()
            raise 