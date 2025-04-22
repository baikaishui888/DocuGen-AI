"""
测试配置模块
为测试提供统一的配置
"""

import os
from pathlib import Path
import json
import unittest
from unittest.mock import patch

# 测试目录
TEST_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# 测试输出目录
TEST_OUTPUT_DIR = TEST_DIR / "test_output"

# 测试提示词目录
TEST_PROMPTS_DIR = TEST_DIR / "test_prompts"

# 确保测试目录存在
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
os.makedirs(TEST_PROMPTS_DIR, exist_ok=True)

# 创建测试提示词
def create_test_prompts():
    """创建测试用的提示词文件"""
    prompts = {
        "brainstorm.md": """# 构思梳理提示词
请为项目进行构思梳理，包括核心功能、用户需求和技术考量。

## 项目名称
{{project_name}}

## 输出要求
- 项目概述
- 核心功能
- 用户需求
- 技术考量
""",
        "prd.md": """# 产品需求文档提示词
请为项目创建产品需求文档，详细描述功能和非功能需求。

## 项目名称
{{project_name}}

## 输出要求
- 产品概述
- 功能需求
- 非功能需求
""",
        "workflow.md": """# 应用流程文档提示词
请为项目设计应用流程，说明文档生成过程和用户交互方式。

## 项目名称
{{project_name}}

## 输出要求
- 文档生成流程
- 用户交互流程
- 错误处理流程
"""
    }
    
    # 写入提示词文件
    for filename, content in prompts.items():
        with open(TEST_PROMPTS_DIR / filename, "w", encoding="utf-8") as f:
            f.write(content)

# 创建测试配置文件
def create_test_config():
    """创建测试配置文件"""
    config = {
        "api": {
            "model": "gpt-4",
            "max_tokens": 1000,
            "temperature": 0.5,
            "timeout": 30,
            "max_retries": 2
        },
        "paths": {
            "prompts_dir": str(TEST_PROMPTS_DIR),
            "output_dir": str(TEST_OUTPUT_DIR)
        },
        "logging": {
            "level": "INFO",
            "file": "tests/test_output/docugen_test.log"
        }
    }
    
    # 写入配置文件
    config_path = TEST_OUTPUT_DIR / "test_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    return config_path

# 初始化测试环境
def init_test_env():
    """初始化测试环境"""
    create_test_prompts()
    config_path = create_test_config()
    return config_path

# 设置测试环境
def init_test_env():
    # 设置项目根目录
    global TEST_ROOT_DIR, TEST_OUTPUT_DIR, TEST_PROMPTS_DIR
    TEST_ROOT_DIR = Path(__file__).parent
    TEST_OUTPUT_DIR = TEST_ROOT_DIR / "test_output"
    TEST_PROMPTS_DIR = TEST_ROOT_DIR / "test_prompts"
    
    # 创建测试目录
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)
    TEST_PROMPTS_DIR.mkdir(exist_ok=True)
    
    # 添加项目根目录到模块搜索路径
    import sys
    project_root = TEST_ROOT_DIR.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

# 初始化测试环境
init_test_env()

# 导入被测试模块
from docugen.config import Config


class TestConfig(unittest.TestCase):
    """配置模块测试用例"""
    
    def setUp(self):
        """测试前准备"""
        # 备份环境变量
        self.original_env = os.environ.copy()
        
        # 创建测试配置文件
        self.config_path = create_test_config()
        
        # 创建一个新的配置实例
        # 注意：由于Config是单例模式，需要重置内部状态
        Config._instance = None
        Config._initialized = False
        self.config = Config()
        
    def tearDown(self):
        """测试后清理"""
        # 恢复环境变量
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # 如果需要，可以删除测试配置文件
        if hasattr(self, 'config_path') and self.config_path.exists():
            self.config_path.unlink()
    
    def test_default_config(self):
        """测试默认配置值"""
        self.assertEqual(self.config.get("api.model"), "gpt-4")
        self.assertEqual(self.config.get("api.max_tokens"), 4000)
        self.assertEqual(self.config.get("api.temperature"), 0.7)
    
    def test_load_config(self):
        """测试加载配置文件"""
        # 加载测试配置文件
        self.config.load_config(str(self.config_path))
        
        # 验证配置是否正确加载
        self.assertEqual(self.config.get("api.model"), "gpt-4")
        self.assertEqual(self.config.get("api.max_tokens"), 1000)
        self.assertEqual(self.config.get("api.temperature"), 0.5)
    
    def test_set_config(self):
        """测试设置配置值"""
        # 设置新值
        self.config.set("api.model", "gpt-3.5-turbo")
        self.config.set("api.temperature", 0.8)
        
        # 验证值已正确设置
        self.assertEqual(self.config.get("api.model"), "gpt-3.5-turbo")
        self.assertEqual(self.config.get("api.temperature"), 0.8)
    
    def test_get_api_key(self):
        """测试获取API密钥"""
        # 设置环境变量
        os.environ["OPENAI_API_KEY"] = "test-key-123"
        
        # 验证是否能正确获取
        self.assertEqual(self.config.get_api_key(), "test-key-123")
    
    def test_get_api_base_url(self):
        """测试获取API基础URL"""
        # 测试从环境变量获取
        os.environ["OPENAI_API_BASE"] = "https://test-api.example.com"
        self.assertEqual(self.config.get_api_base_url(), "https://test-api.example.com")
        
        # 测试从配置获取
        del os.environ["OPENAI_API_BASE"]
        self.config.set("api.base_url", "https://config-api.example.com")
        self.assertEqual(self.config.get_api_base_url(), "https://config-api.example.com")
    
    def test_get_model_name(self):
        """测试获取模型名称"""
        # 测试从环境变量获取
        os.environ["OPENAI_MODEL_NAME"] = "gpt-4-turbo"
        self.assertEqual(self.config.get_model_name(), "gpt-4-turbo")
        
        # 测试从配置获取
        del os.environ["OPENAI_MODEL_NAME"]
        self.config.set("api.model", "gpt-3.5-turbo")
        self.assertEqual(self.config.get_model_name(), "gpt-3.5-turbo")
        
        # 测试默认值
        self.config.set("api.model", None)
        self.assertEqual(self.config.get_model_name(), "gpt-4")

if __name__ == "__main__":
    unittest.main() 