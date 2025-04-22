"""
文档生成器调试脚本
"""

import logging
import json
from pathlib import Path
from docugen.core.generator import DocumentGenerator
from docugen.api.client import AIClient
from docugen.utils.prompt import PromptManager
from docugen.config import Config

# 设置日志
logging.basicConfig(level=logging.INFO)

def debug_generator():
    """测试文档生成器的功能"""
    print("开始测试文档生成器...")
    
    # 初始化配置
    config = Config()
    
    # 检查API密钥
    api_key = config.get_api_key()
    if not api_key:
        print("警告：未设置API密钥，将模拟API响应")
    
    # 获取提示词目录和输出目录
    prompts_dir = config.get("paths.prompts_dir")
    output_dir = config.get("paths.output_dir")
    
    print(f"提示词目录: {prompts_dir}")
    print(f"输出目录: {output_dir}")
    
    # 创建提示词管理器并验证提示词加载
    prompt_manager = PromptManager(prompts_dir)
    available_prompts = prompt_manager.get_available_prompts()
    print(f"可用提示词类型: {available_prompts}")
    
    # 检查第一个文档类型的提示词内容
    if available_prompts:
        first_prompt = prompt_manager.get_prompt(available_prompts[0])
        print(f"{available_prompts[0]}类型提示词前100个字符: {first_prompt[:100] if first_prompt else None}")
    
    # 创建虚拟项目信息
    project_info = {
        "name": "小红书爬虫_调试",
        "description": "用于调试的小红书爬虫项目",
        "timestamp": "2025-04-22 01:45:00"
    }
    
    # 初始化文档生成器
    model_name = config.get_model_name()
    print(f"使用模型: {model_name}")
    
    try:
        # 尝试创建文档生成器
        generator = DocumentGenerator(model_name)
        print(f"生成器初始化成功，使用模型: {generator.model_name}")
        
        # 检查文件管理器
        print(f"文件管理器输出目录: {generator.file_manager.output_dir}")
        
        # 创建项目目录
        project_dir = generator.file_manager.create_project_dir(project_info["name"])
        print(f"项目目录创建结果: {project_dir}")
        
        # 尝试生成一个简单的文档
        mock_content = f"# {project_info['name']}\n\n{project_info['description']}\n\n这是测试生成的文档。"
        file_path = generator.file_manager.save_document(project_info["name"], "brainstorm", mock_content)
        print(f"保存测试文档: {file_path}")
    
    except Exception as e:
        print(f"生成器初始化或测试失败: {str(e)}")
    
    print("文档生成器测试完成.")

if __name__ == "__main__":
    debug_generator() 