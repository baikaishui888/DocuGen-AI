"""
模板管理器模块
负责加载、验证和管理文档模板
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, List, Union
import json

import jinja2
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import Config


class TemplateManager:
    """
    模板管理器
    负责加载、验证和管理文档模板
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        初始化模板管理器
        
        Args:
            templates_dir: 模板目录路径，如未提供则使用配置中的默认路径
        """
        self.logger = logging.getLogger("docugen.template")
        self.config = Config()
        
        # 设置模板目录
        if templates_dir is None:
            templates_dir = self.config.get("paths.templates_dir", "templates")
        
        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            self.logger.warning(f"模板目录不存在: {self.templates_dir}，尝试创建")
            self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 缓存模板元数据
        self.template_metadata: Dict[str, Dict] = {}
        self._load_all_templates()
    
    def _load_all_templates(self) -> None:
        """加载所有模板及其元数据"""
        self.logger.info("加载所有模板文件")
        
        for template_file in self.templates_dir.glob("**/*.j2"):
            template_name = str(template_file.relative_to(self.templates_dir))
            self._load_template_metadata(template_name)
    
    def _load_template_metadata(self, template_name: str) -> Dict:
        """
        加载模板的元数据
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板元数据字典
        """
        # 构建元数据文件路径（与模板同名但扩展名为.json）
        template_path = self.templates_dir / template_name
        metadata_path = template_path.with_suffix('.json')
        
        metadata = {
            "name": template_name,
            "description": "",
            "version": "1.0.0",
            "required_variables": [],
            "optional_variables": []
        }
        
        # 如果存在元数据文件，则加载
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    file_metadata = json.load(f)
                    metadata.update(file_metadata)
            except Exception as e:
                self.logger.error(f"加载模板元数据失败 {template_name}: {str(e)}")
        
        # 缓存元数据
        self.template_metadata[template_name] = metadata
        return metadata
    
    def get_template(self, template_name: str) -> jinja2.Template:
        """
        获取指定名称的模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            Jinja2模板对象
            
        Raises:
            ValueError: 如果模板不存在
        """
        try:
            return self.env.get_template(template_name)
        except jinja2.exceptions.TemplateNotFound:
            self.logger.error(f"模板不存在: {template_name}")
            raise ValueError(f"模板不存在: {template_name}")
    
    def render_template(self, template_name: str, context: Dict) -> str:
        """
        渲染指定的模板
        
        Args:
            template_name: 模板名称
            context: 模板渲染上下文（变量）
            
        Returns:
            渲染后的内容
            
        Raises:
            ValueError: 如果模板不存在或缺少必要变量
        """
        # 获取模板
        template = self.get_template(template_name)
        
        # 检查必要变量是否提供
        if template_name in self.template_metadata:
            metadata = self.template_metadata[template_name]
            required_vars = metadata.get("required_variables", [])
            
            missing_vars = [var for var in required_vars if var not in context]
            if missing_vars:
                self.logger.error(f"模板 {template_name} 缺少必要变量: {', '.join(missing_vars)}")
                raise ValueError(f"模板 {template_name} 缺少必要变量: {', '.join(missing_vars)}")
        
        # 渲染模板
        try:
            return template.render(**context)
        except Exception as e:
            self.logger.error(f"渲染模板失败 {template_name}: {str(e)}")
            raise ValueError(f"渲染模板失败: {str(e)}")
    
    def list_templates(self, category: Optional[str] = None) -> List[str]:
        """
        列出可用的模板
        
        Args:
            category: 可选的模板类别过滤
            
        Returns:
            模板名称列表
        """
        if category:
            return [
                name for name, meta in self.template_metadata.items()
                if meta.get("category") == category
            ]
        return list(self.template_metadata.keys())
    
    def get_template_metadata(self, template_name: str) -> Dict:
        """
        获取模板的元数据
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板元数据
            
        Raises:
            ValueError: 如果模板不存在
        """
        if template_name not in self.template_metadata:
            self.logger.error(f"模板不存在: {template_name}")
            raise ValueError(f"模板不存在: {template_name}")
        
        return self.template_metadata[template_name]
    
    def create_template(self, template_name: str, content: str, metadata: Optional[Dict] = None) -> None:
        """
        创建新的模板
        
        Args:
            template_name: 模板名称
            content: 模板内容
            metadata: 可选的模板元数据
            
        Raises:
            ValueError: 如果模板已存在
        """
        template_path = self.templates_dir / template_name
        
        # 检查是否已存在
        if template_path.exists():
            self.logger.error(f"模板已存在: {template_name}")
            raise ValueError(f"模板已存在: {template_name}")
        
        # 确保目录存在
        template_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入模板内容
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 写入元数据（如果提供）
        if metadata:
            default_metadata = {
                "name": template_name,
                "description": "",
                "version": "1.0.0",
                "required_variables": [],
                "optional_variables": []
            }
            default_metadata.update(metadata)
            
            metadata_path = template_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(default_metadata, f, ensure_ascii=False, indent=2)
            
            # 更新缓存的元数据
            self.template_metadata[template_name] = default_metadata
        
        self.logger.info(f"创建模板成功: {template_name}")
        
        # 重新加载模板环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def update_template(self, template_name: str, content: str, metadata: Optional[Dict] = None) -> None:
        """
        更新现有模板
        
        Args:
            template_name: 模板名称
            content: 新的模板内容
            metadata: 可选的新元数据
            
        Raises:
            ValueError: 如果模板不存在
        """
        template_path = self.templates_dir / template_name
        
        # 检查是否存在
        if not template_path.exists():
            self.logger.error(f"模板不存在: {template_name}")
            raise ValueError(f"模板不存在: {template_name}")
        
        # 更新模板内容
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 更新元数据（如果提供）
        if metadata:
            current_metadata = self.template_metadata.get(template_name, {})
            current_metadata.update(metadata)
            
            metadata_path = template_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(current_metadata, f, ensure_ascii=False, indent=2)
            
            # 更新缓存的元数据
            self.template_metadata[template_name] = current_metadata
        
        self.logger.info(f"更新模板成功: {template_name}") 