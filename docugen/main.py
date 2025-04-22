#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DocuGen AI - 智能文档生成助手
入口模块
"""

import os
import sys
import time
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from docugen.core.generator import DocumentGenerator
from docugen.core.pipeline import DocumentPipeline
from docugen.utils.cli import CommandLineInterface
from docugen.utils.i18n import I18nManager
from docugen.utils.web_server import web_visualizer, update_document_status, start_web_server
from docugen.utils.logger import LogManager
from docugen.utils.progress import progress_manager, ProgressStatus, ProgressManager
from docugen.utils.debug_tracer import model_tracer
from docugen.config import Config

# 获取I18n管理器
i18n = I18nManager()
_ = i18n.get_translator()

# 获取CLI界面
cli = CommandLineInterface()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='DocuGen AI - 智能文档生成工具')
    
    # 基本参数
    parser.add_argument('--project', '-p', type=str, help='项目名称')
    parser.add_argument('--description', type=str, help='项目描述')
    parser.add_argument('--input', '-i', type=str, help='输入文件路径（包含项目信息的JSON文件）')
    
    # API相关参数
    parser.add_argument('--model', '-m', type=str, help='指定使用的模型名称')
    parser.add_argument('--api-base', type=str, help='自定义API基础URL')
    parser.add_argument('--temperature', type=float, help='模型温度参数(0-1)')
    
    # 输出相关参数
    parser.add_argument('--output', '-o', type=str, help='输出目录')
    parser.add_argument('--format', '-f', choices=['md', 'html', 'pdf'], default='md', help='输出格式')
    
    # 界面相关参数
    parser.add_argument('--web', '-w', action='store_true', help='启用Web界面')
    parser.add_argument('--port', type=int, default=8080, help='Web服务器端口')
    
    # 流程相关参数
    parser.add_argument('--doc-type', '-d', type=str, help='指定生成的文档类型')
    parser.add_argument('--all', '-a', action='store_true', help='生成所有文档')
    
    # 调试参数
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--debug-model', action='store_true', help='启用模型输入输出调试')
    
    return parser.parse_args()

def check_environment():
    """检查环境配置"""
    # 检查API密钥
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        cli.show_error(_("errors.api_key_not_set", "未设置OPENAI_API_KEY环境变量"), 1001)
        cli.console.print(_("ui.api_key_instruction", "请使用以下命令设置API密钥:"))
        cli.console.print("  export OPENAI_API_KEY='your-key'  # Linux/macOS")
        cli.console.print("  set OPENAI_API_KEY=your-key  # Windows")
        return False
    
    # 检查提示词目录
    config = Config()
    prompts_dir = Path(config.get("paths.prompts_dir"))
    
    # 如果是相对路径，计算绝对路径
    if not prompts_dir.is_absolute():
        if str(prompts_dir).startswith("../"):
            # 相对于docugen目录的上级目录（项目根目录）
            prompts_dir = Path(__file__).parent.parent / str(prompts_dir)[3:]
        elif str(prompts_dir).startswith("./"):
            # 相对于当前目录
            prompts_dir = Path(__file__).parent / str(prompts_dir)[2:]
        else:
            # 简单的相对路径
            prompts_dir = Path(__file__).parent / prompts_dir
    
    if not prompts_dir.exists() or not prompts_dir.is_dir():
        cli.show_warning(_("errors.prompt_dir_not_found", f"提示词目录不存在: {prompts_dir}"))
        cli.console.print(_("ui.prompt_dir_instruction", "请确保提示词目录存在，或使用--prompts参数指定正确的路径"))
        return False
        
    return True

def setup_environment(args):
    """设置环境变量和配置"""
    # 设置API相关环境变量
    if args.model:
        os.environ['OPENAI_MODEL_NAME'] = args.model
    
    if args.api_base:
        os.environ['OPENAI_API_BASE'] = args.api_base
    
    # 设置调试相关环境变量
    if args.debug:
        os.environ['DOCUGEN_DEBUG'] = 'true'
        
    if args.debug_model:
        os.environ['DOCUGEN_DEBUG_MODEL'] = 'true'
    
    # 初始化配置
    config = Config()
    
    # 设置输出目录
    if args.output:
        config.set('paths.output_dir', args.output)
    
    # 设置Web端口
    if args.port:
        config.set('web.port', args.port)
    
    # 设置温度参数
    if args.temperature is not None:
        config.set('api.temperature', args.temperature)
    
    return config

def load_project_info(args):
    """
    加载项目信息，优先从JSON文件加载，其次从命令行参数加载，最后请求用户输入
    :param args: 命令行参数
    :return: 项目信息字典
    """
    logger = logging.getLogger("docugen.main")
    
    # 优先从JSON文件加载项目信息
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"错误: 输入文件不存在: {args.input}")
            sys.exit(1)
            
        with open(input_path, 'r', encoding='utf-8') as f:
            try:
                logger.info(f"从 {args.input} 加载项目信息")
                return json.load(f)
            except json.JSONDecodeError:
                print(f"错误: 无法解析输入文件: {args.input}")
                sys.exit(1)
    
    # 否则使用默认项目信息或请求用户输入
    project_info = {}
    
    if args.project:
        project_info['name'] = args.project
    else:
        project_info['name'] = cli.input_text("请输入项目名称: ")
    
    if args.description:
        project_info['description'] = args.description
    else:
        project_info['description'] = cli.input_text("请输入项目描述: ")
    
    # 添加创建时间
    project_info['created_at'] = datetime.now().isoformat()
    
    return project_info

def main():
    """主入口函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 设置环境和配置
    config = setup_environment(args)
    
    # 设置日志
    log_manager = LogManager(debug_mode=args.debug)
    logger = logging.getLogger("docugen.main")
    
    # 初始化进度管理器
    progress_manager.reset()
    
    # 初始化model_tracer（即使不启用）
    if os.environ.get("DOCUGEN_DEBUG_MODEL") == "true" or args.debug_model:
        model_tracer.enable()
        logger.info("已启用模型调试模式，将显示模型输入和输出内容")
    
    # 显示启动信息
    logger.info(f"DocuGen AI 启动中...")
    
    try:
        # 加载项目信息
        project_info = load_project_info(args)
        
        # 显示项目信息
        project_name = project_info.get('name', project_info.get('project_name', '未命名项目'))
        logger.info(f"项目名称: {project_name}")
        
        # 启动Web界面（如果指定）
        if args.web:
            web_port = config.get('web.port', 8080)
            logger.info(f"启动Web界面，端口: {web_port}")
            # 使用从web_server模块导入的函数
            start_web_server(port=web_port, host='localhost')
        
        # 初始化文档生成器
        generator = DocumentGenerator(
            model_name=args.model,
            debug_mode=args.debug_model or config.is_model_debug_enabled(),
            progress_manager=progress_manager
        )
        
        # 根据参数确定生成单个文档还是所有文档
        if args.doc_type:
            # 生成单个文档
            doc_type = args.doc_type
            logger.info(f"生成单个文档: {doc_type}")
            
            # 更新进度
            progress_manager.update_status(ProgressStatus.GENERATING)
            progress_manager.set_current_step(1, 1)
            progress_manager.update_current_task(f"生成 {doc_type} 文档")
            
            # 为单个文档类型生成内容并保存
            content = generator.generate_document(project_info, doc_type)
            output_file = generator.file_manager.save_document(
                project_name, 
                doc_type, 
                content
            )
            logger.info(f"已保存文档: {output_file}")
            
            # 更新进度
            progress_manager.update_status(ProgressStatus.COMPLETED)
            
        else:
            # 生成所有文档
            logger.info("生成所有文档")
            
            # 创建项目目录
            generator.file_manager.create_project_dir(project_name)
            
            # 调用流水线生成所有文档
            generator.pipeline.run(project_info)
        
    except Exception as e:
        logger.error(f"发生错误: {e}")
        
        # 更新进度
        progress_manager.update_status(ProgressStatus.FAILED)
        progress_manager.update_current_task(f"错误: {e}")
        
        # 在调试模式下显示异常堆栈
        if args.debug:
            logger.exception("详细错误信息:")
        
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 