"""
版本管理模块
负责管理文档版本和创建版本快照
"""

import os
import json
import logging
import difflib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

from ..utils.file import FileManager


class VersionManager:
    """
    版本管理器
    管理文档版本和版本快照
    """
    
    def __init__(self, file_manager: FileManager):
        """
        初始化版本管理器
        :param file_manager: 文件管理器实例
        """
        self.file_manager = file_manager
        self.logger = logging.getLogger("docugen.version")
        
        # 当前记录的文档内容
        self.current_docs: Dict[str, str] = {}
        # 当前项目名称
        self.project_name: Optional[str] = None
    
    def set_project(self, project_name: str) -> None:
        """
        设置当前项目
        :param project_name: 项目名称
        """
        self.project_name = project_name
        self.logger.info(f"设置当前项目: {project_name}")
    
    def add_document(self, doc_type: str, content: str) -> None:
        """
        添加文档到当前版本
        :param doc_type: 文档类型
        :param content: 文档内容
        """
        if not self.project_name:
            self.logger.error("未设置项目名称，无法添加文档")
            raise ValueError("未设置项目名称，请先调用set_project方法")
        
        self.current_docs[doc_type] = content
        self.logger.info(f"添加文档到当前版本: {doc_type}")
    
    def create_checkpoint(self, label: Optional[str] = None, comments: Optional[str] = None) -> str:
        """
        创建版本快照
        :param label: 版本标签，可选
        :param comments: 版本备注，可选
        :return: 版本ID (时间戳)
        """
        if not self.project_name:
            self.logger.error("未设置项目名称，无法创建版本快照")
            raise ValueError("未设置项目名称，请先调用set_project方法")
        
        if not self.current_docs:
            self.logger.warning("没有文档内容，无法创建版本快照")
            return ""
        
        # 生成版本ID (时间戳)
        version_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存所有文档到版本目录
        for doc_type, content in self.current_docs.items():
            self.file_manager.save_document(self.project_name, doc_type, content)
        
        # 创建版本快照
        version_dir = self.file_manager.create_version_snapshot(self.project_name, version_id)
        if version_dir:
            self.logger.info(f"创建版本快照成功: {version_id}")
            # 保存版本元数据，添加标签和备注
            self._save_version_metadata(version_id, label, comments)
            return version_id
        else:
            self.logger.error(f"创建版本快照失败: {version_id}")
            return ""
    
    def _save_version_metadata(self, version_id: str, label: Optional[str] = None, comments: Optional[str] = None) -> None:
        """
        保存版本元数据
        :param version_id: 版本ID
        :param label: 版本标签，可选
        :param comments: 版本备注，可选
        """
        metadata = {
            "version_id": version_id,
            "created_at": datetime.now().isoformat(),
            "doc_types": list(self.current_docs.keys()),
            "project_name": self.project_name
        }
        
        # 添加标签和备注
        if label:
            metadata["label"] = label
        if comments:
            metadata["comments"] = comments
        
        # 构建元数据文件路径
        metadata_path = Path(self.file_manager.output_dir) / self.project_name / "versions" / version_id / "metadata.json"
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            self.logger.info(f"版本元数据保存成功: {metadata_path}")
        except Exception as e:
            self.logger.error(f"保存版本元数据失败: {str(e)}")
    
    def list_versions(self) -> List[Dict[str, Any]]:
        """
        列出项目的所有版本
        :return: 版本信息列表
        """
        if not self.project_name:
            self.logger.error("未设置项目名称，无法列出版本")
            raise ValueError("未设置项目名称，请先调用set_project方法")
        
        versions = self.file_manager.list_versions(self.project_name)
        version_info = []
        
        for version_id in versions:
            metadata_path = Path(self.file_manager.output_dir) / self.project_name / "versions" / version_id / "metadata.json"
            
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    version_info.append(metadata)
                except Exception as e:
                    self.logger.error(f"读取版本元数据失败 {version_id}: {str(e)}")
                    # 添加基本信息
                    version_info.append({
                        "version_id": version_id,
                        "created_at": "未知",
                        "project_name": self.project_name
                    })
            else:
                # 元数据文件不存在，添加基本信息
                version_info.append({
                    "version_id": version_id,
                    "created_at": "未知",
                    "project_name": self.project_name
                })
        
        return version_info
    
    def load_version(self, version_id: str) -> Dict[str, str]:
        """
        加载指定版本的文档
        :param version_id: 版本ID
        :return: 文档内容字典
        """
        if not self.project_name:
            self.logger.error("未设置项目名称，无法加载版本")
            raise ValueError("未设置项目名称，请先调用set_project方法")
        
        documents = self.file_manager.load_version(self.project_name, version_id)
        
        if documents:
            self.logger.info(f"成功加载版本: {version_id}")
            # 更新当前文档
            self.current_docs = documents
        else:
            self.logger.warning(f"版本加载失败或版本为空: {version_id}")
        
        return documents
    
    def revert_to_version(self, version_id: str) -> bool:
        """
        回滚到指定版本
        :param version_id: 要回滚到的版本ID
        :return: 是否回滚成功
        """
        if not self.project_name:
            self.logger.error("未设置项目名称，无法回滚版本")
            raise ValueError("未设置项目名称，请先调用set_project方法")
        
        # 加载要回滚的版本
        documents = self.load_version(version_id)
        
        if not documents:
            self.logger.error(f"回滚失败，无法加载版本: {version_id}")
            return False
        
        # 保存加载的文档到当前目录，完成回滚
        for doc_type, content in documents.items():
            self.file_manager.save_document(self.project_name, doc_type, content)
        
        self.logger.info(f"成功回滚到版本: {version_id}")
        return True
    
    def compare_versions(self, version_id1: str, version_id2: str) -> Dict[str, Dict[str, Union[bool, int, List[str]]]]:
        """
        比较两个版本的差异，增强版本比较功能
        :param version_id1: 第一个版本ID
        :param version_id2: 第二个版本ID
        :return: 差异信息
        """
        if not self.project_name:
            self.logger.error("未设置项目名称，无法比较版本")
            raise ValueError("未设置项目名称，请先调用set_project方法")
        
        # 加载两个版本的文档
        docs1 = self.file_manager.load_version(self.project_name, version_id1)
        docs2 = self.file_manager.load_version(self.project_name, version_id2)
        
        # 比较结果
        comparison = {}
        
        # 获取所有文档类型
        all_doc_types = set(list(docs1.keys()) + list(docs2.keys()))
        
        for doc_type in all_doc_types:
            content1 = docs1.get(doc_type, "")
            content2 = docs2.get(doc_type, "")
            
            # 检查文档是否存在于两个版本中
            exists_in_both = doc_type in docs1 and doc_type in docs2
            
            # 简单比较内容差异
            lines1 = content1.split("\n") if content1 else []
            lines2 = content2.split("\n") if content2 else []
            
            # 计算行数差异
            line_diff = len(lines2) - len(lines1)
            
            # 详细差异分析
            diff_details = []
            
            if exists_in_both and content1 != content2:
                # 使用difflib进行更详细的差异比较
                diff = list(difflib.unified_diff(
                    lines1, lines2, 
                    fromfile=f'版本 {version_id1}',
                    tofile=f'版本 {version_id2}',
                    lineterm=''))
                
                if diff:
                    diff_details = diff[3:]  # 跳过头部信息
            
            comparison[doc_type] = {
                "exists_in_both": exists_in_both,
                "line_diff": line_diff,
                "diff_details": diff_details if exists_in_both else [],
                "is_new": not exists_in_both and doc_type in docs2,
                "is_deleted": not exists_in_both and doc_type in docs1
            }
        
        return comparison
    
    def get_version_details(self, version_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个版本的详细信息
        :param version_id: 版本ID
        :return: 版本详细信息
        """
        if not self.project_name:
            self.logger.error("未设置项目名称，无法获取版本详情")
            raise ValueError("未设置项目名称，请先调用set_project方法")
        
        # 构建元数据文件路径
        metadata_path = Path(self.file_manager.output_dir) / self.project_name / "versions" / version_id / "metadata.json"
        
        if not metadata_path.exists():
            self.logger.error(f"版本元数据不存在: {version_id}")
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 获取版本包含的文档列表
            documents = self.file_manager.load_version(self.project_name, version_id)
            doc_info = []
            
            for doc_type, content in documents.items():
                # 简单分析文档结构
                lines = content.split("\n")
                headings = []
                for line in lines:
                    if line.startswith("#"):
                        headings.append(line)
                
                doc_info.append({
                    "doc_type": doc_type,
                    "filename": self.file_manager._get_filename_for_doc_type(doc_type),
                    "headings": headings[:5],  # 只取前5个标题
                    "size": len(content)
                })
            
            # 增强版本信息
            metadata["documents"] = doc_info
            return metadata
            
        except Exception as e:
            self.logger.error(f"读取版本元数据失败: {str(e)}")
            return None
    
    def generate_version_report(self, format: str = "markdown") -> str:
        """
        生成版本历史报告
        :param format: 报告格式，支持"markdown"和"text"
        :return: 版本历史报告内容
        """
        if not self.project_name:
            self.logger.error("未设置项目名称，无法生成版本报告")
            raise ValueError("未设置项目名称，请先调用set_project方法")
        
        # 获取所有版本信息
        versions = self.list_versions()
        
        if not versions:
            return "没有找到任何版本记录。"
        
        if format == "markdown":
            return self._generate_markdown_report(versions)
        else:
            return self._generate_text_report(versions)
    
    def _generate_markdown_report(self, versions: List[Dict[str, Any]]) -> str:
        """
        生成Markdown格式的版本历史报告
        :param versions: 版本信息列表
        :return: Markdown格式的报告
        """
        report = [f"# {self.project_name} 版本历史报告", ""]
        
        # 添加版本汇总表格
        report.extend([
            "## 版本汇总",
            "",
            "| 版本ID | 标签 | 创建时间 | 文档数 |",
            "|--------|------|----------|--------|"
        ])
        
        for version in versions:
            version_id = version.get("version_id", "未知")
            label = version.get("label", "无标签")
            created_at = version.get("created_at", "未知")
            # 简化时间戳显示
            if isinstance(created_at, str) and len(created_at) > 16:
                created_at = created_at[:16].replace("T", " ")
            doc_count = len(version.get("doc_types", []))
            
            report.append(f"| {version_id} | {label} | {created_at} | {doc_count} |")
        
        report.append("")
        
        # 添加详细版本信息
        report.append("## 详细版本信息")
        report.append("")
        
        for version in versions:
            version_id = version.get("version_id", "未知")
            label = version.get("label", "无标签")
            created_at = version.get("created_at", "未知")
            # 简化时间戳显示
            if isinstance(created_at, str) and len(created_at) > 16:
                created_at = created_at[:16].replace("T", " ")
            comments = version.get("comments", "无备注")
            doc_types = version.get("doc_types", [])
            
            report.append(f"### 版本 {version_id}")
            report.append("")
            report.append(f"- **标签**: {label}")
            report.append(f"- **创建时间**: {created_at}")
            report.append(f"- **备注**: {comments}")
            report.append("")
            
            # 添加文档列表
            report.append("#### 包含文档")
            report.append("")
            for doc_type in doc_types:
                filename = self.file_manager._get_filename_for_doc_type(doc_type)
                report.append(f"- {filename} ({doc_type})")
            report.append("")
        
        return "\n".join(report)
    
    def _generate_text_report(self, versions: List[Dict[str, Any]]) -> str:
        """
        生成纯文本格式的版本历史报告
        :param versions: 版本信息列表
        :return: 纯文本格式的报告
        """
        report = [f"{self.project_name} 版本历史报告", "=" * 50, ""]
        
        # 添加版本汇总
        report.append("版本汇总:")
        report.append("-" * 50)
        
        for version in versions:
            version_id = version.get("version_id", "未知")
            label = version.get("label", "无标签")
            created_at = version.get("created_at", "未知")
            # 简化时间戳显示
            if isinstance(created_at, str) and len(created_at) > 16:
                created_at = created_at[:16].replace("T", " ")
            doc_count = len(version.get("doc_types", []))
            
            report.append(f"版本ID: {version_id}")
            report.append(f"标签: {label}")
            report.append(f"创建时间: {created_at}")
            report.append(f"文档数: {doc_count}")
            report.append("-" * 50)
        
        report.append("")
        
        # 添加详细版本信息
        report.append("详细版本信息:")
        report.append("=" * 50)
        report.append("")
        
        for version in versions:
            version_id = version.get("version_id", "未知")
            label = version.get("label", "无标签")
            created_at = version.get("created_at", "未知")
            # 简化时间戳显示
            if isinstance(created_at, str) and len(created_at) > 16:
                created_at = created_at[:16].replace("T", " ")
            comments = version.get("comments", "无备注")
            doc_types = version.get("doc_types", [])
            
            report.append(f"版本 {version_id}")
            report.append("-" * 30)
            report.append(f"标签: {label}")
            report.append(f"创建时间: {created_at}")
            report.append(f"备注: {comments}")
            report.append("")
            
            # 添加文档列表
            report.append("包含文档:")
            for doc_type in doc_types:
                filename = self.file_manager._get_filename_for_doc_type(doc_type)
                report.append(f"- {filename} ({doc_type})")
            report.append("")
            report.append("=" * 50)
            report.append("")
        
        return "\n".join(report)
    
    def export_version(self, version_id: str, export_dir: str) -> bool:
        """
        导出指定版本的所有文档到指定目录
        :param version_id: 版本ID
        :param export_dir: 导出目录
        :return: 是否导出成功
        """
        if not self.project_name:
            self.logger.error("未设置项目名称，无法导出版本")
            raise ValueError("未设置项目名称，请先调用set_project方法")
        
        # 加载要导出的版本
        documents = self.file_manager.load_version(self.project_name, version_id)
        
        if not documents:
            self.logger.error(f"导出失败，无法加载版本: {version_id}")
            return False
        
        # 确保导出目录存在
        export_path = Path(export_dir)
        try:
            export_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建导出目录失败: {str(e)}")
            return False
        
        # 导出所有文档
        try:
            for doc_type, content in documents.items():
                filename = self.file_manager._get_filename_for_doc_type(doc_type)
                file_path = export_path / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # 导出版本元数据
            metadata = self.get_version_details(version_id)
            if metadata:
                metadata_path = export_path / "版本信息.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"成功导出版本 {version_id} 到目录: {export_dir}")
            return True
        except Exception as e:
            self.logger.error(f"导出版本失败: {str(e)}")
            return False 