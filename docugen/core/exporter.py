"""
文档导出器模块
负责将生成的文档内容转换为不同格式并导出
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from docugen.utils.html_formatter import HTMLFormatter
from docugen.utils.pdf_generator import PDFGenerator


class MarkdownExporter:
    """
    Markdown格式导出器
    将文档内容标准化为Markdown格式并导出
    """
    
    def __init__(self):
        """初始化Markdown导出器"""
        self.logger = logging.getLogger("docugen.exporter.markdown")
    
    def format(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        格式化Markdown内容
        - 规范化标题层级
        - 标准化列表格式
        - 确保代码块格式正确
        - 添加元数据（如果提供）
        
        :param content: 原始Markdown内容
        :param metadata: 文档元数据，可选
        :return: 格式化后的Markdown内容
        """
        self.logger.debug("开始格式化Markdown内容")
        
        # 如果内容为空，返回空字符串
        if not content or not content.strip():
            self.logger.warning("内容为空，无法格式化")
            return ""
        
        # 规范化内容
        formatted_content = self._normalize_content(content)
        
        # 如果有元数据，添加到文档头部
        if metadata and isinstance(metadata, dict):
            formatted_content = self._add_metadata(formatted_content, metadata)
        
        self.logger.debug("Markdown内容格式化完成")
        return formatted_content
    
    def export(self, content: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        导出Markdown内容到文件
        
        :param content: Markdown内容
        :param output_path: 输出文件路径
        :param metadata: 文档元数据，可选
        :return: 输出文件的绝对路径
        """
        # 格式化内容
        formatted_content = self.format(content, metadata)
        
        # 确保输出目录存在
        output_file = Path(output_path)
        output_dir = output_file.parent
        
        if not output_dir.exists():
            self.logger.info(f"创建输出目录: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            self.logger.info(f"Markdown内容成功导出到: {output_file}")
            return str(output_file.absolute())
        except Exception as e:
            self.logger.error(f"导出Markdown内容失败: {str(e)}")
            raise
    
    def _normalize_content(self, content: str) -> str:
        """
        规范化Markdown内容
        
        :param content: 原始Markdown内容
        :return: 规范化后的内容
        """
        lines = content.split('\n')
        normalized_lines = []
        
        # 处理每一行
        for line in lines:
            # 确保标题与#之间有空格
            if line.strip().startswith('#'):
                for i in range(6, 0, -1):  # 从h6到h1检查
                    prefix = '#' * i
                    if line.strip().startswith(prefix) and not line.strip().startswith(prefix + ' '):
                        line = line.replace(prefix, prefix + ' ', 1)
                        break
            
            # 确保列表项与内容之间有空格
            if line.strip().startswith(('-', '*', '+')) and len(line.strip()) > 1:
                list_marker = line.strip()[0]
                if line.strip()[1] != ' ':
                    line = line.replace(list_marker, list_marker + ' ', 1)
            
            # 确保有序列表项与内容之间有空格
            if line.strip() and line.strip()[0].isdigit() and '.' in line.strip()[:3]:
                number_part = line.strip().split('.')[0]
                if number_part.isdigit() and line.strip()[len(number_part)+1] != ' ':
                    line = line.replace(number_part + '.', number_part + '. ', 1)
            
            normalized_lines.append(line)
        
        # 确保文档末尾有一个空行
        if normalized_lines and normalized_lines[-1].strip():
            normalized_lines.append('')
        
        return '\n'.join(normalized_lines)
    
    def _add_metadata(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        在Markdown内容前添加YAML格式的元数据
        
        :param content: Markdown内容
        :param metadata: 元数据字典
        :return: 添加了元数据的内容
        """
        yaml_lines = ['---']
        
        for key, value in metadata.items():
            # 处理简单类型
            if isinstance(value, (str, int, float, bool)):
                yaml_lines.append(f"{key}: {value}")
            # 处理列表
            elif isinstance(value, list):
                yaml_lines.append(f"{key}:")
                for item in value:
                    yaml_lines.append(f"  - {item}")
            # 处理字典
            elif isinstance(value, dict):
                yaml_lines.append(f"{key}:")
                for k, v in value.items():
                    yaml_lines.append(f"  {k}: {v}")
        
        yaml_lines.append('---')
        yaml_lines.append('')  # 空行分隔元数据和内容
        
        return '\n'.join(yaml_lines) + content


class HTMLExporter:
    """
    HTML格式导出器
    将Markdown内容转换为HTML格式并导出
    """
    
    def __init__(self, custom_css: Optional[str] = None):
        """
        初始化HTML导出器
        
        :param custom_css: 自定义CSS样式，可选
        """
        self.logger = logging.getLogger("docugen.exporter.html")
        self.html_formatter = HTMLFormatter(custom_css)
    
    def convert(self, markdown_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        将Markdown内容转换为HTML
        
        :param markdown_content: Markdown格式内容
        :param metadata: 文档元数据，可选
        :return: HTML格式内容
        """
        self.logger.debug("开始转换Markdown到HTML")
        
        if not markdown_content or not markdown_content.strip():
            self.logger.warning("内容为空，无法转换")
            return ""
        
        html_content = self.html_formatter.convert_to_html(markdown_content, metadata)
        
        self.logger.debug("Markdown到HTML转换完成")
        return html_content
    
    def export(self, markdown_content: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        将Markdown内容转换为HTML并导出到文件
        
        :param markdown_content: Markdown格式内容
        :param output_path: 输出文件路径
        :param metadata: 文档元数据，可选
        :return: 输出文件的绝对路径
        """
        # 转换为HTML
        html_content = self.convert(markdown_content, metadata)
        
        # 确保输出目录存在
        output_file = Path(output_path)
        output_dir = output_file.parent
        
        if not output_dir.exists():
            self.logger.info(f"创建输出目录: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"HTML内容成功导出到: {output_file}")
            return str(output_file.absolute())
        except Exception as e:
            self.logger.error(f"导出HTML内容失败: {str(e)}")
            raise
    
    def set_custom_css(self, custom_css: str) -> None:
        """
        设置自定义CSS样式
        
        :param custom_css: CSS样式内容
        """
        self.html_formatter.set_custom_css(custom_css)
    
    def load_css_file(self, css_file_path: str) -> bool:
        """
        从文件加载CSS样式
        
        :param css_file_path: CSS文件路径
        :return: 是否成功加载
        """
        return self.html_formatter.load_css_file(css_file_path)


class PDFExporter:
    """
    PDF格式导出器
    将Markdown或HTML内容转换为PDF格式并导出
    """
    
    def __init__(self, custom_css: Optional[str] = None, html_exporter: Optional[HTMLExporter] = None):
        """
        初始化PDF导出器
        
        :param custom_css: 自定义CSS样式，可选
        :param html_exporter: HTML导出器实例，如果为None则创建新实例
        """
        self.logger = logging.getLogger("docugen.exporter.pdf")
        self.pdf_generator = PDFGenerator(custom_css)
        
        # 如果没有提供HTML导出器，创建一个新的
        self.html_exporter = html_exporter if html_exporter else HTMLExporter(custom_css)
    
    def export_from_markdown(self, markdown_content: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        将Markdown内容转换为PDF并导出
        
        :param markdown_content: Markdown格式内容
        :param output_path: 输出文件路径
        :param metadata: 文档元数据，可选
        :return: 输出文件的绝对路径
        """
        self.logger.debug("开始从Markdown生成PDF")
        
        # 先转换为HTML
        html_content = self.html_exporter.convert(markdown_content, metadata)
        
        # 使用PDF生成器生成PDF
        try:
            result_path = self.pdf_generator.generate_and_save_pdf(html_content, output_path)
            self.logger.info(f"PDF内容成功导出到: {result_path}")
            return result_path
        except Exception as e:
            self.logger.error(f"Markdown转PDF导出失败: {str(e)}")
            raise
    
    def export_from_html(self, html_content: str, output_path: str) -> str:
        """
        将HTML内容转换为PDF并导出
        
        :param html_content: HTML格式内容
        :param output_path: 输出文件路径
        :return: 输出文件的绝对路径
        """
        self.logger.debug("开始从HTML生成PDF")
        
        # 使用PDF生成器生成PDF
        try:
            result_path = self.pdf_generator.generate_and_save_pdf(html_content, output_path)
            self.logger.info(f"PDF内容成功导出到: {result_path}")
            return result_path
        except Exception as e:
            self.logger.error(f"HTML转PDF导出失败: {str(e)}")
            raise
    
    def export_from_html_file(self, html_file_path: str, output_path: str) -> str:
        """
        将HTML文件转换为PDF并导出
        
        :param html_file_path: HTML文件路径
        :param output_path: 输出文件路径
        :return: 输出文件的绝对路径
        """
        self.logger.debug(f"开始从HTML文件生成PDF: {html_file_path}")
        
        try:
            # 生成PDF内容
            pdf_content = self.pdf_generator.generate_pdf_from_html_file(html_file_path)
            
            # 保存到文件
            result_path = self.pdf_generator.save_pdf_to_file(pdf_content, output_path)
            self.logger.info(f"PDF内容成功导出到: {result_path}")
            return result_path
        except Exception as e:
            self.logger.error(f"HTML文件转PDF导出失败: {str(e)}")
            raise
    
    def set_custom_css(self, custom_css: str) -> None:
        """
        设置自定义CSS样式
        
        :param custom_css: CSS样式内容
        """
        self.pdf_generator.set_custom_css(custom_css)
        self.html_exporter.set_custom_css(custom_css)
    
    def load_css_file(self, css_file_path: str) -> bool:
        """
        从文件加载CSS样式
        
        :param css_file_path: CSS文件路径
        :return: 是否成功加载
        """
        result = self.pdf_generator.load_css_file(css_file_path)
        if result:
            # 同时设置HTML导出器的CSS样式
            self.html_exporter.set_custom_css(self.pdf_generator.custom_css)
        return result


class DocumentExporter:
    """
    文档导出器
    集中管理各种格式的导出功能
    """
    
    def __init__(self, custom_css: Optional[str] = None):
        """
        初始化文档导出器
        
        :param custom_css: 自定义CSS样式，可选，用于HTML和PDF输出
        """
        self.logger = logging.getLogger("docugen.exporter")
        self.markdown_exporter = MarkdownExporter()
        self.html_exporter = HTMLExporter(custom_css)
        self.pdf_exporter = PDFExporter(custom_css, self.html_exporter)
    
    def export_markdown(self, content: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        导出为Markdown格式
        
        :param content: 文档内容
        :param output_path: 输出路径
        :param metadata: 文档元数据，可选
        :return: 输出文件的路径
        """
        return self.markdown_exporter.export(content, output_path, metadata)
    
    def format_markdown(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        格式化Markdown内容但不导出
        
        :param content: 原始Markdown内容
        :param metadata: 文档元数据，可选
        :return: 格式化后的Markdown内容
        """
        return self.markdown_exporter.format(content, metadata)
    
    def export_html(self, content: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        导出为HTML格式
        
        :param content: Markdown格式内容
        :param output_path: 输出路径
        :param metadata: 文档元数据，可选
        :return: 输出文件的路径
        """
        return self.html_exporter.export(content, output_path, metadata)
    
    def convert_to_html(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        将Markdown内容转换为HTML但不导出
        
        :param content: Markdown格式内容
        :param metadata: 文档元数据，可选
        :return: HTML格式内容
        """
        return self.html_exporter.convert(content, metadata)
    
    def export_pdf(self, content: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        导出为PDF格式
        
        :param content: Markdown格式内容
        :param output_path: 输出路径
        :param metadata: 文档元数据，可选
        :return: 输出文件的路径
        """
        return self.pdf_exporter.export_from_markdown(content, output_path, metadata)
    
    def export_html_to_pdf(self, html_content: str, output_path: str) -> str:
        """
        将HTML内容导出为PDF格式
        
        :param html_content: HTML格式内容
        :param output_path: 输出路径
        :return: 输出文件的路径
        """
        return self.pdf_exporter.export_from_html(html_content, output_path)
    
    def export_html_file_to_pdf(self, html_file_path: str, output_path: str) -> str:
        """
        将HTML文件导出为PDF格式
        
        :param html_file_path: HTML文件路径
        :param output_path: 输出路径
        :return: 输出文件的路径
        """
        return self.pdf_exporter.export_from_html_file(html_file_path, output_path)
    
    def set_html_css(self, custom_css: str) -> None:
        """
        设置HTML输出的CSS样式
        
        :param custom_css: CSS样式内容
        """
        self.html_exporter.set_custom_css(custom_css)
    
    def set_pdf_css(self, custom_css: str) -> None:
        """
        设置PDF输出的CSS样式
        
        :param custom_css: CSS样式内容
        """
        self.pdf_exporter.set_custom_css(custom_css)
    
    def set_all_css(self, custom_css: str) -> None:
        """
        同时设置HTML和PDF输出的CSS样式
        
        :param custom_css: CSS样式内容
        """
        self.html_exporter.set_custom_css(custom_css)
        self.pdf_exporter.set_custom_css(custom_css)
    
    def load_html_css_file(self, css_file_path: str) -> bool:
        """
        从文件加载HTML输出的CSS样式
        
        :param css_file_path: CSS文件路径
        :return: 是否成功加载
        """
        return self.html_exporter.load_css_file(css_file_path)
    
    def load_pdf_css_file(self, css_file_path: str) -> bool:
        """
        从文件加载PDF输出的CSS样式
        
        :param css_file_path: CSS文件路径
        :return: 是否成功加载
        """
        return self.pdf_exporter.load_css_file(css_file_path) 