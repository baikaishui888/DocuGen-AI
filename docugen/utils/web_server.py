#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web服务器模块
提供可视化界面的Web服务功能
"""

import os
import json
import logging
import threading
import asyncio
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import webbrowser

from docugen.utils.i18n import i18n, _
from docugen.config import Config

logger = logging.getLogger(__name__)

# 定义全局变量用于存储运行状态数据
_generation_status = {
    "project_name": "",
    "current_step": 0,
    "total_steps": 7,
    "current_document": "",
    "documents": [],
    "status": "ready",  # ready, generating, completed, failed, paused
    "progress": 0,
    "messages": []
}

# 全局锁，用于线程安全地更新状态
_status_lock = threading.Lock()

def update_generation_status(**kwargs):
    """更新生成状态
    
    Args:
        **kwargs: 要更新的状态字段
    """
    global _generation_status
    with _status_lock:
        for key, value in kwargs.items():
            if key in _generation_status:
                _generation_status[key] = value
                
        # 自动计算进度百分比
        if 'current_step' in kwargs and 'total_steps' in _generation_status:
            _generation_status['progress'] = int(100 * _generation_status['current_step'] / _generation_status['total_steps'])

def add_status_message(message: str, level: str = "info"):
    """添加状态消息
    
    Args:
        message: 消息内容
        level: 消息等级 (info, warning, error, success)
    """
    global _generation_status
    with _status_lock:
        _generation_status["messages"].append({
            "text": message,
            "level": level,
            "time": Config.get_formatted_time()
        })
        
        # 限制消息数量，保留最新的50条
        if len(_generation_status["messages"]) > 50:
            _generation_status["messages"] = _generation_status["messages"][-50:]

def get_generation_status():
    """获取当前生成状态
    
    Returns:
        当前状态的副本
    """
    with _status_lock:
        return dict(_generation_status)

def set_document_status(doc_name: str, status: str):
    """设置文档状态
    
    Args:
        doc_name: 文档名称
        status: 状态 (pending, generating, completed, failed)
    """
    with _status_lock:
        for doc in _generation_status["documents"]:
            if doc["name"] == doc_name:
                doc["status"] = status
                return
                
        # 如果文档不存在，则添加
        _generation_status["documents"].append({
            "name": doc_name,
            "status": status
        })

class StatusHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器，提供状态API和静态文件服务"""
    
    def __init__(self, *args, **kwargs):
        # 设置静态文件目录
        self.static_dir = Path(__file__).parent.parent / "web" / "static"
        # 调用父类初始化方法
        super().__init__(*args, **kwargs)
    
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/':
            # 提供主页
            self.path = '/index.html'
            return self.serve_static_file()
            
        elif self.path == '/api/status':
            # 返回生成状态
            self._set_headers()
            self.wfile.write(json.dumps(get_generation_status()).encode())
            
        elif self.path.startswith('/api/'):
            # 其他API路由
            self._set_headers()
            self.wfile.write(json.dumps({"error": "Not implemented"}).encode())
            
        else:
            # 静态文件
            return self.serve_static_file()
    
    def serve_static_file(self):
        """提供静态文件服务"""
        try:
            # 确保使用正确的静态目录路径
            static_dir = Path(__file__).parent.parent / "web" / "static"
            file_path = static_dir / self.path.lstrip('/')
            
            if not file_path.exists():
                self.send_error(404, "File not found")
                return
                
            # 确定内容类型
            content_type = self.get_content_type(file_path)
            
            # 发送响应头
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            
            # 发送文件内容
            with open(file_path, 'rb') as file:
                self.wfile.write(file.read())
                
        except Exception as e:
            logger.error(f"Error serving static file: {e}")
            self.send_error(500, f"Server error: {str(e)}")
    
    def get_content_type(self, file_path: Path) -> str:
        """根据文件扩展名确定内容类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            内容类型字符串
        """
        ext = file_path.suffix.lower()
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml'
        }
        return content_types.get(ext, 'application/octet-stream')

