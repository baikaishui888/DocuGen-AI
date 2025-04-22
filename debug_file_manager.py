"""
文件管理器调试脚本
"""

import logging
from pathlib import Path
from docugen.utils.file import FileManager

# 设置日志
logging.basicConfig(level=logging.INFO)

def debug_file_manager():
    """测试文件管理器的功能"""
    print("开始测试文件管理器...")
    
    # 创建文件管理器实例
    output_dir = "docugen/utils/output"
    file_manager = FileManager(output_dir)
    
    # 测试项目目录创建
    project_name = "调试测试项目"
    project_dir = file_manager.create_project_dir(project_name)
    print(f"项目目录创建结果: {project_dir}")
    
    # 测试文档保存
    doc_types = ['brainstorm', 'prd', 'workflow', 'tech_stack']
    for doc_type in doc_types:
        content = f"# 测试文档: {doc_type}\n\n这是{doc_type}类型的测试文档内容。"
        file_path = file_manager.save_document(project_name, doc_type, content)
        print(f"保存文档 {doc_type}: {file_path}")
    
    # 测试版本创建
    version_id = "v1.0"
    version_dir = file_manager.create_version_snapshot(project_name, version_id)
    print(f"版本快照创建结果: {version_dir}")
    
    # 列出版本
    versions = file_manager.list_versions(project_name)
    print(f"项目版本列表: {versions}")
    
    print("文件管理器测试完成.")

if __name__ == "__main__":
    debug_file_manager() 