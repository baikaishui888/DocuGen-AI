"""
变量替换引擎模块
负责处理文档中的变量定义和替换
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set


class VariableManager:
    """
    变量管理器
    负责解析、存储和替换文档中的变量
    """
    
    # 变量定义格式：${变量名:默认值}或${变量名}
    VAR_PATTERN = r'\${([a-zA-Z0-9_]+)(?::([^}]*))?}'
    
    # 变量块定义格式
    VAR_BLOCK_START = "```variables"
    VAR_BLOCK_END = "```"
    
    def __init__(self):
        """初始化变量管理器"""
        self.logger = logging.getLogger("docugen.variable")
        self.variables: Dict[str, Any] = {}
    
    def extract_variables(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """
        从文档内容中提取变量定义
        
        Args:
            content: 文档内容
            
        Returns:
            清理后的内容和提取的变量字典
        """
        # 提取变量块
        variables = {}
        cleaned_content = content
        
        # 首先提取变量块中定义的变量
        var_blocks = self._extract_variable_blocks(content)
        for block in var_blocks:
            block_vars = self._parse_variable_block(block)
            variables.update(block_vars)
            # 从内容中移除变量块
            cleaned_content = cleaned_content.replace(f"{self.VAR_BLOCK_START}\n{block}\n{self.VAR_BLOCK_END}", "").strip()
        
        # 更新内部变量存储
        self.variables.update(variables)
        
        return cleaned_content, variables
    
    def _extract_variable_blocks(self, content: str) -> List[str]:
        """
        提取文档中的变量定义块
        
        Args:
            content: 文档内容
            
        Returns:
            变量块列表
        """
        blocks = []
        lines = content.split('\n')
        in_block = False
        current_block = []
        
        for line in lines:
            if line.strip() == self.VAR_BLOCK_START:
                in_block = True
                current_block = []
            elif line.strip() == self.VAR_BLOCK_END and in_block:
                in_block = False
                blocks.append('\n'.join(current_block))
            elif in_block:
                current_block.append(line)
        
        return blocks
    
    def _parse_variable_block(self, block: str) -> Dict[str, Any]:
        """
        解析变量定义块中的变量
        
        Args:
            block: 变量块内容
            
        Returns:
            变量字典
        """
        variables = {}
        lines = block.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # 尝试解析变量定义（格式：变量名 = 值）
            parts = line.split('=', 1)
            if len(parts) == 2:
                name = parts[0].strip()
                value = parts[1].strip()
                
                # 如果值被引号包围，去掉引号
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                variables[name] = value
        
        return variables
    
    def replace_variables(self, content: str) -> str:
        """
        替换文档中的变量引用
        
        Args:
            content: 包含变量引用的文档内容
            
        Returns:
            替换后的内容
        """
        def _replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            
            if var_name in self.variables:
                return str(self.variables[var_name])
            return default_value
        
        # 替换变量引用
        return re.sub(self.VAR_PATTERN, _replace_var, content)
    
    def set_variable(self, name: str, value: Any) -> None:
        """
        设置变量值
        
        Args:
            name: 变量名
            value: 变量值
        """
        self.variables[name] = value
        self.logger.debug(f"设置变量: {name} = {value}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        获取变量值
        
        Args:
            name: 变量名
            default: 默认值
            
        Returns:
            变量值或默认值
        """
        return self.variables.get(name, default)
    
    def clear_variables(self) -> None:
        """清除所有变量"""
        self.variables.clear()
    
    def find_undefined_variables(self, content: str) -> Set[str]:
        """
        查找内容中引用但未定义的变量
        
        Args:
            content: 文档内容
            
        Returns:
            未定义的变量名集合
        """
        # 提取所有变量引用
        references = set(re.findall(self.VAR_PATTERN, content))
        # 获取已定义的变量
        defined = set(self.variables.keys())
        
        # 返回未定义的变量名
        undefined = {ref[0] for ref in references if ref[0] not in defined}
        return undefined


class TemplateVariableProcessor:
    """
    模板变量处理器
    将变量管理器与模板系统集成
    """
    
    def __init__(self):
        """初始化模板变量处理器"""
        self.logger = logging.getLogger("docugen.variable.processor")
        self.variable_manager = VariableManager()
    
    def process_content(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """
        处理文档内容，提取变量并进行替换
        
        Args:
            content: 原始文档内容
            
        Returns:
            处理后的内容和提取的变量字典
        """
        # 提取变量
        cleaned_content, variables = self.variable_manager.extract_variables(content)
        
        # 替换变量引用
        processed_content = self.variable_manager.replace_variables(cleaned_content)
        
        return processed_content, variables
    
    def get_template_context(self, additional_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取用于模板渲染的上下文
        
        Args:
            additional_vars: 附加的变量
            
        Returns:
            模板上下文（变量字典）
        """
        context = self.variable_manager.variables.copy()
        
        if additional_vars:
            context.update(additional_vars)
            
        return context
    
    def validate_content(self, content: str) -> List[str]:
        """
        验证内容中的变量引用是否都已定义
        
        Args:
            content: 文档内容
            
        Returns:
            错误消息列表
        """
        undefined = self.variable_manager.find_undefined_variables(content)
        
        errors = []
        if undefined:
            for var_name in sorted(undefined):
                errors.append(f"变量 '${{{var_name}}}' 未定义")
        
        return errors 