#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
进度显示系统测试模块
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
import io

# 确保能够导入docugen模块
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from docugen.utils.progress import ProgressManager, ProgressStatus


class TestProgressManager(unittest.TestCase):
    """进度管理器测试类"""

    def setUp(self):
        """测试前准备"""
        # 创建一个模拟控制台对象
        self.mock_console = MagicMock()
        self.progress_manager = ProgressManager(console=self.mock_console)
        
        # 模拟Progress对象
        self.mock_progress = MagicMock()
        self.progress_manager._progress = self.mock_progress
        self.mock_progress.add_task.return_value = "task1"

    def test_add_task(self):
        """测试添加任务"""
        # 调用被测试的方法
        task_id = self.progress_manager.add_task("测试任务", 100, "准备中")
        
        # 验证任务ID
        self.assertEqual(task_id, "task1")
        
        # 验证任务被正确添加到内部字典
        self.assertIn(task_id, self.progress_manager._tasks)
        self.assertEqual(self.progress_manager._tasks[task_id]["description"], "测试任务")
        self.assertEqual(self.progress_manager._tasks[task_id]["total"], 100)
        self.assertEqual(self.progress_manager._tasks[task_id]["current"], 0)
        self.assertEqual(self.progress_manager._tasks[task_id]["status"], ProgressStatus.PENDING)
        
        # 验证底层Progress对象的方法被正确调用
        self.mock_progress.add_task.assert_called_once_with(
            "测试任务", total=100, status="准备中"
        )

    def test_update_task(self):
        """测试更新任务"""
        # 添加一个测试任务
        task_id = self.progress_manager.add_task("测试任务")
        
        # 调用被测试的方法
        self.progress_manager.update_task(
            task_id, 
            advance=10, 
            status=ProgressStatus.RUNNING
        )
        
        # 验证任务状态被正确更新
        self.assertEqual(self.progress_manager._tasks[task_id]["current"], 10)
        self.assertEqual(self.progress_manager._tasks[task_id]["status"], ProgressStatus.RUNNING)
        
        # 验证底层Progress对象的方法被正确调用
        self.mock_progress.update.assert_called_with(
            task_id, 
            advance=10, 
            status="[blue]处理中[/blue]"
        )

    def test_get_status_text(self):
        """测试获取状态文本"""
        # 测试各种状态的文本格式
        self.assertIn("yellow", self.progress_manager._get_status_text(ProgressStatus.PENDING))
        self.assertIn("blue", self.progress_manager._get_status_text(ProgressStatus.RUNNING))
        self.assertIn("green", self.progress_manager._get_status_text(ProgressStatus.SUCCESS))
        self.assertIn("red", self.progress_manager._get_status_text(ProgressStatus.FAILED))
        self.assertIn("yellow", self.progress_manager._get_status_text(ProgressStatus.PAUSED))

    def test_set_task_description(self):
        """测试设置任务描述"""
        # 添加一个测试任务
        task_id = self.progress_manager.add_task("原始描述")
        
        # 调用被测试的方法
        self.progress_manager.set_task_description(task_id, "新描述")
        
        # 验证任务描述被正确更新
        self.assertEqual(self.progress_manager._tasks[task_id]["description"], "新描述")
        
        # 验证底层Progress对象的方法被正确调用
        self.mock_progress.update.assert_called_with(task_id, description="新描述")

    def test_get_task_status(self):
        """测试获取任务状态"""
        # 添加一个测试任务
        task_id = self.progress_manager.add_task("测试任务")
        
        # 设置状态
        self.progress_manager._tasks[task_id]["status"] = ProgressStatus.SUCCESS
        
        # 调用被测试的方法
        status = self.progress_manager.get_task_status(task_id)
        
        # 验证返回的状态
        self.assertEqual(status, ProgressStatus.SUCCESS)

    def test_get_completion_percentage(self):
        """测试获取任务完成百分比"""
        # 添加一个测试任务
        task_id = self.progress_manager.add_task("测试任务", total=200)
        
        # 设置当前进度
        self.progress_manager._tasks[task_id]["current"] = 50
        
        # 调用被测试的方法
        percentage = self.progress_manager.get_completion_percentage(task_id)
        
        # 验证返回的百分比
        self.assertEqual(percentage, 25.0)  # 50/200 * 100 = 25%

    def test_start_and_stop(self):
        """测试启动和停止进度显示"""
        # 测试start方法
        progress = self.progress_manager.start()
        self.assertEqual(progress, self.mock_progress)
        
        # 测试stop方法
        self.progress_manager.stop()
        self.mock_progress.stop.assert_called_once()

    @patch('docugen.utils.progress.Table')
    def test_get_summary_table(self, mock_table):
        """测试获取摘要表格"""
        # 设置模拟表格对象
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        
        # 添加测试任务
        task_id1 = self.progress_manager.add_task("任务1", total=100)
        self.progress_manager._tasks[task_id1]["current"] = 50
        self.progress_manager._tasks[task_id1]["status"] = ProgressStatus.SUCCESS
        
        task_id2 = self.progress_manager.add_task("任务2", total=100)
        self.progress_manager._tasks[task_id2]["current"] = 20
        self.progress_manager._tasks[task_id2]["status"] = ProgressStatus.RUNNING
        
        # 调用被测试的方法
        table = self.progress_manager.get_summary_table()
        
        # 验证表格创建和行添加
        mock_table.assert_called_once_with(title="任务执行摘要")
        self.assertEqual(mock_table_instance.add_row.call_count, 2)

    def test_run_with_progress(self):
        """测试使用进度显示运行任务"""
        # 模拟任务列表
        tasks = [
            {"description": "任务1", "total": 100, "value": 1},
            {"description": "任务2", "total": 100, "value": 2}
        ]
        
        # 模拟任务处理函数
        task_func = MagicMock()
        
        # 模拟start方法返回上下文管理器
        self.mock_progress.__enter__ = MagicMock(return_value=self.mock_progress)
        self.mock_progress.__exit__ = MagicMock(return_value=None)
        
        # 调用被测试的方法
        self.progress_manager.run_with_progress(tasks, task_func)
        
        # 验证任务处理函数被调用
        self.assertEqual(task_func.call_count, 2)
        for args, kwargs in task_func.call_args_list:
            self.assertEqual(len(args), 2)  # 任务信息和任务ID


if __name__ == '__main__':
    unittest.main() 