"""
配置管理模块
负责加载和管理系统配置
"""

import os
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dotenv import load_dotenv


class Config:
    """配置管理器，单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        :param config_file: 配置文件路径，如果为None则使用默认路径
        """
        if not Config._initialized:
            self.logger = logging.getLogger("docugen.config")
            
            # 加载环境变量
            load_dotenv()
            
            # 默认配置
            self.defaults = {
                "api": {
                    "model": "gpt-4",
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "timeout": 60,
                    "max_retries": 3,
                    "base_url": None  # 添加API基础URL配置，默认为None表示使用OpenAI默认URL
                },
                "paths": {
                    "prompts_dir": "../文档提示词",
                    "output_dir": "output",
                    "templates_dir": "./templates",
                    "translations_dir": "./translations"
                },
                "logging": {
                    "level": "INFO",
                    "file": "logs/docugen.log"
                },
                "i18n": {
                    "language": "zh_CN",
                    "auto_detect": True,
                    "document_generation": {
                        "use_target_language": True,
                        "translate_output": False
                    }
                },
                "web": {
                    "enabled": True,
                    "host": "localhost",
                    "port": 8080,
                    "auto_open": True,
                    "static_dir": "docugen/web/static"
                },
                "debug": {
                    "enabled": False,
                    "log_model_io": False,
                    "log_dir": "logs/model_debug"
                }
            }
            
            # 实际配置，初始化为默认配置
            self.config = self.defaults.copy()
            
            # 如果提供了配置文件，则加载配置
            if config_file:
                self.load_config(config_file)
            
            # 标记为已初始化
            Config._initialized = True
    
    def load_config(self, config_file: str) -> bool:
        """
        从文件加载配置
        :param config_file: 配置文件路径
        :return: 是否成功加载
        """
        config_path = Path(config_file)
        if not config_path.exists():
            self.logger.warning(f"配置文件不存在: {config_file}")
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # 合并配置
            self._merge_config(user_config)
            self.logger.info(f"配置加载成功: {config_file}")
            return True
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            return False
    
    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """
        合并用户配置到当前配置
        :param user_config: 用户配置
        """
        for section, values in user_config.items():
            if section in self.config:
                if isinstance(self.config[section], dict) and isinstance(values, dict):
                    # 如果都是字典，递归合并
                    for key, value in values.items():
                        self.config[section][key] = value
                else:
                    # 直接替换
                    self.config[section] = values
            else:
                # 新增部分
                self.config[section] = values
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        获取配置项
        :param path: 配置路径，格式为'section.key'
        :param default: 默认值，如果配置项不存在则返回此值
        :return: 配置值
        """
        parts = path.split('.')
        config = self.config
        
        for part in parts:
            if isinstance(config, dict) and part in config:
                config = config[part]
            else:
                return default
        
        return config
    
    def set(self, path: str, value: Any) -> None:
        """
        设置配置项
        :param path: 配置路径，格式为'section.key'
        :param value: 配置值
        """
        parts = path.split('.')
        config = self.config
        
        # 遍历到最后一级
        for i, part in enumerate(parts[:-1]):
            if part not in config:
                config[part] = {}
            config = config[part]
        
        # 设置最后一级的值
        config[parts[-1]] = value
    
    def save_config(self, config_file: str) -> bool:
        """
        保存配置到文件
        :param config_file: 配置文件路径
        :return: 是否成功保存
        """
        config_path = Path(config_file)
        
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"配置保存成功: {config_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
            return False
    
    def get_api_key(self) -> Optional[str]:
        """
        获取API密钥
        :return: API密钥，如果未设置则返回None
        """
        return os.environ.get("OPENAI_API_KEY")
    
    def get_api_base_url(self) -> Optional[str]:
        """
        获取API基础URL
        :return: API基础URL，如果未设置则返回None
        """
        # 优先从环境变量获取
        env_url = os.environ.get("OPENAI_API_BASE")
        if env_url:
            return env_url
        
        # 其次从配置中获取
        return self.get("api.base_url")
    
    def get_model_name(self) -> str:
        """
        获取模型名称
        :return: 模型名称，默认为"gpt-4"
        """
        # 优先从环境变量获取
        env_model = os.environ.get("OPENAI_MODEL_NAME")
        if env_model:
            return env_model
            
        # 其次从配置中获取
        return self.get("api.model", "gpt-4")
    
    def get_temperature(self) -> float:
        """
        获取温度参数
        :return: 温度参数，控制输出的随机性，默认为0.7
        """
        # 优先从环境变量获取
        env_temp = os.environ.get("AI_TEMPERATURE")
        if env_temp:
            try:
                return float(env_temp)
            except ValueError:
                self.logger.warning(f"环境变量AI_TEMPERATURE值无效: {env_temp}，使用默认值")
        
        # 其次从配置中获取
        return self.get("api.temperature", 0.7)
    
    def get_max_tokens(self) -> int:
        """
        获取最大令牌数
        :return: 最大生成令牌数，默认为4000
        """
        # 优先从环境变量获取
        env_tokens = os.environ.get("AI_MAX_TOKENS")
        if env_tokens:
            try:
                return int(env_tokens)
            except ValueError:
                self.logger.warning(f"环境变量AI_MAX_TOKENS值无效: {env_tokens}，使用默认值")
        
        # 其次从配置中获取
        return self.get("api.max_tokens", 4000)
    
    @staticmethod
    def get_formatted_time(format: str = "%H:%M:%S") -> str:
        """
        获取格式化的当前时间
        :param format: 时间格式，默认为时:分:秒
        :return: 格式化的时间字符串
        """
        # 获取当前时间（使用上海时区 UTC+8）
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        return now.strftime(format)
    
    @staticmethod
    def get_formatted_date(format: str = "%Y-%m-%d") -> str:
        """
        获取格式化的当前日期
        :param format: 日期格式，默认为年-月-日
        :return: 格式化的日期字符串
        """
        # 获取当前日期（使用上海时区 UTC+8）
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        return now.strftime(format)
    
    @staticmethod
    def get_formatted_datetime(format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        获取格式化的当前日期时间
        :param format: 日期时间格式，默认为年-月-日 时:分:秒
        :return: 格式化的日期时间字符串
        """
        # 获取当前日期时间（使用上海时区 UTC+8）
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        return now.strftime(format)
    
    def is_debug_enabled(self) -> bool:
        """
        检查是否启用调试模式
        
        Returns:
            True表示启用调试模式，False表示禁用
        """
        # 优先从环境变量获取
        if os.environ.get("DOCUGEN_DEBUG") and os.environ.get("DOCUGEN_DEBUG").lower() in ["true", "1", "yes"]:
            return True
        
        # 其次从配置获取
        return self.get("debug.enabled", False)
    
    def is_model_debug_enabled(self) -> bool:
        """
        检查是否启用模型输入输出调试
        
        Returns:
            True表示启用模型调试，False表示禁用
        """
        # 优先从环境变量获取
        if os.environ.get("DOCUGEN_DEBUG_MODEL") and os.environ.get("DOCUGEN_DEBUG_MODEL").lower() in ["true", "1", "yes"]:
            return True
        
        # 其次从配置获取
        return self.get("debug.log_model_io", False) 