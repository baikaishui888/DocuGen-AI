"""
内容验证器模块
负责验证文档内容的一致性和完整性
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Optional


class ContentValidator:
    """
    内容验证器
    检查文档内容的一致性和完整性
    """
    
    def __init__(self):
        """初始化内容验证器"""
        self.logger = logging.getLogger("docugen.validator")
    
    def check_consistency(self, documents: Dict[str, str]) -> List[Dict]:
        """
        检查文档间的一致性
        :param documents: 文档内容字典 {doc_type: content}
        :return: 问题列表
        """
        issues = []
        
        # 检查文档引用关系
        if 'prd' in documents and 'dev_plan' in documents:
            issues.extend(self._check_references(documents['prd'], documents['dev_plan'], 
                                               '产品需求', '开发计划'))
        
        # 检查技术栈引用
        if 'tech_stack' in documents and 'backend' in documents:
            issues.extend(self._check_tech_consistency(documents['tech_stack'], documents['backend']))
        
        # 检查功能点一致性
        if 'prd' in documents and 'workflow' in documents:
            issues.extend(self._check_feature_consistency(documents['prd'], documents['workflow']))
        
        # 检查文档间的交叉引用
        issues.extend(self._check_cross_references(documents))
        
        # 检查链接完整性
        for doc_type, content in documents.items():
            issues.extend(self._check_link_integrity(content, doc_type))
        
        # 检查图表引用
        for doc_type, content in documents.items():
            issues.extend(self._check_figure_references(content, doc_type))
        
        return issues
    
    def _check_references(self, source_doc: str, target_doc: str, 
                        source_name: str, target_name: str) -> List[Dict]:
        """
        检查文档间引用关系
        :param source_doc: 源文档内容
        :param target_doc: 目标文档内容
        :param source_name: 源文档名称
        :param target_name: 目标文档名称
        :return: 问题列表
        """
        issues = []
        
        # 提取源文档中的关键要素
        source_elements = self._extract_key_elements(source_doc)
        
        # 检查这些要素在目标文档中是否存在引用
        for element in source_elements:
            if not self._element_exists(element, target_doc):
                issues.append({
                    "type": "missing_reference",
                    "source": source_name,
                    "target": target_name,
                    "element": element,
                    "message": f"'{element}' 在{source_name}中定义但在{target_name}中未引用"
                })
        
        return issues
    
    def _extract_key_elements(self, content: str) -> Set[str]:
        """
        提取文档中的关键要素
        :param content: 文档内容
        :return: 关键要素集合
        """
        elements = set()
        
        # 提取标题
        title_pattern = r'^#{1,3}\s+(.+)$'
        titles = re.findall(title_pattern, content, re.MULTILINE)
        for title in titles:
            # 排除常见的通用标题
            if not any(common in title.lower() for common in 
                     ['概述', '简介', '附录', '背景', '总结']):
                elements.add(title.strip())
        
        # 提取功能点
        feature_pattern = r'[-*]\s+(?:\*\*)?([^:：]+)(?:\*\*)?[:：]'
        features = re.findall(feature_pattern, content, re.MULTILINE)
        for feature in features:
            if len(feature.strip()) > 3:  # 忽略太短的内容
                elements.add(feature.strip())
        
        return elements
    
    def _element_exists(self, element: str, content: str) -> bool:
        """
        检查元素是否在内容中存在
        :param element: 要检查的元素
        :param content: 文档内容
        :return: 是否存在
        """
        # 宽松匹配，只要关键词在内容中即可
        return element.lower() in content.lower()
    
    def _check_tech_consistency(self, tech_doc: str, impl_doc: str) -> List[Dict]:
        """
        检查技术栈与实现文档的一致性
        :param tech_doc: 技术栈文档内容
        :param impl_doc: 实现文档内容
        :return: 问题列表
        """
        issues = []
        
        # 提取技术栈中的关键技术，分别匹配不同类型的标记
        patterns = [
            r'`([^`]+)`',           # 反引号包围
            r'"([^"]+)"',           # 双引号包围
            r"'([^']+)'",           # 单引号包围
            r'\*\*([^\*]+)\*\*'     # 粗体标记
        ]
        
        techs = []
        # 对每种模式单独匹配
        for pattern in patterns:
            matches = re.findall(pattern, tech_doc)
            techs.extend([match.strip() for match in matches if match])
        
        # 检查这些技术在实现文档中是否存在
        for tech in techs:
            if len(tech) > 3 and not self._element_exists(tech, impl_doc):
                issues.append({
                    "type": "technology_mismatch",
                    "tech": tech,
                    "message": f"技术 '{tech}' 在技术栈中定义但在实现文档中未使用"
                })
        
        return issues
    
    def _check_feature_consistency(self, prd_doc: str, workflow_doc: str) -> List[Dict]:
        """
        检查PRD文档与流程文档中功能点的一致性
        :param prd_doc: PRD文档内容
        :param workflow_doc: 流程文档内容
        :return: 问题列表
        """
        issues = []
        
        # 从PRD中提取功能描述
        feature_pattern = r'(?:功能|模块)[：:]\s*([^\n]+)'
        features = re.findall(feature_pattern, prd_doc)
        
        # 检查这些功能在流程文档中是否有对应的流程
        for feature in features:
            feature = feature.strip()
            if not self._element_exists(feature, workflow_doc):
                issues.append({
                    "type": "missing_workflow",
                    "feature": feature,
                    "message": f"功能 '{feature}' 在PRD中定义但在流程文档中没有对应流程"
                })
        
        return issues
    
    def _check_cross_references(self, documents: Dict[str, str]) -> List[Dict]:
        """
        检查文档间的交叉引用
        :param documents: 文档内容字典 {doc_type: content}
        :return: 问题列表
        """
        issues = []
        
        # 提取所有文档中的交叉引用
        cross_references = self._extract_cross_references(documents)
        
        # 验证交叉引用的有效性
        for doc_type, references in cross_references.items():
            for ref in references:
                target_doc = ref.get('target_doc')
                target_anchor = ref.get('target_anchor')
                
                # 检查引用的目标文档是否存在
                if target_doc and target_doc not in documents:
                    issues.append({
                        "type": "invalid_doc_reference",
                        "source_doc": doc_type,
                        "reference": ref.get('original'),
                        "message": f"引用了不存在的文档: {target_doc}"
                    })
                    continue
                
                # 检查引用的锚点是否存在于目标文档中
                if target_doc and target_anchor:
                    if not self._anchor_exists(target_anchor, documents.get(target_doc, '')):
                        issues.append({
                            "type": "invalid_anchor_reference",
                            "source_doc": doc_type,
                            "target_doc": target_doc,
                            "reference": ref.get('original'),
                            "message": f"在文档 {target_doc} 中引用了不存在的锚点: {target_anchor}"
                        })
        
        return issues
    
    def _extract_cross_references(self, documents: Dict[str, str]) -> Dict[str, List[Dict]]:
        """
        提取所有文档中的交叉引用
        :param documents: 文档内容字典 {doc_type: content}
        :return: 交叉引用字典 {doc_type: [{引用信息}]}
        """
        cross_references = {}
        
        # 引用模式: [显示文本](目标文档#锚点)
        reference_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        for doc_type, content in documents.items():
            cross_references[doc_type] = []
            
            matches = re.findall(reference_pattern, content)
            for display_text, target in matches:
                reference_info = {
                    'original': f'[{display_text}]({target})',
                    'display_text': display_text,
                    'target': target
                }
                
                # 解析目标引用
                if '#' in target:
                    doc_part, anchor_part = target.split('#', 1)
                    reference_info['target_doc'] = doc_part.strip() if doc_part else doc_type
                    reference_info['target_anchor'] = anchor_part.strip()
                else:
                    reference_info['target_doc'] = target.strip()
                    reference_info['target_anchor'] = None
                
                cross_references[doc_type].append(reference_info)
        
        return cross_references
    
    def _anchor_exists(self, anchor: str, content: str) -> bool:
        """
        检查锚点是否存在于文档中
        :param anchor: 锚点名称
        :param content: 文档内容
        :return: 锚点是否存在
        """
        # 转换锚点为标题格式并检查
        heading_pattern = r'^#{1,6}\s+' + re.escape(anchor) + r'\s*$'
        heading_match = re.search(heading_pattern, content, re.MULTILINE)
        
        # 检查ID格式的锚点
        id_pattern = r'<a\s+id=["\']' + re.escape(anchor) + r'["\'][^>]*>'
        id_match = re.search(id_pattern, content, re.IGNORECASE)
        
        return bool(heading_match or id_match)
    
    def _check_link_integrity(self, content: str, doc_type: str) -> List[Dict]:
        """
        检查文档中链接的完整性
        :param content: 文档内容
        :param doc_type: 文档类型
        :return: 问题列表
        """
        issues = []
        
        # 检查外部链接格式
        url_pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'
        url_matches = re.findall(url_pattern, content)
        
        for display_text, url in url_matches:
            # 检查URL格式
            if not self._is_valid_url(url):
                issues.append({
                    "type": "invalid_url_format",
                    "doc_type": doc_type,
                    "url": url,
                    "message": f"URL格式不正确: {url}"
                })
                
            # 检查链接文本是否为默认的URL
            if url in display_text and len(display_text.strip()) > 10:
                issues.append({
                    "type": "raw_url_as_text",
                    "doc_type": doc_type,
                    "url": url,
                    "message": "链接文本使用了原始URL，建议使用更有描述性的文本"
                })
        
        # 检查本地文件链接
        file_pattern = r'\[([^\]]+)\]\(([^http][^)]+\.(md|txt|pdf|docx))\)'
        file_matches = re.findall(file_pattern, content)
        
        for display_text, file_path, ext in file_matches:
            # 检查文件路径格式
            if not self._is_valid_file_path(file_path):
                issues.append({
                    "type": "invalid_file_path",
                    "doc_type": doc_type,
                    "file_path": file_path,
                    "message": f"文件路径格式不正确: {file_path}"
                })
        
        return issues
    
    def _is_valid_url(self, url: str) -> bool:
        """
        简单验证URL格式
        :param url: URL地址
        :return: 是否为有效格式
        """
        url_pattern = r'^https?://[\w\-\.]+(:\d+)?(/[\w\-\./%~&=+?]*)?$'
        return bool(re.match(url_pattern, url))
    
    def _is_valid_file_path(self, file_path: str) -> bool:
        """
        简单验证文件路径格式
        :param file_path: 文件路径
        :return: 是否为有效格式
        """
        # 简单检查，排除明显不合法的路径
        invalid_chars = ['<', '>', '|', '*', '?', '"', ';']
        return not any(char in file_path for char in invalid_chars)
    
    def _check_figure_references(self, content: str, doc_type: str) -> List[Dict]:
        """
        检查文档中图表引用的完整性
        :param content: 文档内容
        :param doc_type: 文档类型
        :return: 问题列表
        """
        issues = []
        
        # 提取所有图片定义
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        images = re.findall(image_pattern, content)
        image_ids = {}
        
        for i, (alt_text, src) in enumerate(images):
            image_id = f"图 {i+1}"
            # 尝试从alt文本中提取图表编号
            if alt_text and re.match(r'^(图|表|Figure|Table)\s*\d+', alt_text, re.IGNORECASE):
                image_id = alt_text
            image_ids[src] = image_id
        
        # 提取所有图表引用
        reference_pattern = r'(图|表|Figure|Table)\s+\d+\b'
        references = re.findall(reference_pattern, content)
        
        # 检查引用是否有对应的图表定义
        for reference in references:
            # 跳过图表定义本身
            skip = False
            for alt_text, _ in images:
                if reference in alt_text:
                    skip = True
                    break
            
            if skip:
                continue
                
            # 检查引用是否有对应的图表
            if not any(reference in img_id for img_id in image_ids.values()):
                issues.append({
                    "type": "invalid_figure_reference",
                    "doc_type": doc_type,
                    "reference": reference,
                    "message": f"引用了不存在的图表: {reference}"
                })
        
        # 检查图片路径格式
        for alt_text, src in images:
            if not src.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                issues.append({
                    "type": "invalid_image_format",
                    "doc_type": doc_type,
                    "src": src,
                    "message": f"图片格式不受支持: {src}"
                })
        
        return issues
    
    def validate_document_format(self, content: str) -> List[Dict]:
        """
        验证文档格式是否符合规范
        :param content: 文档内容
        :return: 问题列表
        """
        issues = []
        
        # 检查标题层级
        current_level = 0
        for line in content.split('\n'):
            if line.strip().startswith('#'):
                # 计算#的数量
                level = len(line) - len(line.lstrip('#'))
                
                # 标题层级不应该跳跃，例如从# 直接到###
                if level > current_level + 1 and current_level > 0:
                    issues.append({
                        "type": "heading_level_jump",
                        "line": line.strip(),
                        "message": f"标题层级跳跃: 从{current_level}级到{level}级"
                    })
                
                current_level = level
        
        # 检查表格格式
        table_header_pattern = r'\|[^|]+\|[^|]+\|'
        table_separator_pattern = r'\|[\s\-:]+\|[\s\-:]+\|'
        
        for i, line in enumerate(content.split('\n')):
            if re.match(table_header_pattern, line):
                # 检查下一行是否为分隔符
                if i + 1 < len(content.split('\n')):
                    next_line = content.split('\n')[i + 1]
                    if not re.match(table_separator_pattern, next_line):
                        issues.append({
                            "type": "table_format_error",
                            "line": line,
                            "message": "表格头部后缺少分隔行"
                        })
        
        # 检查列表格式
        list_format_issues = self._check_list_format(content)
        issues.extend(list_format_issues)
        
        # 检查代码块格式
        code_block_issues = self._check_code_blocks(content)
        issues.extend(code_block_issues)
        
        return issues
    
    def _check_list_format(self, content: str) -> List[Dict]:
        """
        检查列表格式
        :param content: 文档内容
        :return: 问题列表
        """
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # 检查无序列表格式
            if re.match(r'^\s*[-*+]\s', line):
                # 列表项之间不应该有空行
                if i > 0 and i < len(lines) - 1:
                    prev_line = lines[i-1].strip()
                    next_line = lines[i+1].strip()
                    
                    # 列表开始前应有空行
                    if i > 1 and not prev_line and re.match(r'^\s*[^-*+\s]', lines[i-2]):
                        issues.append({
                            "type": "list_format_error",
                            "line": line,
                            "message": "列表开始前应有空行"
                        })
                    
                    # 列表中间不应该有空行
                    if next_line and re.match(r'^\s*[-*+]\s', next_line) and not prev_line:
                        issues.append({
                            "type": "list_format_error",
                            "line": line,
                            "message": "列表项之间不应有空行"
                        })
        
        return issues
    
    def _check_code_blocks(self, content: str) -> List[Dict]:
        """
        检查代码块格式
        :param content: 文档内容
        :return: 问题列表
        """
        issues = []
        
        # 检查代码块格式
        code_block_pattern = r'```([a-zA-Z0-9]*)\n(.*?)\n```'
        code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
        
        for language, code in code_blocks:
            # 代码块应该指定语言
            if not language and len(code.strip()) > 0:
                issues.append({
                    "type": "code_block_no_language",
                    "code": code[:30] + "..." if len(code) > 30 else code,
                    "message": "代码块未指定编程语言"
                })
        
        return issues

    def check_all_documents(self, documents: Dict[str, str]) -> Dict[str, List[Dict]]:
        """
        全面检查所有文档的格式和一致性
        :param documents: 文档内容字典 {doc_type: content}
        :return: 按文档类型分类的问题列表 {doc_type: [问题列表]}
        """
        results = {}
        
        # 检查每个文档的格式
        for doc_type, content in documents.items():
            format_issues = self.validate_document_format(content)
            if format_issues:
                if doc_type not in results:
                    results[doc_type] = []
                results[doc_type].extend(format_issues)
        
        # 检查文档间的一致性
        consistency_issues = self.check_consistency(documents)
        
        # 将一致性问题按文档类型分类
        for issue in consistency_issues:
            doc_type = issue.get('source_doc', issue.get('doc_type', 'general'))
            if doc_type not in results:
                results[doc_type] = []
            results[doc_type].append(issue)
        
        return results 