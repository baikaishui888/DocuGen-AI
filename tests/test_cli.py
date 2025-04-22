#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
命令行交互界面测试模块
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

from docugen.utils.cli import CommandLineInterface, cli
from docugen.utils.progress import ProgressManager, ProgressStatus


class TestCommandLineInterface(unittest.TestCase):
    """命令行交互界面测试类"""

    def setUp(self):
        """测试前准备"""
        # 创建一个带有StringIO的测试控制台对象，用于捕获输出
        self.mock_stdout = io.StringIO()
        self.cli = CommandLineInterface()
        # 使用补丁替换控制台对象
        self.original_console = self.cli.console
        self.cli.console = MagicMock()
        self.cli.console.print = lambda *args, **kwargs: self.mock_stdout.write(str(args[0]) + "\n")

    def tearDown(self):
        """测试后清理"""
        # 恢复原始控制台对象
        self.cli.console = self.original_console
        self.mock_stdout.close()

    def test_show_title(self):
        """测试显示标题"""
        self.cli.show_title()
        output = self.mock_stdout.getvalue()
        # 验证标题包含DocuGen AI关键词
        self.assertIn("DocuGen AI", output)

    @patch('docugen.utils.cli.Prompt.ask')
    def test_get_input(self, mock_ask):
        """测试获取用户输入"""
        # 设置模拟的返回值
        mock_ask.return_value = "测试项目"
        
        # 调用被测试的方法
        result = self.cli.get_input("请输入项目名称")
        
        # 验证返回值
        self.assertEqual(result, "测试项目")
        # 验证mock方法被调用
        mock_ask.assert_called_once_with("请输入项目名称", default=None)

    @patch('docugen.utils.cli.Confirm.ask')
    def test_confirm(self, mock_confirm):
        """测试用户确认"""
        # 设置模拟的返回值
        mock_confirm.return_value = True
        
        # 调用被测试的方法
        result = self.cli.confirm("是否继续？")
        
        # 验证返回值
        self.assertTrue(result)
        # 验证mock方法被调用
        mock_confirm.assert_called_once_with("是否继续？", default=True)

    def test_show_status(self):
        """测试显示状态信息"""
        # 测试成功状态
        self.cli.show_status("测试成功", True)
        output_success = self.mock_stdout.getvalue()
        self.assertIn("测试成功", output_success)
        
        # 清空输出缓冲
        self.mock_stdout = io.StringIO()
        self.cli.console.print = lambda *args, **kwargs: self.mock_stdout.write(str(args[0]) + "\n")
        
        # 测试失败状态
        self.cli.show_status("测试失败", False)
        output_failure = self.mock_stdout.getvalue()
        self.assertIn("测试失败", output_failure)

    def test_show_warning(self):
        """测试显示警告信息"""
        self.cli.show_warning("测试警告")
        output = self.mock_stdout.getvalue()
        self.assertIn("测试警告", output)

    def test_show_error(self):
        """测试显示错误信息"""
        # 测试无错误代码
        self.cli.show_error("测试错误")
        output1 = self.mock_stdout.getvalue()
        self.assertIn("测试错误", output1)
        
        # 清空输出缓冲
        self.mock_stdout = io.StringIO()
        self.cli.console.print = lambda *args, **kwargs: self.mock_stdout.write(str(args[0]) + "\n")
        
        # 测试有错误代码
        self.cli.show_error("测试错误", 1001)
        output2 = self.mock_stdout.getvalue()
        self.assertIn("测试错误", output2)
        self.assertIn("1001", output2)

    @patch('docugen.utils.cli.Prompt.ask')
    def test_show_menu(self, mock_ask):
        """测试显示菜单"""
        # 设置模拟的返回值
        mock_ask.return_value = "2"
        
        options = ["选项1", "选项2", "选项3"]
        result = self.cli.show_menu(options, "测试菜单")
        
        # 验证返回值
        self.assertEqual(result, 2)
        
        # 验证输出
        output = self.mock_stdout.getvalue()
        self.assertIn("测试菜单", output)
        self.assertIn("1. 选项1", output)
        self.assertIn("2. 选项2", output)
        self.assertIn("3. 选项3", output)


if __name__ == '__main__':
    unittest.main() 