class WebVisualizer:
    """Web可视化服务器类，提供可视化界面和API服务"""
    
    def __init__(self, host='localhost', port=8080):
        """初始化Web可视化服务器
        
        Args:
            host: 主机地址
            port: 端口号
        """
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.is_running = False
        
        # 创建静态文件目录
        self.static_dir = Path(__file__).parent.parent / "web" / "static"
        self.static_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化状态
        self._init_status()
    
    def _init_status(self):
        """初始化生成状态"""
        update_generation_status(
            project_name="",
            current_step=0,
            total_steps=7,
            current_document="",
            documents=[
                {"name": "构思梳理文档", "status": "pending"},
                {"name": "PRD文档", "status": "pending"},
                {"name": "应用流程文档", "status": "pending"},
                {"name": "技术栈文档", "status": "pending"},
                {"name": "前端设计文档", "status": "pending"},
                {"name": "后端设计文档", "status": "pending"},
                {"name": "开发计划", "status": "pending"}
            ],
            status="ready",
            progress=0,
            messages=[]
        )
    
    def start(self, open_browser=True):
        """启动Web服务器
        
        Args:
            open_browser: 是否自动打开浏览器
        """
        if self.is_running:
            logger.warning("Web visualizer already running")
            return
            
        try:
            # 创建并配置HTTP服务器
            handler = StatusHandler
            # 允许地址重用，解决端口占用问题
            socketserver.TCPServer.allow_reuse_address = True
            self.server = socketserver.ThreadingTCPServer((self.host, self.port), handler)
            
            # 在单独的线程中启动服务器
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.is_running = True
            logger.info(f"Web visualizer started at http://{self.host}:{self.port}")
            
            # 自动打开浏览器
            if open_browser:
                webbrowser.open(f"http://{self.host}:{self.port}")
            
            add_status_message(_("ui.web.server_started", f"Web可视化服务已启动: http://{self.host}:{self.port}"), "success")
            
        except Exception as e:
            logger.error(f"Failed to start web visualizer: {e}")
            add_status_message(_("ui.web.server_error", f"Web可视化服务启动失败: {str(e)}"), "error")
    
    def stop(self):
        """停止Web服务器"""
        if not self.is_running:
            return
            
        try:
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join()
            self.is_running = False
            logger.info("Web visualizer stopped")
            
        except Exception as e:
            logger.error(f"Error stopping web visualizer: {e}")
    
    def update_status(self, **kwargs):
        """更新生成状态
        
        Args:
            **kwargs: 要更新的状态字段
        """
        update_generation_status(**kwargs)
    
    def add_message(self, message: str, level: str = "info"):
        """添加状态消息
        
        Args:
            message: 消息内容
            level: 消息等级 (info, warning, error, success)
        """
        add_status_message(message, level)
    
    def set_document_status(self, doc_name: str, status: str):
        """设置文档状态
        
        Args:
            doc_name: 文档名称
            status: 状态 (pending, generating, completed, failed)
        """
        with _status_lock:
            for doc in _generation_status["documents"]:
                if doc["name"] == doc_name:
                    doc["status"] = status
                    return
                
            # 如果文档不存在，则添加
            _generation_status["documents"].append({
                "name": doc_name,
                "status": status
            })
    
    def update_progress(self, current: int, total: int):
        """更新进度
        
        Args:
            current: 当前步骤
            total: 总步骤数
        """
        update_generation_status(
            current_step=current,
            total_steps=total,
            progress=int(100 * current / total)
        )

# 创建默认实例
web_visualizer = WebVisualizer()

# 导出关键函数，方便外部调用
update_status = web_visualizer.update_status
add_message = web_visualizer.add_message
# 使用不同的名称避免递归调用
update_document_status = web_visualizer.set_document_status
update_progress = web_visualizer.update_progress

def start_web_server(port=8080, host='localhost', open_browser=True):
    """
    启动Web可视化服务器的便捷函数
    
    Args:
        port: 端口号，默认为8080
        host: 主机地址，默认为localhost
        open_browser: 是否自动打开浏览器，默认为True
        
    Returns:
        bool: 是否成功启动
    """
    try:
        # 设置可视化器的主机和端口
        web_visualizer.host = host
        web_visualizer.port = port
        
        # 启动服务器
        web_visualizer.start(open_browser=open_browser)
        
        logger.info(f"Web服务器已启动: http://{host}:{port}")
        return True
    except Exception as e:
        logger.error(f"启动Web服务器失败: {e}")
        return False 