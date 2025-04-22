"""
API错误处理模块
定义API调用过程中可能遇到的各类异常
"""

class APIError(Exception):
    """OpenAI API调用基础异常类"""
    def __init__(self, message: str, error_code: int = 5001):
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{error_code}] {message}")


class RateLimitError(APIError):
    """API速率限制异常"""
    def __init__(self, message: str):
        super().__init__(message, error_code=5002)


class NetworkError(APIError):
    """网络连接异常"""
    def __init__(self, message: str):
        super().__init__(message, error_code=5003)


class TokenLimitError(APIError):
    """Token数量超限异常"""
    def __init__(self, message: str):
        super().__init__(message, error_code=5004)


class AuthenticationError(APIError):
    """认证异常，通常是API密钥问题"""
    def __init__(self, message: str):
        super().__init__(message, error_code=5005)


class ContentFilterError(APIError):
    """内容过滤异常，提示内容被审核系统拒绝"""
    def __init__(self, message: str):
        super().__init__(message, error_code=5006) 