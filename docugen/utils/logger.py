"""
日志工具模块
提供统一的日志记录功能和高级调试日志
"""

import os
import sys
import logging
import inspect
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Union


def setup_logger(
    logger_name: str = "docugen",
    log_file: Optional[str] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> logging.Logger:
    """
    设置一个具有控制台和文件处理器的日志记录器
    :param logger_name: 日志记录器名称
    :param log_file: 日志文件路径，如果为None则不创建文件处理器
    :param console_level: 控制台处理器的日志级别
    :param file_level: 文件处理器的日志级别
    :return: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # 设置最低级别为DEBUG
    logger.propagate = False  # 不传播到父日志记录器
    
    # 清除已存在的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建详细的文件格式化器，包含更多调试信息
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果提供了日志文件路径，创建文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(file_level)
        file_handler.setFormatter(detailed_formatter)  # 使用详细的格式化器
        logger.addHandler(file_handler)
    
    return logger


def get_default_log_file() -> str:
    """
    获取默认日志文件路径
    :return: 默认日志文件路径
    """
    # 使用日期作为日志文件名
    date_str = datetime.now().strftime("%Y%m%d")
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    return str(log_dir / f"docugen_{date_str}.log")


class LogManager:
    """日志管理器，提供全局日志访问"""
    
    _instance = None
    _initialized = False
    _loggers: Dict[str, logging.Logger] = {}
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, log_file: Optional[str] = None, debug_mode: bool = False):
        if not LogManager._initialized:
            self.log_file = log_file or get_default_log_file()
            self.debug_mode = debug_mode
            
            # 根据debug_mode设置控制台日志级别
            console_level = logging.DEBUG if debug_mode else logging.INFO
            
            self.root_logger = setup_logger(log_file=self.log_file, console_level=console_level)
            LogManager._initialized = True
            self._loggers["docugen"] = self.root_logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器
        :param name: 日志记录器名称
        :return: 日志记录器
        """
        if name in self._loggers:
            return self._loggers[name]
        
        if name == "docugen":
            return self.root_logger
        
        logger = logging.getLogger(name)
        # 确保子日志记录器不重复添加处理器
        if not logger.handlers:
            # 使用与根日志记录器相同的处理器
            for handler in self.root_logger.handlers:
                logger.addHandler(handler)
            
            # 设置日志级别
            logger.setLevel(self.root_logger.level)
            # 禁止传播到父日志记录器以避免重复日志
            logger.propagate = False
        
        self._loggers[name] = logger
        return logger
    
    def set_debug_mode(self, debug_mode: bool) -> None:
        """
        设置调试模式，影响控制台日志输出级别
        :param debug_mode: 是否启用调试模式
        """
        self.debug_mode = debug_mode
        console_level = logging.DEBUG if debug_mode else logging.INFO
        
        # 更新所有已存在的日志记录器
        for logger in self._loggers.values():
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                    handler.setLevel(console_level)


# 高级日志记录功能
class DebugLogger:
    """
    提供高级调试日志记录功能的类
    """
    
    def __init__(self, module_name: str = None):
        """
        初始化调试日志记录器
        :param module_name: 模块名称，如果为None则自动从调用栈获取
        """
        if module_name is None:
            # 尝试从调用栈获取模块名称
            frame = inspect.currentframe().f_back
            module = inspect.getmodule(frame)
            module_name = module.__name__ if module else "unknown"
        
        self.logger = LogManager().get_logger(module_name)
    
    def log_function_call(self, func_name: str, args: List[Any] = None, kwargs: Dict[str, Any] = None) -> None:
        """
        记录函数调用信息
        :param func_name: 函数名称
        :param args: 位置参数
        :param kwargs: 关键字参数
        """
        args_str = ", ".join([str(arg) for arg in args]) if args else ""
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        params = ", ".join(filter(None, [args_str, kwargs_str]))
        
        self.logger.debug(f"函数调用: {func_name}({params})")
    
    def log_variable(self, name: str, value: Any, level: int = logging.DEBUG) -> None:
        """
        记录变量值
        :param name: 变量名称
        :param value: 变量值
        :param level: 日志级别
        """
        self.logger.log(level, f"变量 {name} = {value} (类型: {type(value).__name__})")
    
    def log_performance(self, operation: str, duration_ms: float) -> None:
        """
        记录性能数据
        :param operation: 操作名称
        :param duration_ms: 持续时间(毫秒)
        """
        self.logger.debug(f"性能: {operation} 完成时间 {duration_ms:.2f}ms")
    
    def log_exception(self, exc: Exception, context: str = None) -> None:
        """
        记录异常详情
        :param exc: 异常对象
        :param context: 上下文信息
        """
        if context:
            self.logger.error(f"异常在 {context}: {exc}")
        else:
            self.logger.error(f"异常: {exc}")
        
        # 记录详细的堆栈跟踪
        self.logger.debug(f"异常堆栈: {traceback.format_exc()}")
    
    def log_api_call(self, api_name: str, request_data: Dict[str, Any], response_data: Dict[str, Any] = None, 
                     status_code: int = None, duration_ms: float = None) -> None:
        """
        记录API调用详情
        :param api_name: API名称
        :param request_data: 请求数据
        :param response_data: 响应数据
        :param status_code: 状态码
        :param duration_ms: 持续时间(毫秒)
        """
        log_parts = [f"API调用: {api_name}"]
        
        if status_code is not None:
            log_parts.append(f"状态码: {status_code}")
        
        if duration_ms is not None:
            log_parts.append(f"耗时: {duration_ms:.2f}ms")
        
        self.logger.debug(", ".join(log_parts))
        self.logger.debug(f"请求数据: {request_data}")
        
        if response_data is not None:
            self.logger.debug(f"响应数据: {response_data}")
    
    def log_system_info(self, info: Dict[str, Any]) -> None:
        """
        记录系统信息
        :param info: 系统信息字典
        """
        self.logger.debug(f"系统信息: {info}")


# 创建性能计时器
class PerformanceTimer:
    """用于测量代码块执行时间的上下文管理器"""
    
    def __init__(self, operation_name: str, logger: Union[logging.Logger, DebugLogger] = None):
        """
        初始化性能计时器
        :param operation_name: 操作名称
        :param logger: 日志记录器
        """
        self.operation_name = operation_name
        self.start_time = None
        
        # 如果提供的是DebugLogger实例，获取其内部logger
        if isinstance(logger, DebugLogger):
            self.logger = logger
        else:
            self.logger = logger or DebugLogger()
    
    def __enter__(self):
        """开始计时"""
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """结束计时并记录"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() * 1000  # 转换为毫秒
        
        if hasattr(self.logger, 'log_performance'):
            self.logger.log_performance(self.operation_name, duration)
        else:
            self.logger.debug(f"性能: {self.operation_name} 完成时间 {duration:.2f}ms") 