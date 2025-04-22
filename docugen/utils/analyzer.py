"""
文档分析模块

此模块提供用于分析Markdown文档的工具，包括：
- 提取文档标题和结构
- 提取关键概念
- 分析链接、图片和表格
- 生成目录和索引
- 增强文档结构

主要用于支持文档生成过程中的结构分析和增强功能。
"""

import re
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple

# 配置日志
logger = logging.getLogger(__name__)

class DocumentAnalyzer:
    """文档分析器类
    
    用于分析Markdown文档结构并提供增强功能，如自动生成目录和索引。
    """
    
    def __init__(self):
        """初始化DocumentAnalyzer类"""
        # 标题匹配模式 (# 标题)
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+?)(?:\s+\{#([a-zA-Z0-9_-]+)\})?\s*$', re.MULTILINE)
        
        # 强调文本匹配模式 (*斜体* 和 **粗体**)
        self.emphasis_pattern = re.compile(r'(\*\*|__)(.*?)\1|(\*|_)(.*?)\3')
        
        # 链接匹配模式 [链接文本](URL)
        self.link_pattern = re.compile(r'\[(.*?)\]\((.*?)\)')
        
        # 图片匹配模式 ![替代文本](URL)
        self.image_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
        
        # 表格头部匹配模式
        self.table_header_pattern = re.compile(r'\n\|(.+)\|\n\|(?:[-:]+\|)+\n')
        
        # 代码块匹配模式 ```语言 代码 ```
        self.code_block_pattern = re.compile(r'```([a-zA-Z0-9]*)\n(.*?)\n```', re.DOTALL)
        
        # 元数据块匹配模式 (YAML front matter)
        self.metadata_block_pattern = re.compile(r'---\n(.*?)\n---', re.DOTALL)
        
        # 元数据项匹配模式
        self.metadata_item_pattern = re.compile(r'([a-zA-Z0-9_-]+):\s*(.*)')
    
    def analyze_document(self, content: str) -> Dict[str, Any]:
        """分析文档内容，提取各种元素
        
        Args:
            content: 文档内容字符串
            
        Returns:
            包含分析结果的字典，包括标题、标题结构、关键概念、链接、图片等
        """
        title = self._extract_title(content)
        headings = self._extract_headings(content)
        key_concepts = self._extract_key_concepts(content)
        links = self._extract_links(content)
        images = self._extract_images(content)
        tables = self._extract_tables(content)
        code_blocks = self._extract_code_blocks(content)
        metadata = self._extract_metadata(content)
        word_count = self._count_words(content)
        
        # 计算文档结构的统计数据
        stats = {
            "word_count": word_count,
            "heading_count": len(headings),
            "link_count": len(links),
            "image_count": len(images),
            "table_count": len(tables),
            "code_block_count": len(code_blocks),
            "has_metadata": bool(metadata)
        }
        
        # 返回分析结果
        return {
            "title": title,
            "headings": headings,
            "key_concepts": key_concepts,
            "links": links,
            "images": images,
            "tables": tables,
            "code_blocks": code_blocks,
            "metadata": metadata,
            "stats": stats
        }
    
    def _extract_title(self, content: str) -> str:
        """提取文档标题
        
        Args:
            content: 文档内容
            
        Returns:
            文档的标题（第一个一级标题）
        """
        # 查找第一个一级标题
        match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # 如果没有一级标题，尝试从元数据中获取标题
        metadata = self._extract_metadata(content)
        if "title" in metadata:
            return metadata["title"]
        
        return "无标题文档"
    
    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """提取文档中的所有标题
        
        Args:
            content: 文档内容
            
        Returns:
            包含标题信息的字典列表
        """
        headings = []
        
        # 查找所有标题
        for match in self.heading_pattern.finditer(content):
            level = len(match.group(1))  # '#' 的数量决定标题级别
            text = match.group(2)
            custom_id = match.group(3)
            
            # 生成标题ID，如果没有自定义ID
            heading_id = custom_id if custom_id else self._generate_heading_id(text)
            
            headings.append({
                "level": level,
                "text": text,
                "id": heading_id,
                "position": match.start()
            })
        
        return headings
    
    def _extract_key_concepts(self, content: str) -> Dict[str, int]:
        """提取文档中的关键概念
        
        这里使用一个简单的方法：计算名词短语的出现频率
        更复杂的实现可能需要NLP库进行主题分析
        
        Args:
            content: 文档内容
            
        Returns:
            关键概念及其出现次数的字典
        """
        # 移除代码块和表格，以免干扰分析
        cleaned_content = self.code_block_pattern.sub('', content)
        cleaned_content = self.table_header_pattern.sub('', cleaned_content)
        
        # 简单实现：查找所有大写字母开头的词组
        # 更好的实现应使用NLP分析
        concept_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Za-z]+){0,3})\b')
        concepts = {}
        
        for match in concept_pattern.finditer(cleaned_content):
            concept = match.group(1)
            concepts[concept] = concepts.get(concept, 0) + 1
        
        # 过滤掉低频概念
        return {k: v for k, v in concepts.items() if v > 1}
    
    def _extract_links(self, content: str) -> List[Dict[str, Any]]:
        """提取文档中的所有链接
        
        Args:
            content: 文档内容
            
        Returns:
            链接信息的字典列表
        """
        links = []
        
        # 查找所有链接
        for match in self.link_pattern.finditer(content):
            text = match.group(1)
            url = match.group(2)
            
            # 判断链接类型
            link_type = "external"
            if url.startswith('#'):
                link_type = "anchor"
            elif not (url.startswith('http://') or url.startswith('https://')):
                link_type = "internal"
            
            links.append({
                "text": text,
                "url": url,
                "type": link_type,
                "position": match.start()
            })
        
        return links
    
    def _extract_images(self, content: str) -> List[Dict[str, Any]]:
        """提取文档中的所有图片
        
        Args:
            content: 文档内容
            
        Returns:
            图片信息的字典列表
        """
        images = []
        
        # 查找所有图片
        for match in self.image_pattern.finditer(content):
            alt_text = match.group(1)
            url = match.group(2)
            
            # 获取图片类型（通过URL后缀）
            image_type = "unknown"
            if '.' in url:
                ext = url.split('.')[-1].lower()
                if ext in ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp']:
                    image_type = ext
            
            images.append({
                "alt_text": alt_text,
                "url": url,
                "type": image_type,
                "position": match.start()
            })
        
        return images
    
    def _extract_tables(self, content: str) -> List[Dict[str, Any]]:
        """提取文档中的所有表格
        
        Args:
            content: 文档内容
            
        Returns:
            表格信息的字典列表
        """
        tables = []
        
        # 查找所有表格
        for match in self.table_header_pattern.finditer(content):
            header_text = match.group(1)
            table_start = match.start()
            
            # 分析表格头部
            headers = [h.strip() for h in header_text.split('|') if h.strip()]
            
            # 找到表格的结束位置（下一个空行）
            table_content = content[table_start:]
            end_pos = table_content.find('\n\n')
            if end_pos == -1:
                table_content = table_content
            else:
                table_content = table_content[:end_pos]
            
            # 计算行数（减去表头和分隔行）
            rows = len(table_content.split('\n')) - 2
            
            tables.append({
                "headers": headers,
                "column_count": len(headers),
                "row_count": rows,
                "position": table_start
            })
        
        return tables
    
    def _extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """提取文档中的所有代码块
        
        Args:
            content: 文档内容
            
        Returns:
            代码块信息的字典列表
        """
        code_blocks = []
        
        # 查找所有代码块
        for match in self.code_block_pattern.finditer(content):
            language = match.group(1) or "plain"
            code = match.group(2)
            
            code_blocks.append({
                "language": language,
                "code": code,
                "position": match.start()
            })
        
        return code_blocks
    
    def _count_words(self, content: str) -> int:
        """计算文档中的单词数量
        
        Args:
            content: 文档内容
            
        Returns:
            文档中的单词数量
        """
        # 移除代码块、表格和元数据以便更准确地计算单词
        cleaned_content = self.code_block_pattern.sub('', content)
        cleaned_content = self.table_header_pattern.sub('', cleaned_content)
        cleaned_content = self.metadata_block_pattern.sub('', cleaned_content)
        
        # 删除Markdown语法，如链接和图片
        cleaned_content = self.link_pattern.sub(r'\1', cleaned_content)
        cleaned_content = self.image_pattern.sub('', cleaned_content)
        
        # 分割成单词并计数
        words = re.findall(r'\b\w+\b', cleaned_content)
        return len(words)
    
    def _extract_metadata(self, content: str) -> Dict[str, str]:
        """提取文档中的YAML元数据块
        
        Args:
            content: 文档内容
            
        Returns:
            元数据键值对字典
        """
        metadata = {}
        
        # 查找元数据块
        match = self.metadata_block_pattern.search(content)
        if match:
            metadata_text = match.group(1)
            
            # 提取元数据项
            for item_match in self.metadata_item_pattern.finditer(metadata_text):
                key = item_match.group(1).strip()
                value = item_match.group(2).strip()
                metadata[key] = value
        
        return metadata
    
    def _generate_heading_id(self, heading_text: str) -> str:
        """为标题生成ID
        
        Args:
            heading_text: 标题文本
            
        Returns:
            基于标题文本生成的ID
        """
        # 移除特殊字符，替换空格为连字符
        sanitized = re.sub(r'[^\w\s-]', '', heading_text.lower())
        sanitized = re.sub(r'\s+', '-', sanitized)
        
        # 对于完全由非拉丁字符组成的标题，生成一个哈希ID
        if not sanitized:
            sanitized = 'heading-' + hashlib.md5(heading_text.encode('utf-8')).hexdigest()[:8]
        
        return sanitized
    
    def generate_toc(self, headings: List[Dict[str, Any]], exclude_title: bool = True) -> str:
        """生成文档的目录
        
        Args:
            headings: 标题信息列表
            exclude_title: 是否排除主标题（一级标题）
            
        Returns:
            格式化的目录Markdown文本
        """
        toc_lines = []
        
        # 可选排除第一个一级标题
        start_index = 1 if exclude_title and headings and headings[0]['level'] == 1 else 0
        
        for heading in headings[start_index:]:
            # 根据标题级别缩进
            indent = '  ' * (heading['level'] - 1)
            # 创建目录项
            toc_line = f"{indent}- [{heading['text']}](#{heading['id']})"
            toc_lines.append(toc_line)
        
        return '\n'.join(toc_lines)
    
    def generate_index(self, key_concepts: Dict[str, int], content: str) -> str:
        """生成文档的关键概念索引
        
        Args:
            key_concepts: 关键概念及其出现次数的字典
            content: 原始文档内容，用于查找概念所在位置
            
        Returns:
            格式化的索引Markdown文本
        """
        if not key_concepts:
            return "没有检测到关键概念"
        
        # 提取标题以关联概念和标题
        headings = self._extract_headings(content)
        
        index_items = []
        
        # 按字母顺序排序关键概念
        sorted_concepts = sorted(key_concepts.items())
        
        for concept, count in sorted_concepts:
            # 查找概念在哪些标题下出现
            concept_positions = []
            for match in re.finditer(r'\b' + re.escape(concept) + r'\b', content):
                concept_positions.append(match.start())
            
            # 查找每个出现位置对应的标题
            related_headings = []
            for pos in concept_positions:
                # 找到最接近且在概念前面的标题
                closest_heading = None
                min_distance = float('inf')
                
                for heading in headings:
                    if heading['position'] < pos and (pos - heading['position']) < min_distance:
                        min_distance = pos - heading['position']
                        closest_heading = heading
                
                if closest_heading and closest_heading not in related_headings:
                    related_headings.append(closest_heading)
            
            # 构建索引项
            references = []
            for heading in related_headings:
                references.append(f"[{heading['text']}](#{heading['id']})")
            
            # 格式化索引项
            refs_text = ", ".join(references) if references else "整篇文档"
            index_items.append(f"**{concept}** ({count}次): {refs_text}")
        
        return '\n'.join(index_items)
    
    def add_toc_to_document(self, content: str) -> str:
        """向文档添加目录
        
        Args:
            content: 原始文档内容
            
        Returns:
            添加了目录的文档内容
        """
        # 提取标题
        headings = self._extract_headings(content)
        
        # 生成目录
        toc = self.generate_toc(headings)
        
        # 找到合适的位置插入目录
        # 如果有一级标题，在第一个一级标题后插入
        if headings and headings[0]['level'] == 1:
            title_end = headings[0]['position'] + len('\n')
            # 找到标题后的第一个换行符
            while title_end < len(content) and content[title_end] != '\n':
                title_end += 1
            
            # 在标题后插入目录
            return (
                content[:title_end + 1] +
                "\n## 目录\n\n" +
                toc +
                "\n\n" +
                content[title_end + 1:]
            )
        else:
            # 如果没有一级标题，在文档开头插入目录
            return "## 目录\n\n" + toc + "\n\n" + content
    
    def add_index_to_document(self, content: str) -> str:
        """向文档添加索引
        
        Args:
            content: 原始文档内容
            
        Returns:
            添加了索引的文档内容
        """
        # 提取关键概念
        key_concepts = self._extract_key_concepts(content)
        
        # 生成索引
        index = self.generate_index(key_concepts, content)
        
        # 在文档末尾添加索引
        return content + "\n\n## 索引\n\n" + index
    
    def enhance_document(self, content: str) -> str:
        """增强文档，添加目录和索引
        
        Args:
            content: 原始文档内容
            
        Returns:
            增强后的文档内容
        """
        # 先添加目录
        enhanced = self.add_toc_to_document(content)
        
        # 再添加索引
        enhanced = self.add_index_to_document(enhanced)
        
        return enhanced


# 创建实例方便导入
document_analyzer = DocumentAnalyzer() 