"""
文件工具模块
负责文件和目录操作的工具函数集
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Dict


class FileManager:
    """
    文件管理器
    处理文档生成过程中的文件操作
    """
    
    def __init__(self, output_dir: str):
        """
        初始化文件管理器
        :param output_dir: 输出目录路径
        """
        self.logger = logging.getLogger("docugen.file")
        
        # 转换相对路径为绝对路径
        if output_dir.startswith("./") or output_dir.startswith("../"):
            # 确保相对路径是相对于项目根目录，而不是相对于当前模块目录
            current_dir = Path(__file__).parent
            module_dir = current_dir.parent  # docugen目录
            project_root = module_dir.parent  # 项目根目录
            
            # 移除前缀并创建绝对路径
            if output_dir.startswith("./"):
                # 如果是"./output"这样的路径，应该是相对于项目根目录
                clean_path = output_dir[2:]
                self.output_dir = (project_root / clean_path).resolve()
                self.logger.info(f"检测到相对路径 './': {output_dir} -> {self.output_dir}")
            elif output_dir.startswith("../"):
                # 如果是"../output"这样的路径，则是相对于docugen目录，向上一级
                parent_count = output_dir.count("../")
                clean_path = output_dir.replace("../", "", parent_count)
                
                # 从module_dir开始向上parent_count级
                target_dir = module_dir
                for _ in range(parent_count):
                    target_dir = target_dir.parent
                
                self.output_dir = (target_dir / clean_path).resolve()
                self.logger.info(f"检测到相对路径 '../': {output_dir} -> {self.output_dir}")
        else:
            # 如果是绝对路径或者简单的相对路径（不带./或../前缀）
            if os.path.isabs(output_dir):
                # 绝对路径
                self.output_dir = Path(output_dir)
                self.logger.info(f"检测到绝对路径: {output_dir}")
            else:
                # 简单相对路径，视为相对于项目根目录
                project_root = Path(__file__).parent.parent.parent  # 项目根目录
                self.output_dir = (project_root / output_dir).resolve()
                self.logger.info(f"检测到简单相对路径: {output_dir} -> {self.output_dir}")
        
        # 创建输出目录
        try:
            self._ensure_dir(self.output_dir)
        except Exception as e:
            self.logger.error(f"创建输出目录失败: {self.output_dir}, 错误: {str(e)}")
            # 如果无法创建指定目录，尝试使用备用目录
            backup_dir = Path.home() / "DocuGen_Output"
            self.logger.warning(f"尝试使用备用目录: {backup_dir}")
            self.output_dir = backup_dir
            self._ensure_dir(self.output_dir)
    
    def _ensure_dir(self, directory: Path) -> None:
        """
        确保目录存在，如不存在则创建
        :param directory: 目录路径
        """
        if not directory.exists():
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"创建目录: {directory}")
            except Exception as e:
                self.logger.error(f"创建目录失败 {directory}: {str(e)}")
                raise
    
    def create_project_dir(self, project_name: str) -> Path:
        """
        创建项目目录
        :param project_name: 项目名称
        :return: 项目目录路径
        """
        project_dir = self.output_dir / project_name
        self._ensure_dir(project_dir)
        
        # 创建current和versions子目录
        current_dir = project_dir / "current"
        versions_dir = project_dir / "versions"
        self._ensure_dir(current_dir)
        self._ensure_dir(versions_dir)
        
        return project_dir
    
    def save_document(self, project_name: str, doc_type: str, content: str) -> Path:
        """
        保存文档到项目的current目录
        :param project_name: 项目名称
        :param doc_type: 文档类型
        :param content: 文档内容
        :return: 保存的文件路径
        """
        # 确定文件名
        filename = self._get_filename_for_doc_type(doc_type)
        
        # 确保项目目录存在
        project_dir = self.create_project_dir(project_name)
        file_path = project_dir / "current" / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"文档保存成功: {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"保存文档失败 {file_path}: {str(e)}")
            raise
    
    def save_documents(self, project_name: str, documents: Dict[str, str]) -> Dict[str, Path]:
        """
        保存多个文档到项目目录
        :param project_name: 项目名称
        :param documents: 文档内容字典，格式为 {doc_type: content}
        :return: 保存的文件路径字典，格式为 {doc_type: file_path}
        """
        result = {}
        for doc_type, content in documents.items():
            file_path = self.save_document(project_name, doc_type, content)
            result[doc_type] = file_path
        
        return result
    
    def _get_filename_for_doc_type(self, doc_type: str) -> str:
        """
        根据文档类型获取文件名
        :param doc_type: 文档类型
        :return: 文件名
        """
        # 文档类型到文件名的映射
        doc_filenames = {
            'brainstorm': '构思梳理.md',
            'requirement_confirm': '需求确认.md',
            'prd': '产品需求文档(PRD).md',
            'workflow': '应用流程文档.md',
            'tech_stack': '技术栈.md',
            'frontend': '前端设计指南.md',
            'backend': '后端架构设计.md',
            'dev_plan': '项目开发计划.md'
        }
        
        if doc_type not in doc_filenames:
            self.logger.warning(f"未知的文档类型: {doc_type}，使用默认文件名")
            return f"{doc_type}.md"
            
        return doc_filenames[doc_type]
    
    def create_version_snapshot(self, project_name: str, version_id: str) -> Optional[Path]:
        """
        创建版本快照
        :param project_name: 项目名称
        :param version_id: 版本ID（通常是时间戳）
        :return: 版本目录路径，如果失败则返回None
        """
        project_dir = self.output_dir / project_name
        current_dir = project_dir / "current"
        version_dir = project_dir / "versions" / version_id
        
        # 检查current目录是否存在
        if not current_dir.exists() or not current_dir.is_dir():
            self.logger.error(f"current目录不存在: {current_dir}")
            return None
        
        # 创建版本目录
        self._ensure_dir(version_dir)
        
        try:
            # 复制current目录中的所有文件到版本目录
            for file_path in current_dir.glob("*.md"):
                shutil.copy2(file_path, version_dir)
            
            self.logger.info(f"创建版本快照成功: {version_id}")
            return version_dir
        except Exception as e:
            self.logger.error(f"创建版本快照失败 {version_id}: {str(e)}")
            return None
    
    def list_versions(self, project_name: str) -> List[str]:
        """
        列出项目的所有版本
        :param project_name: 项目名称
        :return: 版本ID列表（按时间排序）
        """
        versions_dir = self.output_dir / project_name / "versions"
        
        if not versions_dir.exists() or not versions_dir.is_dir():
            return []
        
        # 获取所有版本目录并排序
        versions = [d.name for d in versions_dir.iterdir() if d.is_dir()]
        versions.sort()  # 按时间戳排序
        
        return versions
    
    def load_version(self, project_name: str, version_id: str) -> Dict[str, str]:
        """
        加载指定版本的所有文档
        :param project_name: 项目名称
        :param version_id: 版本ID
        :return: 文档内容字典 {doc_type: content}
        """
        version_dir = self.output_dir / project_name / "versions" / version_id
        
        if not version_dir.exists() or not version_dir.is_dir():
            self.logger.error(f"版本目录不存在: {version_dir}")
            return {}
        
        documents = {}
        
        # 加载所有markdown文件
        for file_path in version_dir.glob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 根据文件名推断文档类型
                doc_type = self._get_doc_type_from_filename(file_path.name)
                if doc_type:
                    documents[doc_type] = content
            except Exception as e:
                self.logger.error(f"加载文档失败 {file_path}: {str(e)}")
        
        return documents
    
    def _get_doc_type_from_filename(self, filename: str) -> Optional[str]:
        """
        根据文件名获取文档类型
        :param filename: 文件名
        :return: 文档类型，如果无法识别则返回None
        """
        # 文件名到文档类型的映射（与_get_filename_for_doc_type相反）
        filename_to_doc_type = {
            '构思梳理.md': 'brainstorm',
            '需求确认.md': 'requirement_confirm',
            '产品需求文档(PRD).md': 'prd',
            '应用流程文档.md': 'workflow',
            '技术栈.md': 'tech_stack',
            '前端设计指南.md': 'frontend',
            '后端架构设计.md': 'backend',
            '项目开发计划.md': 'dev_plan'
        }
        
        return filename_to_doc_type.get(filename) 