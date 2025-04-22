"""
PDF生成器模块
负责将HTML内容转换为PDF格式
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
import tempfile
from weasyprint import HTML, CSS


class PDFGenerator:
    """
    PDF生成器
    将HTML内容转换为PDF格式并提供导出功能
    """
    
    def __init__(self, custom_css: Optional[str] = None):
        """
        初始化PDF生成器
        
        :param custom_css: 自定义CSS样式，可选
        """
        self.logger = logging.getLogger("docugen.utils.pdf_generator")
        self.custom_css = custom_css
    
    def generate_pdf_from_html(self, html_content: str) -> bytes:
        """
        根据HTML内容生成PDF
        
        :param html_content: HTML格式内容
        :return: PDF二进制内容
        """
        self.logger.debug("开始将HTML转换为PDF")
        
        try:
            # 使用WeasyPrint将HTML转换为PDF
            html = HTML(string=html_content)
            
            # 应用自定义样式(如果有)
            if self.custom_css:
                css = CSS(string=self.custom_css)
                pdf_content = html.write_pdf(stylesheets=[css])
            else:
                pdf_content = html.write_pdf()
            
            self.logger.debug("HTML成功转换为PDF")
            return pdf_content
            
        except Exception as e:
            self.logger.error(f"HTML转PDF失败: {str(e)}")
            raise
    
    def generate_pdf_from_html_file(self, html_file_path: Union[str, Path]) -> bytes:
        """
        从HTML文件生成PDF
        
        :param html_file_path: HTML文件路径
        :return: PDF二进制内容
        """
        html_path = Path(html_file_path)
        if not html_path.exists() or not html_path.is_file():
            raise FileNotFoundError(f"HTML文件不存在: {html_file_path}")
        
        self.logger.debug(f"从HTML文件生成PDF: {html_file_path}")
        
        try:
            # 使用WeasyPrint从文件生成PDF
            html = HTML(filename=str(html_path))
            
            # 应用自定义样式(如果有)
            if self.custom_css:
                css = CSS(string=self.custom_css)
                pdf_content = html.write_pdf(stylesheets=[css])
            else:
                pdf_content = html.write_pdf()
            
            self.logger.debug("HTML文件成功转换为PDF")
            return pdf_content
            
        except Exception as e:
            self.logger.error(f"HTML文件转PDF失败: {str(e)}")
            raise
    
    def save_pdf_to_file(self, pdf_content: bytes, output_path: Union[str, Path]) -> str:
        """
        将PDF内容保存到文件
        
        :param pdf_content: PDF二进制内容
        :param output_path: 输出文件路径
        :return: 输出文件的绝对路径
        """
        output_file = Path(output_path)
        output_dir = output_file.parent
        
        # 确保输出目录存在
        if not output_dir.exists():
            self.logger.info(f"创建输出目录: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        try:
            with open(output_file, 'wb') as f:
                f.write(pdf_content)
            self.logger.info(f"PDF内容成功保存到: {output_file}")
            return str(output_file.absolute())
        except Exception as e:
            self.logger.error(f"保存PDF内容失败: {str(e)}")
            raise
    
    def generate_and_save_pdf(self, html_content: str, output_path: Union[str, Path]) -> str:
        """
        生成PDF并保存到文件
        
        :param html_content: HTML格式内容
        :param output_path: 输出文件路径
        :return: 输出文件的绝对路径
        """
        pdf_content = self.generate_pdf_from_html(html_content)
        return self.save_pdf_to_file(pdf_content, output_path)
    
    def set_custom_css(self, custom_css: str) -> None:
        """
        设置自定义CSS样式
        
        :param custom_css: CSS样式内容
        """
        self.custom_css = custom_css
    
    def load_css_file(self, css_file_path: Union[str, Path]) -> bool:
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
                self.custom_css = f.read()
            self.logger.info(f"已加载CSS文件: {css_file_path}")
            return True
        except Exception as e:
            self.logger.error(f"加载CSS文件失败: {str(e)}")
            return False 