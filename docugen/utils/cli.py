#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
命令行交互界面模块
提供用户交互功能和界面展示
"""

import os
import sys
import logging
import platform
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax

from docugen.utils.i18n import i18n, _

# 创建控制台实例
console = Console()

class CommandLineInterface:
    """命令行交互界面类"""
    
    def __init__(self, enable_color: bool = True):
        """初始化命令行界面
        
        Args:
            enable_color: 是否启用彩色输出
        """
        self.console = Console(highlight=enable_color)
        self.logger = logging.getLogger("docugen.cli")
    
    def show_title(self):
        """显示应用标题"""
        title = Panel(
            f"[bold blue]{_('ui.title')}[/bold blue]",
            subtitle="v1.0",
            border_style="blue"
        )
        self.console.print(title)
        self.console.print("-" * 60)
    
    def show_welcome(self):
        """显示欢迎信息"""
        self.show_title()
        self.console.print(_("ui.welcome_message", "[bold]欢迎使用 DocuGen AI - 智能文档生成助手[/bold]"))
        self.console.print(_("ui.start_guide", "开始使用文档生成工具...\n"))
    
    def show_version(self):
        """显示版本信息"""
        from docugen import __version__
        self.console.print(f"DocuGen AI v{__version__}")
    
    def get_input(self, prompt: str, default: str = None) -> str:
        """获取用户输入
        
        Args:
            prompt: 提示文本
            default: 默认值
            
        Returns:
            用户输入的文本
        """
        # 检查提示文本是否是翻译键
        if prompt.startswith("ui."):
            prompt = _(prompt)
        return Prompt.ask(prompt, default=default)
    
    def confirm(self, prompt: str, default: bool = True) -> bool:
        """获取用户确认
        
        Args:
            prompt: 提示文本
            default: 默认值
            
        Returns:
            用户确认结果
        """
        # 检查提示文本是否是翻译键
        if prompt.startswith("ui."):
            prompt = _(prompt)
        return Confirm.ask(prompt, default=default)
    
    def show_status(self, message: str, success: bool = True):
        """显示状态信息
        
        Args:
            message: 状态信息
            success: 是否成功
        """
        icon = "✓" if success else "✗"
        style = "green" if success else "red"
        
        # 检查消息是否是翻译键
        if message.startswith("ui.") or message.startswith("status."):
            message = _(message)
            
        self.console.print(f"[bold {style}]{icon}[/bold {style}] {message}")
    
    def show_success(self, message: str):
        """显示成功信息
        
        Args:
            message: 成功信息
        """
        # 检查消息是否是翻译键
        if message.startswith("ui.") or message.startswith("status."):
            message = _(message)
            
        self.console.print(f"[bold green]✓ {_('ui.success')}:[/bold green] {message}")
    
    def show_generating_prompt(self, project_name: str):
        """显示文档生成开始的提示
        
        Args:
            project_name: 项目名称
        """
        self.console.print(f"[bold]{_('ui.generating_prompt', f'正在为项目 [cyan]{project_name}[/cyan] 生成文档...')}[/bold]")
    
    def show_warning(self, message: str):
        """显示警告信息
        
        Args:
            message: 警告信息
        """
        # 检查消息是否是翻译键
        if message.startswith("ui.") or message.startswith("errors."):
            message = _(message)
            
        self.console.print(f"[bold yellow]! {_('ui.warning')}:[/bold yellow] {message}")
    
    def show_error(self, message: str, error_code: Optional[int] = None):
        """显示错误信息
        
        Args:
            message: 错误信息
            error_code: 错误代码
        """
        # 检查消息是否是翻译键
        if message.startswith("ui.") or message.startswith("errors."):
            message = _(message)
            
        if error_code:
            self.console.print(f"[bold red]✗ {_('ui.error')} [{error_code}]:[/bold red] {message}")
        else:
            self.console.print(f"[bold red]✗ {_('ui.error')}:[/bold red] {message}")
    
    def show_menu(self, options: List[str], title: str = "请选择操作") -> int:
        """显示菜单并获取用户选择
        
        Args:
            options: 选项列表
            title: 菜单标题
            
        Returns:
            用户选择的选项索引(从1开始)
        """
        # 翻译菜单标题
        if title.startswith("ui."):
            title = _(title)
            
        # 翻译选项
        translated_options = []
        for option in options:
            if option.startswith("ui.") or option.startswith("documents."):
                translated_options.append(_(option))
            else:
                translated_options.append(option)
                
        self.console.print(f"[bold]{title}[/bold]")
        for i, option in enumerate(translated_options, 1):
            self.console.print(f"{i}. {option}")
        
        while True:
            try:
                choice = int(self.get_input(_("ui.enter_option_number", "请输入选项编号")))
                if 1 <= choice <= len(options):
                    return choice
                self.show_warning(_("ui.invalid_option_range", f"请输入1-{len(options)}之间的数字"))
            except ValueError:
                self.show_warning(_("ui.invalid_number", "请输入有效的数字"))
    
    def create_progress_bar(self, total: int, description: str = "进度") -> Progress:
        """创建进度条
        
        Args:
            total: 总步骤数
            description: 进度条描述
            
        Returns:
            进度条对象
        """
        # 翻译描述
        if description.startswith("ui.") or description.startswith("status."):
            description = _(description)
            
        return Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )
        
    def progress_display(self):
        """创建进度显示上下文管理器
        
        Returns:
            Progress对象作为上下文管理器
        """
        return Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )
    
    def progress_bar(self):
        """创建进度条上下文管理器
        
        Returns:
            Progress对象作为上下文管理器
        """
        return Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console
        )
    
    def show_document_list(self, documents: List[Dict[str, Any]], title: str = "文档列表"):
        """显示文档列表
        
        Args:
            documents: 文档列表，每个文档包含name和status字段
            title: 表格标题
        """
        # 翻译标题
        if title.startswith("ui."):
            title = _(title)
            
        table = Table(title=title)
        table.add_column(_("ui.document_name", "文档名称"), style="cyan")
        table.add_column(_("ui.status", "状态"), justify="center")
        
        for doc in documents:
            # 获取文档名称并尝试翻译
            name = doc["name"]
            if name.startswith("documents."):
                name = _(name)
                
            status = doc["status"]
            
            # 状态图标
            if status == "success":
                status_text = Text("✓", style="green")
            elif status == "failed":
                status_text = Text("✗", style="red")
            elif status == "pending":
                status_text = Text("○", style="yellow")
            else:
                # 尝试翻译状态
                if status.startswith("status."):
                    status_text = Text(_(status))
                else:
                    status_text = Text(status)
                
            table.add_row(name, status_text)
            
        self.console.print(table)
    
    def show_file_summary(self, path: str, count: int):
        """显示文件生成摘要
        
        Args:
            path: 文件路径
            count: 文件数量
        """
        panel = Panel(
            _("ui.generated_files_message", f"已生成 [green]{count}[/green] 个文档文件\n"
            f"保存路径: [blue]{path}[/blue]"),
            title=_("ui.generation_complete", "文档生成完成"),
            border_style="green"
        )
        self.console.print(panel)
    
    def ask(self, prompt: str, default: str = None) -> str:
        """获取用户输入（get_input的别名）
        
        Args:
            prompt: 提示文本
            default: 默认值
            
        Returns:
            用户输入的文本
        """
        return self.get_input(prompt, default)
    
    def show_language_menu(self) -> str:
        """显示语言选择菜单
        
        Returns:
            选择的语言代码
        """
        # 获取支持的语言
        languages = i18n.get_supported_languages()
        options = list(languages.values())
        codes = list(languages.keys())
        
        # 当前语言
        current_lang = i18n.get_current_language()
        current_index = codes.index(current_lang) if current_lang in codes else 0
        
        self.console.print(f"[bold]{_('ui.current_language', '当前语言')}: [cyan]{languages[current_lang]}[/cyan][/bold]")
        
        # 显示语言选择菜单
        choice = self.show_menu(options, _("ui.select_language", "请选择语言"))
        selected_code = codes[choice - 1]
        
        # 切换语言
        if selected_code != current_lang:
            i18n.switch_language(selected_code)
            self.show_status(_("ui.language_switched", f"已切换到{languages[selected_code]}"), success=True)
            
        return selected_code
    
    def clear(self):
        """清空控制台"""
        if sys.platform == "win32":
            # Windows
            os.system("cls")
        else:
            # Unix/Linux/MacOS
            os.system("clear")

    def input_text_optional(self, prompt: str, allow_empty: bool = True) -> Optional[str]:
        """获取可选的文本输入，允许为空
        
        Args:
            prompt: 提示文本
            allow_empty: 是否允许空输入
            
        Returns:
            用户输入的文本，如果用户直接按回车且allow_empty为True，则返回None
        """
        # 检查提示文本是否是翻译键
        if prompt.startswith("ui."):
            prompt = _(prompt)
            
        result = Prompt.ask(prompt, default="", show_default=False)
        
        if not result and allow_empty:
            return None
        return result or (None if allow_empty else "")

    def print_welcome(self):
        """打印欢迎信息"""
        welcome_text = """
        ╔════════════════════════════════════════════════════╗
        ║                                                    ║
        ║            DocuGen AI - 智能文档生成助手           ║
        ║                                                    ║
        ╚════════════════════════════════════════════════════╝
        """
        self.console.print(Panel.fit(welcome_text, border_style="blue"))
        
        version_info = f"Version: 1.0.0 | Python: {platform.python_version()} | OS: {platform.system()}"
        self.console.print(version_info, style="dim")
        self.console.print()
    
    def print_info(self, message: str):
        """打印信息
        
        Args:
            message: 信息内容
        """
        self.console.print(f"[blue]INFO:[/blue] {message}")
    
    def print_success(self, message: str):
        """打印成功信息
        
        Args:
            message: 成功信息内容
        """
        self.console.print(f"[green]SUCCESS:[/green] {message}")
    
    def print_warning(self, message: str):
        """打印警告信息
        
        Args:
            message: 警告信息内容
        """
        self.console.print(f"[yellow]WARNING:[/yellow] {message}")
    
    def print_error(self, message: str):
        """打印错误信息
        
        Args:
            message: 错误信息内容
        """
        self.console.print(f"[red]ERROR:[/red] {message}")
    
    def get_project_name(self) -> str:
        """获取项目名称
        
        Returns:
            项目名称
        """
        return self.get_input("请输入项目名称", "未命名项目")
    
    def get_project_description(self) -> str:
        """获取项目描述
        
        Returns:
            项目描述
        """
        return self.get_input("请输入项目描述", "一个自动生成的项目")
    
    def get_boolean_input(self, prompt: str, default: bool = False) -> bool:
        """获取布尔值输入
        
        Args:
            prompt: 提示信息
            default: 默认值
        
        Returns:
            布尔值
        """
        yes_no = "Y/n" if default else "y/N"
        response = self.get_input(f"{prompt} ({yes_no})").lower()
        
        if not response:
            return default
        
        return response.startswith("y")
    
    def show_options(self, title: str, options: List[str]) -> int:
        """显示选项列表并获取用户选择
        
        Args:
            title: 选项标题
            options: 选项列表
        
        Returns:
            选择的选项索引
        """
        self.console.print(f"\n[bold]{title}[/bold]")
        
        for i, option in enumerate(options, 1):
            self.console.print(f"  {i}. {option}")
        
        while True:
            try:
                choice = int(self.get_input("请选择序号"))
                if 1 <= choice <= len(options):
                    return choice - 1
                self.print_error(f"无效选择，请输入1-{len(options)}之间的数字")
            except ValueError:
                self.print_error("请输入有效数字")
    
    def show_progress_bar(self, total: int, description: str = "生成中") -> Progress:
        """显示进度条
        
        Args:
            total: 总步数
            description: 进度条描述
        
        Returns:
            Progress对象
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[bold]{task.fields[status]}"),
            console=self.console
        )
        
        task_id = progress.add_task(description, total=total, status="进行中")
        return progress, task_id
    
    def show_generation_info(self, project_name: str, project_desc: str):
        """显示文档生成信息
        
        Args:
            project_name: 项目名称
            project_desc: 项目描述
        """
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold]项目信息[/bold]\n\n"
            f"名称: [cyan]{project_name}[/cyan]\n"
            f"描述: [cyan]{project_desc}[/cyan]",
            title="文档生成",
            border_style="green"
        ))
        self.console.print()
    
    def show_markdown_preview(self, content: str, title: str = "预览"):
        """显示Markdown预览
        
        Args:
            content: Markdown内容
            title: 预览标题
        """
        md = Markdown(content)
        self.console.print(Panel(md, title=title, border_style="green"))
    
    def show_code_preview(self, code: str, language: str = "python", title: str = "代码预览"):
        """显示代码预览
        
        Args:
            code: 代码内容
            language: 代码语言
            title: 预览标题
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title=title, border_style="cyan"))
    
    def show_generation_results(self, documents: Dict[str, str], save_paths: Dict[str, str] = None):
        """显示文档生成结果
        
        Args:
            documents: 生成的文档字典，格式为 {doc_type: content}
            save_paths: 文档保存路径字典，格式为 {doc_type: file_path}
        """
        self.console.print()
        
        # 创建结果表格
        table = Table(title="文档生成结果")
        table.add_column("文档类型", style="cyan")
        table.add_column("状态", style="green")
        table.add_column("保存路径", style="blue")
        
        doc_titles = {
            'brainstorm': '构思梳理',
            'requirement_confirm': '需求确认',
            'prd': '产品需求文档(PRD)',
            'workflow': '应用流程文档',
            'tech_stack': '技术栈',
            'frontend': '前端设计指南',
            'backend': '后端架构设计',
            'dev_plan': '项目开发计划'
        }
        
        for doc_type, content in documents.items():
            title = doc_titles.get(doc_type, doc_type)
            status = "[green]已完成[/green]"
            path = save_paths.get(doc_type, "") if save_paths else ""
            
            table.add_row(title, status, path)
        
        self.console.print(table)
        self.console.print()
        
        # 显示保存路径摘要
        if save_paths and len(save_paths) > 0:
            self.console.print(Panel(
                "\n".join([f"[cyan]{doc_titles.get(dt, dt)}[/cyan]: {path}" for dt, path in save_paths.items()]),
                title="文档保存路径",
                border_style="green"
            ))
            self.console.print()

# 为了简化使用，创建一个默认实例
cli = CommandLineInterface() 