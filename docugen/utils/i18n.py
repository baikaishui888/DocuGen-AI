"""
国际化支持模块
支持文档生成过程中的多语言切换和管理
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any


class I18nManager:
    """
    国际化管理器，支持中英文双语切换
    实现单例模式确保全局一致的语言设置
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(I18nManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, lang: str = "zh_CN", translations_dir: Optional[str] = None):
        """
        初始化国际化管理器
        :param lang: 初始语言代码，默认为中文
        :param translations_dir: 翻译文件目录，默认为None（使用默认目录）
        """
        if not I18nManager._initialized:
            self.logger = logging.getLogger("docugen.i18n")
            
            # 支持的语言列表
            self.supported_languages = {
                "zh_CN": "中文（简体）",
                "en_US": "English (US)"
            }
            
            # 设置当前语言
            self.current_lang = lang if lang in self.supported_languages else "zh_CN"
            
            # 设置翻译文件目录
            if translations_dir:
                self.translations_dir = Path(translations_dir)
            else:
                # 相对于当前文件的默认目录
                self.translations_dir = Path(__file__).parent.parent / "translations"
            
            # 确保翻译目录存在
            self.translations_dir.mkdir(parents=True, exist_ok=True)
            
            # 加载翻译文件
            self.translations = {}
            self._load_translations()
            
            I18nManager._initialized = True
    
    def _load_translations(self) -> None:
        """
        加载所有支持语言的翻译文件
        """
        for lang in self.supported_languages:
            self._load_language(lang)
    
    def _load_language(self, lang: str) -> bool:
        """
        加载指定语言的翻译文件
        :param lang: 语言代码
        :return: 是否成功加载
        """
        translation_file = self.translations_dir / f"{lang}.json"
        
        # 如果文件不存在，尝试创建默认翻译文件
        if not translation_file.exists():
            if lang == "zh_CN":
                # 为中文创建默认翻译
                self.translations[lang] = self._create_default_chinese()
                self._save_translation(lang)
                return True
            elif lang == "en_US":
                # 为英文创建默认翻译
                self.translations[lang] = self._create_default_english()
                self._save_translation(lang)
                return True
            else:
                self.logger.warning(f"翻译文件不存在: {translation_file}")
                return False
        
        try:
            with open(translation_file, 'r', encoding='utf-8') as f:
                self.translations[lang] = json.load(f)
            self.logger.info(f"已加载语言 {lang} 的翻译")
            return True
        except Exception as e:
            self.logger.error(f"加载翻译文件失败 {lang}: {str(e)}")
            return False
    
    def _create_default_chinese(self) -> Dict[str, Any]:
        """
        创建默认中文翻译
        :return: 中文翻译字典
        """
        return {
            "ui": {
                "title": "DocuGen AI 文档生成工具",
                "project_name": "项目名称",
                "prompt_path": "提示词路径",
                "start_generation": "开始生成",
                "confirm_generation": "确认生成文档?",
                "yes": "是",
                "no": "否",
                "cancel": "取消",
                "success": "成功",
                "failure": "失败",
                "done": "完成",
                "error": "错误",
                "warning": "警告",
                "info": "信息",
                "save_path": "保存路径",
                "language": "语言",
                "settings": "设置",
                "help": "帮助",
                "exit": "退出"
            },
            "documents": {
                "brainstorm": "构思梳理文档",
                "prd": "产品需求文档",
                "workflow": "应用流程文档",
                "tech_stack": "技术栈文档",
                "frontend": "前端设计文档",
                "backend": "后端设计文档",
                "dev_plan": "开发计划"
            },
            "status": {
                "generating": "生成中",
                "validating": "验证中",
                "exporting": "导出中",
                "completed": "已完成",
                "failed": "失败",
                "paused": "已暂停"
            },
            "errors": {
                "file_not_found": "文件未找到",
                "permission_denied": "权限不足",
                "invalid_input": "无效输入",
                "api_error": "API错误",
                "timeout": "操作超时",
                "validation_failed": "验证失败",
                "unknown": "未知错误"
            },
            "prompts": {
                "default_title": "文档生成器提示词",
                "system_role": "你是一个专业的文档编写助手",
                "user_instruction": "请根据以下信息生成一份完整的文档："
            }
        }
    
    def _create_default_english(self) -> Dict[str, Any]:
        """
        创建默认英文翻译
        :return: 英文翻译字典
        """
        return {
            "ui": {
                "title": "DocuGen AI Document Generator",
                "project_name": "Project Name",
                "prompt_path": "Prompt Path",
                "start_generation": "Start Generation",
                "confirm_generation": "Confirm document generation?",
                "yes": "Yes",
                "no": "No",
                "cancel": "Cancel",
                "success": "Success",
                "failure": "Failure",
                "done": "Done",
                "error": "Error",
                "warning": "Warning",
                "info": "Info",
                "save_path": "Save Path",
                "language": "Language",
                "settings": "Settings",
                "help": "Help",
                "exit": "Exit"
            },
            "documents": {
                "brainstorm": "Brainstorming Document",
                "prd": "Product Requirements Document",
                "workflow": "Application Workflow Document",
                "tech_stack": "Technology Stack Document",
                "frontend": "Frontend Design Document",
                "backend": "Backend Design Document",
                "dev_plan": "Development Plan"
            },
            "status": {
                "generating": "Generating",
                "validating": "Validating",
                "exporting": "Exporting",
                "completed": "Completed",
                "failed": "Failed",
                "paused": "Paused"
            },
            "errors": {
                "file_not_found": "File not found",
                "permission_denied": "Permission denied",
                "invalid_input": "Invalid input",
                "api_error": "API error",
                "timeout": "Operation timeout",
                "validation_failed": "Validation failed",
                "unknown": "Unknown error"
            },
            "prompts": {
                "default_title": "Document Generator Prompt",
                "system_role": "You are a professional document writing assistant",
                "user_instruction": "Please generate a complete document based on the following information:"
            }
        }
    
    def _save_translation(self, lang: str) -> bool:
        """
        保存翻译文件
        :param lang: 语言代码
        :return: 是否成功保存
        """
        if lang not in self.translations:
            self.logger.error(f"无法保存不存在的语言翻译: {lang}")
            return False
        
        try:
            translation_file = self.translations_dir / f"{lang}.json"
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(self.translations[lang], f, ensure_ascii=False, indent=2)
            self.logger.info(f"已保存 {lang} 的翻译")
            return True
        except Exception as e:
            self.logger.error(f"保存翻译文件失败 {lang}: {str(e)}")
            return False
    
    def switch_language(self, lang: str) -> bool:
        """
        切换当前语言
        :param lang: 语言代码
        :return: 是否切换成功
        """
        if lang not in self.supported_languages:
            self.logger.warning(f"不支持的语言: {lang}")
            return False
        
        # 如果翻译未加载，先加载
        if lang not in self.translations:
            success = self._load_language(lang)
            if not success:
                return False
        
        # 切换当前语言
        self.current_lang = lang
        self.logger.info(f"已切换到语言: {self.supported_languages[lang]}")
        return True
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        获取当前语言的翻译
        :param key: 翻译键，使用点号分隔层级，如"ui.title"
        :param default: 默认值，如果翻译不存在则返回此值
        :return: 翻译文本
        """
        if self.current_lang not in self.translations:
            self.logger.warning(f"当前语言未加载: {self.current_lang}")
            return default if default is not None else key
        
        parts = key.split('.')
        translation = self.translations[self.current_lang]
        
        # 遍历键路径
        for part in parts:
            if isinstance(translation, dict) and part in translation:
                translation = translation[part]
            else:
                self.logger.debug(f"翻译键不存在: {key}")
                return default if default is not None else key
        
        # 如果找到的结果不是字符串，返回默认值
        if not isinstance(translation, str):
            return default if default is not None else key
        
        return translation
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        获取支持的语言列表
        :return: 语言代码和名称的字典
        """
        return self.supported_languages
    
    def get_current_language(self) -> str:
        """
        获取当前语言代码
        :return: 当前语言代码
        """
        return self.current_lang
    
    def get_current_language_name(self) -> str:
        """
        获取当前语言名称
        :return: 当前语言名称
        """
        return self.supported_languages.get(self.current_lang, "Unknown")
    
    def get_translator(self) -> callable:
        """
        获取翻译函数
        :return: 翻译函数
        """
        return lambda key, default=None: self.get(key, default)
    
    def get_all_keys(self, prefix: str = "") -> List[str]:
        """
        获取所有翻译键
        :param prefix: 键前缀，用于筛选子集
        :return: 翻译键列表
        """
        keys = []
        
        if self.current_lang not in self.translations:
            return keys
        
        def collect_keys(data, current_prefix=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    new_prefix = f"{current_prefix}.{key}" if current_prefix else key
                    if isinstance(value, dict):
                        collect_keys(value, new_prefix)
                    else:
                        keys.append(new_prefix)
        
        collect_keys(self.translations[self.current_lang])
        
        # 筛选符合前缀的键
        if prefix:
            return [key for key in keys if key.startswith(prefix)]
        
        return keys


# 创建全局实例方便导入
i18n = I18nManager()


def _(key: str, default: Optional[str] = None) -> str:
    """
    获取翻译的简便函数，类似gettext
    :param key: 翻译键
    :param default: 默认值
    :return: 翻译文本
    """
    return i18n.get(key, default) 