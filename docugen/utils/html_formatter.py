"""
HTML格式化器模块
负责将Markdown内容转换为HTML格式
"""

import logging
from typing import Dict, Any, Optional
import markdown
from pathlib import Path


class HTMLFormatter:
    """
    HTML格式化器
    将Markdown内容转换为HTML格式并支持样式定制
    """
    
    DEFAULT_CSS = """
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
        margin-top: 24px;
        margin-bottom: 16px;
        font-weight: 600;
        line-height: 1.25;
    }
    h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
    h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
    code {
        background-color: #f6f8fa;
        border-radius: 3px;
        padding: 0.2em 0.4em;
        font-family: monospace;
    }
    pre {
        background-color: #f6f8fa;
        border-radius: 3px;
        padding: 16px;
        overflow: auto;
        font-family: monospace;
    }
    blockquote {
        margin: 0;
        padding: 0 1em;
        color: #6a737d;
        border-left: 0.25em solid #dfe2e5;
    }
    ul, ol {
        padding-left: 2em;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 16px;
    }
    table th, table td {
        padding: 6px 13px;
        border: 1px solid #dfe2e5;
    }
    table tr:nth-child(2n) {
        background-color: #f6f8fa;
    }
    """
    
    def __init__(self, custom_css: Optional[str] = None):
        """
        初始化HTML格式化器
        
        :param custom_css: 自定义CSS样式，可选
        """
        self.logger = logging.getLogger("docugen.utils.html_formatter")
        
        # 使用Python-Markdown库的扩展
        self.markdown_extensions = [
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.meta'
        ]
        
        # CSS样式设置
        self.css = custom_css if custom_css else self.DEFAULT_CSS
    
    def convert_to_html(self, markdown_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        将Markdown内容转换为HTML
        
        :param markdown_content: Markdown格式内容
        :param metadata: 文档元数据，可选
        :return: HTML格式内容
        """
        self.logger.debug("开始将Markdown转换为HTML")
        
        # 使用Python-Markdown将内容转换为HTML
        try:
            html_body = markdown.markdown(
                markdown_content,
                extensions=self.markdown_extensions
            )
        except Exception as e:
            self.logger.error(f"Markdown转HTML失败: {str(e)}")
            html_body = f"<p>转换错误: {str(e)}</p>"
        
        # 构建完整HTML文档
        full_html = self._build_full_html(html_body, metadata)
        
        self.logger.debug("Markdown成功转换为HTML")
        return full_html
    
    def _build_full_html(self, html_body: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        构建完整的HTML文档，包括头部、样式和元数据
        
        :param html_body: HTML正文内容
        :param metadata: 文档元数据，可选
        :return: 完整的HTML文档
        """
        # 准备标题
        title = "DocuGen生成文档"
        if metadata and 'title' in metadata:
            title = metadata['title']
        
        # 构建HTML头部
        html_head = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{self.css}
    </style>
"""
        
        # 添加元数据
        if metadata:
            html_head += "    <!-- 文档元数据 -->\n"
            for key, value in metadata.items():
                if isinstance(value, str):
                    # 转义双引号
                    value = value.replace('"', "&quot;")
                    html_head += f'    <meta name="{key}" content="{value}">\n'
        
        html_head += "</head>\n<body>\n"
        
        # 构建完整HTML
        full_html = f"{html_head}{html_body}\n</body>\n</html>"
        
        return full_html
    
    def set_custom_css(self, custom_css: str) -> None:
        """
        设置自定义CSS样式
        
        :param custom_css: CSS样式内容
        """
        self.css = custom_css
    
    def load_css_file(self, css_file_path: str) -> bool:
        """
        从文件加载CSS样式
        
        :param css_file_path: CSS文件路径
        :return: 是否成功加载
        """
        css_path = Path(css_file_path)
        if not css_path.exists() or not css_path.is_file():
            self.logger.warning(f"CSS文件不存在: {css_file_path}")
            return False
        
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                self.css = f.read()
            self.logger.info(f"已加载CSS文件: {css_file_path}")
            return True
        except Exception as e:
            self.logger.error(f"加载CSS文件失败: {str(e)}")
            return False 