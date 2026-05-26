# -*- coding: utf-8 -*-
"""
AI 辅助转换器
"""
import os
import re
import json
import ast
from typing import Optional, Dict, Any, Callable


class AIConverter:
    """使用 AI 将外部插件转换为 TG HELPER 原生插件"""
    
    def __init__(self, llm_call: Callable[[str], str]):
        """
        llm_call: 调用 AI 的函数，接收 prompt 字符串，返回响应字符串
        """
        self.llm_call = llm_call
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    
    def convert_openclaw(self, adapter) -> Optional[str]:
        """
        转换 OpenClaw 插件，返回生成的 Python 代码
        """
        prompt = adapter.get_conversion_prompt()
        source_context = adapter.get_source_code()
        full_prompt = f"{prompt}\n\n【参考源代码片段】\n{source_context[:3000]}"
        
        response = self.llm_call(full_prompt)
        code = self._extract_python_code(response)
        
        if code and self._validate_code(code):
            return code
        return None
    
    def convert_xiaoli(self, adapter) -> Optional[str]:
        """
        转换小狸插件，返回生成的 Python 代码
        """
        prompt = adapter.get_conversion_prompt()
        response = self.llm_call(prompt)
        code = self._extract_python_code(response)
        
        if code and self._validate_code(code):
            return code
        return None
    
    def _extract_python_code(self, text: str) -> Optional[str]:
        # 提取 ```python ... ``` 代码块
        match = re.search(r'```python\s*([\s\S]*?)\s*```', text)
        if match:
            return match.group(1).strip()
        # 尝试提取任意代码块
        match = re.search(r'```\s*([\s\S]*?)\s*```', text)
        if match:
            return match.group(1).strip()
        # 如果没有代码块，返回原始文本（可能直接是代码）
        if 'import' in text and 'class' in text:
            return text.strip()
        return None
    
    def _validate_code(self, code: str) -> bool:
        """AST 安全检查（允许正常模块导入，仅禁止危险调用）"""
        try:
            tree = ast.parse(code)
            # 禁止危险函数调用（eval/exec/compile/__import__）
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ('eval', 'exec', 'compile', '__import__'):
                        return False
                    # 禁止 os.system / subprocess.call 等
                    if isinstance(func, ast.Attribute):
                        if func.attr in ('system', 'popen', 'spawn', 'call', 'run', 'Popen'):
                            return False
            return True
        except SyntaxError:
            return False