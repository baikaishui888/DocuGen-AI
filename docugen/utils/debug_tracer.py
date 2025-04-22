"""
调试跟踪器模块
用于记录和显示大模型的输入和输出内容
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from .logger import DebugLogger


class ModelDebugTracer:
    """
    大模型交互调试跟踪器
    负责记录和展示大模型的输入和输出内容
    """
    
    def __init__(self, enabled: bool = False, log_dir: str = "logs/model_debug"):
        """
        初始化调试跟踪器
        
        Args:
            enabled: 是否启用调试跟踪
            log_dir: 调试日志存储目录
        """
        self.enabled = enabled
        self.log_dir = Path(log_dir)
        self.logger = DebugLogger("model_debug_tracer")
        
        # 创建日志目录
        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.logger.logger.info(f"调试跟踪器已启动，日志目录: {self.log_dir}")
    
    def trace_model_call(self, 
                         model_name: str, 
                         prompt: str, 
                         messages: List[Dict[str, str]], 
                         response: Optional[Any] = None,
                         duration_ms: Optional[float] = None) -> None:
        """
        记录模型调用详情
        
        Args:
            model_name: 模型名称
            prompt: 原始提示词
            messages: 发送给模型的消息数组
            response: 模型响应内容
            duration_ms: 调用持续时间(毫秒)
        """
        if not self.enabled:
            return
        
        # 创建时间戳和唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_id = f"{timestamp}_{model_name.replace('-', '_')}"
        
        # 准备跟踪数据
        trace_data = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "duration_ms": duration_ms,
            "input": {
                "prompt": prompt,
                "messages": messages
            }
        }
        
        # 添加响应数据（如果有）
        if response is not None:
            if hasattr(response, 'choices') and response.choices:
                response_content = response.choices[0].message.content
                trace_data["output"] = response_content
                
                # 记录token使用情况（如果可用）
                if hasattr(response, 'usage') and response.usage:
                    trace_data["usage"] = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
        
        # 保存跟踪日志到JSON文件
        trace_file = self.log_dir / f"{trace_id}.json"
        with open(trace_file, 'w', encoding='utf-8') as f:
            json.dump(trace_data, ensure_ascii=False, indent=2, fp=f)
        
        self.logger.logger.debug(f"已记录模型调用跟踪: {trace_file}")
        
        # 控制台输出调试信息
        self._print_debug_info(trace_data)
    
    def _print_debug_info(self, trace_data: Dict[str, Any]) -> None:
        """
        打印调试信息到控制台
        
        Args:
            trace_data: 跟踪数据
        """
        print("\n" + "="*80)
        print(f"模型调试信息 [{trace_data['timestamp']}]")
        print("-"*80)
        
        # 打印模型和性能信息
        print(f"模型: {trace_data['model']}")
        if 'duration_ms' in trace_data and trace_data['duration_ms']:
            print(f"调用耗时: {trace_data['duration_ms']:.2f}ms")
        
        # 打印输入信息
        print("-"*80)
        print("输入内容:")
        
        # 由于提示词可能很长，只展示前500个字符
        prompt = trace_data['input']['prompt']
        if len(prompt) > 500:
            print(f"{prompt[:500]}... (共{len(prompt)}字符)")
        else:
            print(prompt)
        
        # 打印输出信息
        if 'output' in trace_data:
            print("-"*80)
            print("输出内容:")
            output = trace_data['output']
            if len(output) > 500:
                print(f"{output[:500]}... (共{len(output)}字符)")
            else:
                print(output)
        
        # 打印Token使用情况
        if 'usage' in trace_data:
            print("-"*80)
            usage = trace_data['usage']
            print(f"Token使用: 输入={usage['prompt_tokens']}, 输出={usage['completion_tokens']}, 总计={usage['total_tokens']}")
        
        print("="*80 + "\n")
    
    def enable(self) -> None:
        """启用调试跟踪"""
        if not self.enabled:
            self.enabled = True
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.logger.logger.info(f"调试跟踪器已启用，日志目录: {self.log_dir}")
    
    def disable(self) -> None:
        """禁用调试跟踪"""
        if self.enabled:
            self.enabled = False
            self.logger.logger.info("调试跟踪器已禁用")


# 创建默认实例
model_tracer = ModelDebugTracer() 