"""
OpenAI API客户端模块，用于与OpenAI API进行通信

此模块实现了OpenAI API客户端，处理API调用、错误处理和重试逻辑
"""

import os
import time
import json
from typing import Dict, Any, Optional, List, Union
import logging

from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion
from ..api.error import APIError, RateLimitError, NetworkError, AuthenticationError
from ..config import Config
from docugen.utils.logger import DebugLogger, PerformanceTimer
from docugen.utils.debug_tracer import model_tracer


class AIClient:
    """
    OpenAI API客户端类，负责处理与OpenAI API的通信
    """
    
    DEFAULT_MODEL = "gpt-4-1106-preview"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # 基础重试延迟（秒）
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, debug_mode: bool = False):
        """
        初始化AI客户端
        
        Args:
            api_key: OpenAI API密钥
            base_url: 可选的自定义API基础URL
            debug_mode: 是否启用调试模式，显示API请求和响应详情
        """
        self.api_key = api_key
        self.base_url = base_url
        self.debug_mode = debug_mode
        
        # 初始化同步客户端
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
        # 初始化异步客户端
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        # 初始化调试日志记录器
        self.logger = DebugLogger("api.client")
        
        # 配置调试模式
        if self.debug_mode:
            model_tracer.enable()
        
        # 记录客户端初始化信息
        self.logger.logger.debug(f"AI客户端已初始化，base_url={base_url or 'default'}, debug_mode={debug_mode}")
    
    def generate_document(self, 
                         prompt: str, 
                         context: Optional[Dict[str, Any]] = None, 
                         model_name: Optional[str] = None,
                         temperature: float = 0.7,
                         max_tokens: int = 4000) -> str:
        """
        生成文档内容
        
        Args:
            prompt: 提示词
            context: 上下文信息，将转换为JSON字符串
            model_name: 要使用的模型名称
            temperature: 温度参数，控制输出的随机性
            max_tokens: 最大生成令牌数
            
        Returns:
            生成的文档内容
            
        Raises:
            APIError: 调用API出错
        """
        # 确保优先使用传入的model_name，如果没有则使用DEFAULT_MODEL
        model = model_name or self.DEFAULT_MODEL
        
        # 记录使用的模型信息，用于调试
        self.logger.logger.debug(f"使用模型: {model}")
        
        # 准备上下文字符串
        context_str = ""
        if context:
            # 检查是否包含文档链
            if "document_chain" in context and context["document_chain"]:
                # 优化版：将前序文档作为有结构的上下文
                prev_docs = ""
                for i, doc in enumerate(context["document_chain"]):
                    doc_title = doc.get("title", f"文档{i+1}")
                    doc_type = doc.get("type", "unknown")
                    doc_content = doc.get("content", "")
                    prev_docs += f"\n\n## {doc_title} ({doc_type})\n\n{doc_content}"
                
                context_str = f"\n\n# 前序文档内容\n{prev_docs}\n\n# 项目信息\n{json.dumps(context['project_info'], ensure_ascii=False, indent=2)}"
            else:
                # 兼容旧版：简单JSON格式
                context_str = f"\n\n上下文信息:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        
        # 完整提示词
        full_prompt = f"{prompt}{context_str}"
        
        # 构建请求数据
        request_data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的文档生成助手。请根据用户的需求生成高质量的文档内容。生成的内容应当严格遵循用户指定的格式和要求。"},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 记录API调用请求
        request_data_logging = request_data.copy()
        if len(full_prompt) > 500:
            request_data_logging["messages"][1]["content"] = f"{full_prompt[:500]}... (截断，共{len(full_prompt)}字符)"
        self.logger.log_function_call("generate_document", 
                                     args=[f"prompt (长度: {len(prompt)}字符)", f"context (keys: {list(context.keys()) if context else None})"],
                                     kwargs={"model_name": model_name, "temperature": temperature, "max_tokens": max_tokens})
        
        # 使用性能计时器测量API调用时间
        start_time = time.time()
        with PerformanceTimer("OpenAI API调用", self.logger):
            response = self._make_api_call(request_data)
        duration_ms = (time.time() - start_time) * 1000
        
        # 如果调试模式已启用，记录模型输入和输出
        model_tracer.trace_model_call(
            model_name=model,
            prompt=full_prompt,
            messages=request_data["messages"],
            response=response,
            duration_ms=duration_ms
        )
        
        # 提取并返回生成的内容
        content = response.choices[0].message.content
        
        # 记录返回的内容长度
        self.logger.logger.debug(f"生成的内容长度: {len(content)} 字符")
        
        return content
    
    def _make_api_call(self, request_data: Dict[str, Any], retry_count: int = 0) -> ChatCompletion:
        """
        执行API调用，包含重试逻辑
        
        Args:
            request_data: 请求数据
            retry_count: 当前重试次数
            
        Returns:
            API响应
            
        Raises:
            APIError: 调用API出错
        """
        try:
            # 记录API调用开始
            self.logger.logger.debug(f"开始API调用 (尝试 {retry_count + 1}/{self.MAX_RETRIES + 1})")
            
            start_time = time.time()
            response = self.client.chat.completions.create(**request_data)
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录API调用成功
            self.logger.log_api_call(
                api_name="chat.completions.create", 
                request_data={k: v for k, v in request_data.items() if k != "messages"},
                status_code=200,
                duration_ms=duration_ms
            )
            
            # 记录token使用情况
            if hasattr(response, 'usage') and response.usage:
                self.logger.logger.debug(
                    f"Token使用情况: 输入={response.usage.prompt_tokens}, " 
                    f"输出={response.usage.completion_tokens}, "
                    f"总计={response.usage.total_tokens}"
                )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_type = type(e).__name__
            error_msg = str(e)
            
            # 记录API调用失败
            self.logger.log_api_call(
                api_name="chat.completions.create", 
                request_data={k: v for k, v in request_data.items() if k != "messages"},
                status_code=getattr(e, 'status_code', 500),
                duration_ms=duration_ms
            )
            self.logger.log_exception(e, context="API调用")
            
            # 处理不同类型的错误
            if "rate limit" in error_msg.lower():
                error = RateLimitError(f"API调用超出速率限制: {error_msg}")
                
                # 检查是否还可以重试
                if retry_count < self.MAX_RETRIES:
                    retry_delay = self.RETRY_DELAY * (2 ** retry_count)  # 指数退避
                    self.logger.logger.warning(f"触发速率限制，将在 {retry_delay} 秒后重试 (尝试 {retry_count + 1}/{self.MAX_RETRIES})")
                    time.sleep(retry_delay)
                    return self._make_api_call(request_data, retry_count + 1)
                else:
                    self.logger.logger.error("已达到最大重试次数，放弃API调用")
                    raise error
            
            elif "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                raise AuthenticationError(f"API认证失败: {error_msg}")
            
            else:
                raise APIError(f"API调用失败: {error_type} - {error_msg}")
    
    async def generate_document_async(self, 
                                    prompt: str, 
                                    context: Optional[Dict[str, Any]] = None, 
                                    model_name: Optional[str] = None,
                                    temperature: float = 0.7,
                                    max_tokens: int = 4000) -> str:
        """
        异步生成文档内容
        
        Args:
            prompt: 提示词
            context: 上下文信息，将转换为JSON字符串
            model_name: 要使用的模型名称
            temperature: 温度参数，控制输出的随机性
            max_tokens: 最大生成令牌数
            
        Returns:
            生成的文档内容
            
        Raises:
            APIError: 调用API出错
        """
        model = model_name or self.DEFAULT_MODEL
        
        # 准备上下文字符串
        context_str = ""
        if context:
            # 检查是否包含文档链
            if "document_chain" in context and context["document_chain"]:
                # 优化版：将前序文档作为有结构的上下文
                prev_docs = ""
                for i, doc in enumerate(context["document_chain"]):
                    doc_title = doc.get("title", f"文档{i+1}")
                    doc_type = doc.get("type", "unknown")
                    doc_content = doc.get("content", "")
                    prev_docs += f"\n\n## {doc_title} ({doc_type})\n\n{doc_content}"
                
                context_str = f"\n\n# 前序文档内容\n{prev_docs}\n\n# 项目信息\n{json.dumps(context['project_info'], ensure_ascii=False, indent=2)}"
            else:
                # 兼容旧版：简单JSON格式
                context_str = f"\n\n上下文信息:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        
        # 完整提示词
        full_prompt = f"{prompt}{context_str}"
        
        # 构建请求数据
        request_data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的文档生成助手。请根据用户的需求生成高质量的文档内容。生成的内容应当严格遵循用户指定的格式和要求。"},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 记录API调用请求
        self.logger.log_function_call("generate_document_async", 
                                     args=[f"prompt (长度: {len(prompt)}字符)", f"context (keys: {list(context.keys()) if context else None})"],
                                     kwargs={"model_name": model_name, "temperature": temperature, "max_tokens": max_tokens})
        
        # 使用性能计时器测量API调用时间
        start_time = time.time()
        response = await self._make_api_call_async(request_data)
        duration_ms = (time.time() - start_time) * 1000
        
        self.logger.log_performance("OpenAI API异步调用", duration_ms)
        
        # 如果调试模式已启用，记录模型输入和输出
        model_tracer.trace_model_call(
            model_name=model,
            prompt=full_prompt,  # 使用完整提示词而不是原始提示词
            messages=request_data["messages"],
            response=response,
            duration_ms=duration_ms
        )
        
        # 提取并返回生成的内容
        content = response.choices[0].message.content
        
        # 记录返回的内容长度
        self.logger.logger.debug(f"生成的内容长度: {len(content)} 字符")
        
        return content
    
    async def _make_api_call_async(self, request_data: Dict[str, Any], retry_count: int = 0) -> ChatCompletion:
        """
        执行异步API调用，包含重试逻辑
        
        Args:
            request_data: 请求数据
            retry_count: 当前重试次数
            
        Returns:
            API响应
            
        Raises:
            APIError: 调用API出错
        """
        try:
            # 记录API调用开始
            self.logger.logger.debug(f"开始异步API调用 (尝试 {retry_count + 1}/{self.MAX_RETRIES + 1})")
            
            start_time = time.time()
            response = await self.async_client.chat.completions.create(**request_data)
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录API调用成功
            self.logger.log_api_call(
                api_name="chat.completions.create (async)", 
                request_data={k: v for k, v in request_data.items() if k != "messages"},
                status_code=200,
                duration_ms=duration_ms
            )
            
            # 记录token使用情况
            if hasattr(response, 'usage') and response.usage:
                self.logger.logger.debug(
                    f"Token使用情况: 输入={response.usage.prompt_tokens}, " 
                    f"输出={response.usage.completion_tokens}, "
                    f"总计={response.usage.total_tokens}"
                )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_type = type(e).__name__
            error_msg = str(e)
            
            # 记录API调用失败
            self.logger.log_api_call(
                api_name="chat.completions.create (async)", 
                request_data={k: v for k, v in request_data.items() if k != "messages"},
                status_code=getattr(e, 'status_code', 500),
                duration_ms=duration_ms
            )
            self.logger.log_exception(e, context="异步API调用")
            
            # 处理不同类型的错误
            if "rate limit" in error_msg.lower():
                error = RateLimitError(f"异步API调用超出速率限制: {error_msg}")
                
                # 检查是否还可以重试
                if retry_count < self.MAX_RETRIES:
                    retry_delay = self.RETRY_DELAY * (2 ** retry_count)  # 指数退避
                    self.logger.logger.warning(f"触发速率限制，将在 {retry_delay} 秒后重试 (尝试 {retry_count + 1}/{self.MAX_RETRIES})")
                    time.sleep(retry_delay)
                    return await self._make_api_call_async(request_data, retry_count + 1)
                else:
                    self.logger.logger.error("已达到最大重试次数，放弃API调用")
                    raise error
            
            elif "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                raise AuthenticationError(f"API认证失败: {error_msg}")
            
            else:
                raise APIError(f"API调用失败: {error_type} - {error_msg}") 