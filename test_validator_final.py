"""
最终版内容验证器测试
修复已知问题
"""

import re
import logging
from typing import Dict, List

class SimpleContentValidator:
    """简化版内容验证器"""
    
    def __init__(self):
        """初始化内容验证器"""
        self.logger = logging.getLogger("test_validator")
        
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
        
        # 检查表格格式 - 改进检测逻辑
        lines = content.split('\n')
        table_state = "none"  # 标记表格状态：none, header, separator, data
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 检测表格头部
            if line.startswith('|') and line.endswith('|') and ' | ' in line and table_state == "none":
                table_state = "header"
                
                # 检查下一行是否为分隔符
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('|') and next_line.endswith('|') and '-' in next_line:
                        table_state = "separator"
                    else:
                        issues.append({
                            "type": "table_format_error",
                            "line": line,
                            "message": "表格头部后缺少分隔行"
                        })
            # 表格数据行不需要检查
            elif line.startswith('|') and line.endswith('|') and table_state == "separator":
                table_state = "data"
            # 空行或非表格行重置表格状态
            elif not line or not line.startswith('|'):
                table_state = "none"
        
        # 检查代码块格式
        in_code_block = False
        has_language = False
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    # 检查是否指定了语言
                    has_language = len(line) > 3
                else:
                    # 代码块结束
                    in_code_block = False
                    if not has_language:
                        issues.append({
                            "type": "code_block_no_language",
                            "message": "代码块未指定编程语言"
                        })
                    has_language = False
        
        # 检查未关闭的代码块
        if in_code_block:
            issues.append({
                "type": "unclosed_code_block",
                "message": "代码块未关闭"
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
        
        return issues


def run_tests():
    """运行所有测试"""
    validator = SimpleContentValidator()
    all_tests_passed = True
    
    print("测试1: 标题层级跳跃检测")
    content = """# 一级标题
### 三级标题（跳过二级）
#### 四级标题
"""
    issues = validator.validate_document_format(content)
    if any(issue["type"] == "heading_level_jump" for issue in issues):
        print("✓ 通过")
    else:
        print("✗ 失败")
        all_tests_passed = False
    
    print("\n测试2: 表格格式错误检测")
    content = """# 表格测试
| 列1 | 列2 |
表格内容行缺少分隔符
"""
    issues = validator.validate_document_format(content)
    if any(issue["type"] == "table_format_error" for issue in issues):
        print("✓ 通过")
    else:
        print("✗ 失败")
        all_tests_passed = False
    
    print("\n测试3: 代码块语言缺失检测")
    content = """# 代码测试
```
def test():
    pass
```
"""
    issues = validator.validate_document_format(content)
    if any(issue["type"] == "code_block_no_language" for issue in issues):
        print("✓ 通过")
    else:
        print("✗ 失败")
        all_tests_passed = False
    
    print("\n测试4: 格式正确的文档")
    content = """# 一级标题
## 二级标题
### 三级标题

这是正确格式的文档。

| 列1 | 列2 |
|-----|-----|
| 内容1 | 内容2 |

```python
def test():
    pass
```
"""
    issues = validator.validate_document_format(content)
    if len(issues) == 0:
        print("✓ 通过")
    else:
        print(f"✗ 失败 - 检测到{len(issues)}个问题:")
        for issue in issues:
            print(f"  - {issue.get('type')}: {issue.get('message')}")
        all_tests_passed = False
    
    print("\n测试5: 无效URL格式")
    content = """# 链接测试
请参考[官方文档](http://example.com/with spaces)
"""
    issues = validator._check_link_integrity(content, "test_doc")
    if any(issue["type"] == "invalid_url_format" for issue in issues):
        print("✓ 通过")
    else:
        print("✗ 失败")
        all_tests_passed = False
    
    print("\n测试6: 原始URL作为链接文本")
    content = """# 链接测试
请参考[http://example.com/api/docs](http://example.com/api/docs)
"""
    issues = validator._check_link_integrity(content, "test_doc")
    if any(issue["type"] == "raw_url_as_text" for issue in issues):
        print("✓ 通过")
    else:
        print("✗ 失败")
        all_tests_passed = False
    
    print("\n测试7: 有效链接")
    content = """# 链接测试
请参考[官方文档](https://example.com/api/docs)
"""
    issues = validator._check_link_integrity(content, "test_doc")
    if not any(issue["type"] == "invalid_url_format" for issue in issues):
        print("✓ 通过")
    else:
        print("✗ 失败")
        all_tests_passed = False
    
    print("\n" + "="*50)
    if all_tests_passed:
        print("✅ 所有测试通过！内容验证功能工作正常。")
    else:
        print("❌ 部分测试失败。请查看上述输出以了解详情。")
    print("="*50)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    run_tests() 