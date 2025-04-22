"""
DocuGen AI 工具模块
提供各种辅助功能
"""

from docugen.utils.prompt import PromptManager
from docugen.utils.file import FileManager
from docugen.utils.logger import setup_logger, LogManager, DebugLogger, PerformanceTimer
from docugen.utils.template import TemplateManager
from docugen.utils.variable import VariableManager, TemplateVariableProcessor 
from docugen.utils.cli import CommandLineInterface, cli
from docugen.utils.progress import ProgressManager, progress_manager, ProgressStatus
from docugen.utils.html_formatter import HTMLFormatter
from docugen.utils.pdf_generator import PDFGenerator 
from docugen.utils.i18n import I18nManager, i18n, _
from docugen.utils.debug_tracer import ModelDebugTracer, model_tracer

__all__ = [
    'FileManager', 'file_manager',
    'PromptManager', 'prompt_manager',
    'LogManager', 'DebugLogger', 'PerformanceTimer',
    'TemplateManager', 'TemplateProcessor',
    'CommandLineInterface', 'cli',
    'ProgressManager', 'progress_manager', 'ProgressStatus', 
    'VariableManager', 'TemplateVariableProcessor',
    'I18n', 'i18n',
    'ModelDebugTracer', 'model_tracer'
] 