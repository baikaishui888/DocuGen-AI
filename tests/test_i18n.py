"""
测试国际化支持模块
验证多语言切换和翻译功能
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path

from docugen.utils.i18n import I18nManager, _


class TestI18nManager:
    """测试国际化管理器"""
    
    def setup_method(self):
        """初始化测试环境"""
        # 创建临时目录存放测试翻译文件
        self.test_dir = tempfile.mkdtemp()
        self.translations_dir = Path(self.test_dir) / "translations"
        self.translations_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试用的I18nManager实例
        self.i18n = I18nManager(lang="zh_CN", translations_dir=str(self.translations_dir))
    
    def teardown_method(self):
        """清理测试环境"""
        shutil.rmtree(self.test_dir)
    
    def test_default_translation_creation(self):
        """测试默认翻译文件创建"""
        # 验证是否自动创建了翻译文件
        zh_file = self.translations_dir / "zh_CN.json"
        en_file = self.translations_dir / "en_US.json"
        
        assert zh_file.exists(), "中文翻译文件应该被自动创建"
        assert en_file.exists(), "英文翻译文件应该被自动创建"
    
    def test_language_switching(self):
        """测试语言切换功能"""
        # 默认应该是中文
        assert self.i18n.get_current_language() == "zh_CN"
        
        # 切换到英文
        success = self.i18n.switch_language("en_US")
        assert success, "切换到英文应该成功"
        assert self.i18n.get_current_language() == "en_US"
        
        # 切换到不支持的语言
        success = self.i18n.switch_language("fr_FR")
        assert not success, "切换到不支持的语言应该失败"
        assert self.i18n.get_current_language() == "en_US", "语言应该保持不变"
        
        # 切换回中文
        success = self.i18n.switch_language("zh_CN")
        assert success, "切换回中文应该成功"
        assert self.i18n.get_current_language() == "zh_CN"
    
    def test_translation_retrieval(self):
        """测试翻译获取功能"""
        # 测试中文翻译
        assert self.i18n.get("ui.title") == "DocuGen AI 文档生成工具"
        assert self.i18n.get("documents.prd") == "产品需求文档"
        
        # 切换到英文后测试
        self.i18n.switch_language("en_US")
        assert self.i18n.get("ui.title") == "DocuGen AI Document Generator"
        assert self.i18n.get("documents.prd") == "Product Requirements Document"
        
        # 测试不存在的键
        assert self.i18n.get("non.existent.key") == "non.existent.key"
        assert self.i18n.get("non.existent.key", "默认值") == "默认值"
    
    def test_shorthand_function(self):
        """测试简写函数"""
        # 设置语言为中文
        self.i18n.switch_language("zh_CN")
        
        # 测试_()函数
        assert _("ui.yes") == "是"
        assert _("ui.no") == "否"
        
        # 切换到英文
        self.i18n.switch_language("en_US")
        assert _("ui.yes") == "Yes"
        assert _("ui.no") == "No"
    
    def test_get_all_keys(self):
        """测试获取所有翻译键功能"""
        keys = self.i18n.get_all_keys()
        
        # 验证基本的键是否存在
        assert "ui.title" in keys
        assert "documents.prd" in keys
        assert "status.completed" in keys
        
        # 测试前缀筛选
        ui_keys = self.i18n.get_all_keys("ui")
        assert all(k.startswith("ui.") for k in ui_keys)
        assert "ui.title" in ui_keys
        assert "documents.prd" not in ui_keys
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # 创建另一个实例，应该是同一个对象
        another_i18n = I18nManager()
        
        # 设置第一个实例的语言
        self.i18n.switch_language("en_US")
        
        # 另一个实例应该也是英文
        assert another_i18n.get_current_language() == "en_US"
        
        # 通过另一个实例切换回中文
        another_i18n.switch_language("zh_CN")
        
        # 第一个实例也应该变成中文
        assert self.i18n.get_current_language() == "zh_CN" 