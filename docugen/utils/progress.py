#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
进度显示系统模块
实现文档生成进度的可视化显示
"""

import time
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

# 进度状态枚举
class ProgressStatus(str, Enum):
    """进度状态枚举"""
    PENDING = "pending"  # 待处理
    READY = "ready"      # 就绪
    GENERATING = "generating"  # 生成中
    COMPLETED = "completed"    # 完成
    FAILED = "failed"    # 失败
    PAUSED = "paused"    # 暂停
    SAVED = "saved"      # 已保存 - 新增状态用于追踪文档保存
    
class ProgressManager:
    """进度管理器，提供高级进度跟踪功能"""
    
    def __init__(self, console: Optional[Console] = None):
        """初始化进度管理器
        
        Args:
            console: 控制台对象，为None时创建新实例
        """
        self.console = console or Console()
        self._progress = self._create_progress()
        self._tasks = {}  # 存储任务ID和对应任务信息的字典
        self._current_step = 0
        self._total_steps = 0
        self._current_task = ""
        self._status = ProgressStatus.READY
        self._save_paths = {}  # 存储文档类型和对应保存路径 - 新增
        
    def _create_progress(self) -> Progress:
        """创建进度条对象
        
        Returns:
            Progress对象
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[bold]{task.fields[status]}"),
            console=self.console
        )
    
    def reset(self):
        """重置进度管理器状态"""
        self._tasks = {}
        self._current_step = 0
        self._total_steps = 0
        self._current_task = ""
        self._status = ProgressStatus.READY
        self._save_paths = {}  # 重置保存路径
        # 重新创建进度对象
        self._progress = self._create_progress()
    
    def update_status(self, status: ProgressStatus):
        """更新整体状态
        
        Args:
            status: 新状态
        """
        self._status = status
    
    def set_current_step(self, current: int, total: int):
        """设置当前步骤
        
        Args:
            current: 当前步骤
            total: 总步骤数
        """
        self._current_step = current
        self._total_steps = total
    
    def update_current_task(self, task_description: str):
        """更新当前任务描述
        
        Args:
            task_description: 任务描述
        """
        self._current_task = task_description
        
    def add_task(self, description: str, total: int = 100, 
                 status: str = "准备中", **kwargs) -> str:
        """添加新任务到进度管理器
        
        Args:
            description: 任务描述
            total: 任务总步数
            status: 初始状态文本
            
        Returns:
            任务ID
        """
        task_id = self._progress.add_task(
            description, 
            total=total, 
            status=status, 
            **kwargs
        )
        self._tasks[task_id] = {
            "description": description,
            "total": total,
            "current": 0,
            "status": ProgressStatus.PENDING
        }
        return task_id
        
    def update_task(self, task_id: str, advance: int = 0, 
                   status: Optional[ProgressStatus] = None, **kwargs):
        """更新任务进度
        
        Args:
            task_id: 任务ID
            advance: 前进步数
            status: 新状态
        """
        update_kwargs = {}
        
        # 更新步数
        if advance > 0:
            update_kwargs["advance"] = advance
            self._tasks[task_id]["current"] += advance
            
        # 更新状态
        if status:
            self._tasks[task_id]["status"] = status
            status_text = self._get_status_text(status)
            update_kwargs["status"] = status_text
            
        # 更新其他字段
        update_kwargs.update(kwargs)
        
        # 应用更新
        self._progress.update(task_id, **update_kwargs)
        
    def _get_status_text(self, status: ProgressStatus) -> str:
        """根据状态获取格式化的状态文本
        
        Args:
            status: 状态枚举值
            
        Returns:
            格式化后的状态文本
        """
        if status == ProgressStatus.PENDING:
            return "[yellow]准备中[/yellow]"
        elif status == ProgressStatus.READY:
            return "[cyan]就绪[/cyan]"
        elif status == ProgressStatus.GENERATING:
            return "[blue]生成中[/blue]"
        elif status == ProgressStatus.COMPLETED:
            return "[green]已完成[/green]"
        elif status == ProgressStatus.FAILED:
            return "[red]失败[/red]"
        elif status == ProgressStatus.PAUSED:
            return "[yellow]已暂停[/yellow]"
        elif status == ProgressStatus.SAVED:  # 新增状态显示
            return "[green]已保存[/green]"
        return str(status)
    
    def set_task_description(self, task_id: str, description: str):
        """设置任务描述
        
        Args:
            task_id: 任务ID
            description: 新描述
        """
        self._progress.update(task_id, description=description)
        self._tasks[task_id]["description"] = description
        
    def get_task_status(self, task_id: str) -> ProgressStatus:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态
        """
        return self._tasks[task_id]["status"]
        
    def get_completion_percentage(self, task_id: str) -> float:
        """获取任务完成百分比
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务完成百分比
        """
        if task_id not in self._tasks:
            return 0.0
            
        task = self._tasks[task_id]
        if task["total"] <= 0:
            return 100.0 if task["status"] == ProgressStatus.COMPLETED else 0.0
            
        return (task["current"] / task["total"]) * 100
    
    def update_save_status(self, doc_type: str, save_path: str):
        """更新文档保存状态
        
        Args:
            doc_type: 文档类型
            save_path: 文档保存路径
        """
        # 存储保存路径
        self._save_paths[doc_type] = save_path
        
        # 查找与文档类型关联的任务，并更新状态
        for task_id, task in self._tasks.items():
            if task["description"].endswith(doc_type) or doc_type in task["description"]:
                self.update_task(
                    task_id,
                    status=ProgressStatus.SAVED,
                    save_path=save_path  # 在任务字段中存储保存路径
                )
                break
        
        # 打印保存信息
        self.console.print(f"[green]文档已保存:[/green] [bold]{doc_type}[/bold] -> {save_path}")
    
    def update_task_status(self, doc_type: str, status: str, message: str = ""):
        """更新与文档类型关联的任务状态
        
        Args:
            doc_type: 文档类型
            status: 状态字符串（"COMPLETED", "FAILED", "GENERATING"等）
            message: 状态消息
        """
        # 将状态字符串转换为ProgressStatus枚举
        try:
            progress_status = getattr(ProgressStatus, status.lower())
        except:
            progress_status = ProgressStatus.PENDING
            
        # 查找与文档类型关联的任务，并更新状态
        for task_id, task in self._tasks.items():
            if task["description"].endswith(doc_type) or doc_type in task["description"]:
                self.update_task(
                    task_id,
                    status=progress_status,
                    message=message  # 在任务字段中存储消息
                )
                
                # 如果是失败状态，打印错误信息
                if status.lower() == "failed" and message:
                    self.console.print(f"[red]错误:[/red] {doc_type} - {message}")
                break
    
    def start(self):
        """启动进度显示"""
        self._progress.start()
        
    def stop(self):
        """停止进度显示"""
        self._progress.stop()
        
    def get_summary_table(self) -> Table:
        """获取进度摘要表格
        
        Returns:
            Rich表格对象
        """
        table = Table(title="文档生成状态摘要")
        table.add_column("文档类型", style="cyan")
        table.add_column("状态", style="bold")
        table.add_column("完成度", justify="right")
        table.add_column("保存路径", style="green")  # 新增列
        
        for task_id, task in self._tasks.items():
            description = task["description"]
            status = self._get_status_text(task["status"])
            percentage = f"{self.get_completion_percentage(task_id):.1f}%"
            
            # 查找文档类型
            doc_type = None
            for dt in self._save_paths.keys():
                if dt in description:
                    doc_type = dt
                    break
                    
            # 显示保存路径（如果有）
            save_path = self._save_paths.get(doc_type, "") if doc_type else ""
            
            table.add_row(description, status, percentage, save_path)
            
        return table
        
    def run_with_progress(self, tasks: List[Dict[str, Any]], 
                         task_func: Callable[[Dict[str, Any], str], None]):
        """使用进度条运行任务列表
        
        Args:
            tasks: 任务列表，每个任务是一个字典
            task_func: 任务函数，接收任务字典和任务ID参数
        """
        self._progress.start()
        
        try:
            # 创建所有任务
            for task in tasks:
                desc = task.get("description", "任务")
                total = task.get("total", 100)
                task_id = self.add_task(desc, total=total)
                task["id"] = task_id
            
            # 运行所有任务
            for task in tasks:
                task_id = task["id"]
                try:
                    task_func(task, task_id)
                except Exception as e:
                    self.update_task(task_id, status=ProgressStatus.FAILED)
                    self.console.print(f"[red]任务失败:[/red] {task['description']} - {str(e)}")
        
        finally:
            self._progress.stop()
            
    def get_save_path(self, doc_type: str) -> str:
        """获取文档保存路径
        
        Args:
            doc_type: 文档类型
            
        Returns:
            保存路径，如果未保存则返回空字符串
        """
        return self._save_paths.get(doc_type, "")
    
    def get_all_save_paths(self) -> Dict[str, str]:
        """获取所有保存路径
        
        Returns:
            文档类型到保存路径的映射
        """
        return self._save_paths.copy()

# 创建默认实例方便使用
progress_manager = ProgressManager() 