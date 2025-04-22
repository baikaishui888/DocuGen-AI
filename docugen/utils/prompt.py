"""
提示词管理模块
负责加载、管理和验证各类文档生成的提示词
"""

import os
import logging
import re
from pathlib import Path
from typing import Dict, Optional, List, Tuple


class PromptManager:
    """
    提示词管理器
    加载并管理各类文档的生成提示词
    """
    
    # 默认提示词文件名映射
    DEFAULT_PROMPT_FILES = {
        'brainstorm': '0.构思梳理文档提示词.md',      # 构思梳理文档
        'requirement_confirm': '1.需求确认文档提示词.md',  # 需求确认文档
        'prd': '2.产品需求文档（PRD）提示词.md',     # 产品需求文档
        'workflow': '3.应用流程文档提示词.md',       # 应用流程文档
        'tech_stack': '4.涉及技术栈文档提示词.md',   # 技术栈文档
        'frontend': '5.前端设计文档提示词.md',       # 前端设计指南
        'backend': '6.后端设计文档提示词.md',        # 后端架构设计
        'dev_plan': '7.开发计划提示词.md'           # 开发计划
    }
    
    # 提示词结构验证规则
    PROMPT_STRUCTURE_RULES = {
        'min_length': 100,           # 最小内容长度（字符数）
        'required_sections': 1,      # 至少需要的段落数
        'required_headers': 1,       # 至少需要的标题数
        'required_patterns': [       # 必须包含的内容模式
            r'.*?标题|.*?title|.*?header|.*?提示词'  # 修改模式，放宽对标题的要求
        ],
        'forbidden_patterns': [      # 禁止包含的内容模式
            r'(?<!```)[<]script.*?[>].*?[<]/script[>](?!```)',  # 禁止非代码块中的script标签
            r'(?<!```)[<]iframe.*?[>].*?[<]/iframe[>](?!```)'   # 禁止非代码块中的iframe标签
        ]
    }
    
    def __init__(self, prompt_dir: str):
        """
        初始化提示词管理器
        :param prompt_dir: 提示词目录路径
        """
        # 转换相对路径为绝对路径
        if prompt_dir.startswith("./") or prompt_dir.startswith("../"):
            # 如果是相对路径，则相对于当前文件所在目录解析
            current_dir = Path(__file__).parent
            module_dir = current_dir.parent  # docugen目录
            project_root = module_dir.parent  # 项目根目录
            if prompt_dir.startswith("../"):
                # 如果是"../文档提示词"这样的路径，则是相对于docugen目录，指向项目根目录下的文件夹
                self.prompt_dir = (module_dir / prompt_dir).resolve()
            else:
                # 如果是"./文档提示词"这样的路径，则是相对于当前文件所在目录
                self.prompt_dir = (current_dir / prompt_dir[2:]).resolve()
        else:
            # 如果是绝对路径或者简单的相对路径（不带./或../前缀）
            self.prompt_dir = Path(prompt_dir)
        
        self.logger = logging.getLogger("docugen.prompt")
        
        # 存储已加载的提示词
        self.prompts: Dict[str, str] = {}
        
        # 检查目录是否存在
        if not self.prompt_dir.exists() or not self.prompt_dir.is_dir():
            self.logger.error(f"提示词目录不存在: {self.prompt_dir}")
            raise FileNotFoundError(f"提示词目录不存在: {self.prompt_dir}")
        
        # 加载提示词
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """加载所有提示词文件"""
        self.logger.info(f"从目录加载提示词: {self.prompt_dir}")
        
        loaded_count = 0
        for doc_type, filename in self.DEFAULT_PROMPT_FILES.items():
            prompt_path = self.prompt_dir / filename
            
            if not prompt_path.exists():
                self.logger.warning(f"提示词文件不存在: {prompt_path}")
                continue
                
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        # 验证提示词内容
                        is_valid, issues = self._validate_prompt_content(content, filename)
                        if is_valid:
                            self.prompts[doc_type] = content
                            loaded_count += 1
                        else:
                            self.logger.warning(f"提示词内容验证失败 {prompt_path}: {', '.join(issues)}")
                    else:
                        self.logger.warning(f"提示词文件为空: {prompt_path}")
            except Exception as e:
                self.logger.error(f"加载提示词文件失败 {prompt_path}: {str(e)}")
        
        self.logger.info(f"成功加载 {loaded_count} 个提示词")
    
    def _validate_prompt_content(self, content: str, filename: str) -> Tuple[bool, List[str]]:
        """
        验证提示词内容是否符合结构要求
        :param content: 提示词内容
        :param filename: 文件名（用于日志）
        :return: (是否有效, 问题列表)
        """
        issues = []
        
        # 检查最小长度
        if len(content) < self.PROMPT_STRUCTURE_RULES['min_length']:
            issues.append(f"提示词内容长度不足 ({len(content)} < {self.PROMPT_STRUCTURE_RULES['min_length']})")
        
        # 检查必要段落数
        paragraphs = re.split(r'\n\s*\n', content)
        if len(paragraphs) < self.PROMPT_STRUCTURE_RULES['required_sections']:
            issues.append(f"提示词段落数量不足 ({len(paragraphs)} < {self.PROMPT_STRUCTURE_RULES['required_sections']})")
        
        # 检查必要标题数
        headers = re.findall(r'^#+ .*$', content, re.MULTILINE)
        if len(headers) < self.PROMPT_STRUCTURE_RULES['required_headers']:
            issues.append(f"提示词标题数量不足 ({len(headers)} < {self.PROMPT_STRUCTURE_RULES['required_headers']})")
        
        # 检查必要内容模式
        for pattern in self.PROMPT_STRUCTURE_RULES['required_patterns']:
            if not re.search(pattern, content, re.IGNORECASE):
                issues.append(f"提示词缺少必要内容模式: {pattern}")
        
        # 检查禁止内容模式
        for pattern in self.PROMPT_STRUCTURE_RULES['forbidden_patterns']:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            if matches:
                issues.append(f"提示词包含禁止内容模式: {pattern}")
        
        return len(issues) == 0, issues
    
    def get_prompt(self, doc_type: str) -> Optional[str]:
        """
        获取指定文档类型的提示词
        :param doc_type: 文档类型
        :return: 提示词内容，如果不存在则返回None
        """
        return self.prompts.get(doc_type)
    
    def is_prompt_available(self, doc_type: str) -> bool:
        """
        检查指定文档类型的提示词是否可用
        :param doc_type: 文档类型
        :return: 提示词是否可用
        """
        return doc_type in self.prompts and bool(self.prompts[doc_type])
    
    def get_available_prompts(self) -> List[str]:
        """
        获取所有可用的提示词类型
        :return: 可用的提示词类型列表
        """
        return list(self.prompts.keys())
    
    def get_prompt_details(self) -> Dict[str, Dict]:
        """
        获取所有提示词的详细信息
        :return: 包含提示词详细信息的字典
        """
        details = {}
        for doc_type, content in self.prompts.items():
            # 提取提示词元数据和统计信息
            word_count = len(re.findall(r'\b\w+\b', content))
            headers = re.findall(r'^#+ .*$', content, re.MULTILINE)
            paragraphs = re.split(r'\n\s*\n', content)
            
            details[doc_type] = {
                'filename': self.DEFAULT_PROMPT_FILES[doc_type],
                'word_count': word_count,
                'header_count': len(headers),
                'paragraph_count': len(paragraphs),
                'first_header': headers[0] if headers else None
            }
        
        return details
    
    def reload_prompt(self, doc_type: str) -> bool:
        """
        重新加载指定文档类型的提示词
        :param doc_type: 文档类型
        :return: 是否成功重新加载
        """
        if doc_type not in self.DEFAULT_PROMPT_FILES:
            self.logger.error(f"无效的文档类型: {doc_type}")
            return False
            
        filename = self.DEFAULT_PROMPT_FILES[doc_type]
        prompt_path = self.prompt_dir / filename
        
        if not prompt_path.exists():
            self.logger.warning(f"提示词文件不存在: {prompt_path}")
            if doc_type in self.prompts:
                del self.prompts[doc_type]
            return False
            
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    # 验证提示词内容
                    is_valid, issues = self._validate_prompt_content(content, filename)
                    if is_valid:
                        self.prompts[doc_type] = content
                        self.logger.info(f"成功重新加载提示词: {doc_type}")
                        return True
                    else:
                        self.logger.warning(f"提示词内容验证失败 {prompt_path}: {', '.join(issues)}")
                        return False
                else:
                    self.logger.warning(f"提示词文件为空: {prompt_path}")
                    if doc_type in self.prompts:
                        del self.prompts[doc_type]
                    return False
        except Exception as e:
            self.logger.error(f"重新加载提示词失败 {doc_type}: {str(e)}")
            return False
    
    def update_prompt_file(self, doc_type: str, content: str) -> bool:
        """
        更新提示词文件内容
        :param doc_type: 文档类型
        :param content: 新的提示词内容
        :return: 是否成功更新
        """
        if doc_type not in self.DEFAULT_PROMPT_FILES:
            self.logger.error(f"无效的文档类型: {doc_type}")
            return False
        
        # 验证提示词内容
        filename = self.DEFAULT_PROMPT_FILES[doc_type]
        is_valid, issues = self._validate_prompt_content(content, filename)
        if not is_valid:
            self.logger.warning(f"提示词内容验证失败: {', '.join(issues)}")
            return False
            
        prompt_path = self.prompt_dir / filename
            
        try:
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新内存中的提示词
            self.prompts[doc_type] = content
            self.logger.info(f"成功更新提示词文件: {doc_type}")
            return True
        except Exception as e:
            self.logger.error(f"更新提示词文件失败 {doc_type}: {str(e)}")
            return False 