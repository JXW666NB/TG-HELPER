import os
import yaml
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class SkillMetadata:
    """Skill元数据（从YAML frontmatter解析）"""
    def __init__(self, name: str, description: str, **kwargs):
        self.name = name
        self.description = description
        self.allowed_tools = kwargs.get('allowed-tools', [])
        self.version = kwargs.get('version', '1.0.0')
        self.author = kwargs.get('author', '')
        self.license = kwargs.get('license', '')
        self.compatibility = kwargs.get('compatibility', '')
        self.metadata = kwargs.get('metadata', {})
        self.skill_path = kwargs.get('skill_path', '')

class Skill:
    """单个Skill，包含元数据和内容"""
    def __init__(self, path: str):
        self.path = path
        self.metadata = None
        self.full_content = None
        self.load_metadata()

    def load_metadata(self):
        """加载元数据（第一层）"""
        skill_file = os.path.join(self.path, 'SKILL.md')
        if not os.path.exists(skill_file):
            raise FileNotFoundError(f"SKILL.md not found in {self.path}")
        
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                self.full_content = parts[2].strip()
                try:
                    data = yaml.safe_load(yaml_content)
                    if data:
                        data['skill_path'] = self.path
                        self.metadata = SkillMetadata(**data)
                except Exception as e:
                    print(f"解析Skill {self.path} 失败: {e}")
        
        if not self.metadata:
            # 如果没有frontmatter，使用默认值
            self.metadata = SkillMetadata(
                name=os.path.basename(self.path),
                description="No description",
                skill_path=self.path
            )
            self.full_content = content

    def load_full_content(self):
        """加载完整SKILL.md内容（第二层）"""
        if self.full_content is None:
            skill_file = os.path.join(self.path, 'SKILL.md')
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    self.full_content = parts[2].strip()
                else:
                    self.full_content = content
            else:
                self.full_content = content
        return self.full_content

    def get_script_path(self, script_name: str) -> Optional[str]:
        """获取脚本路径（第三层）"""
        script_path = os.path.join(self.path, 'scripts', script_name)
        if os.path.exists(script_path):
            return script_path
        return None

    def execute_script(self, script_name: str, args: List[str] = None, timeout: int = 30):
        """执行Skill中的脚本"""
        script_path = self.get_script_path(script_name)
        if not script_path:
            return f"错误: 脚本 {script_name} 不存在"
        
        ext = os.path.splitext(script_path)[1].lower()
        cmd = []
        if ext == '.py':
            cmd = ['python', script_path]
        elif ext == '.sh':
            cmd = ['bash', script_path]
        elif ext == '.js':
            cmd = ['node', script_path]
        else:
            return f"错误: 不支持的脚本类型 {ext}"
        
        if args:
            cmd.extend(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            output = result.stdout + result.stderr
            return f"脚本执行成功:\n{output[:2000]}" + ("..." if len(output) > 2000 else "")
        except subprocess.TimeoutExpired:
            return "错误: 脚本执行超时"
        except Exception as e:
            return f"错误: 脚本执行失败: {str(e)}"

class SkillManager:
    """Skill管理器，负责发现和加载Skills"""
    def __init__(self, skills_dirs: List[str] = None):
        self.skills_dirs = skills_dirs or ["./skills", os.path.expanduser("~/.tghelper/skills")]
        self.skills: Dict[str, Skill] = {}
        self.cache = {}  # 缓存已加载的完整内容
        self.discover()

    def discover(self):
        """发现所有可用的Skill（加载元数据）"""
        self.skills.clear()
        for skills_dir in self.skills_dirs:
            if not os.path.exists(skills_dir):
                continue
            for item in os.listdir(skills_dir):
                skill_path = os.path.join(skills_dir, item)
                if os.path.isdir(skill_path):
                    try:
                        skill = Skill(skill_path)
                        self.skills[skill.metadata.name] = skill
                    except Exception as e:
                        print(f"加载Skill {skill_path} 失败: {e}")
        return self.skills

    def get_skill_metadata(self) -> List[Dict]:
        """获取所有Skill的元数据（用于渐进式披露）"""
        return [
            {
                "name": skill.metadata.name,
                "description": skill.metadata.description,
                "version": skill.metadata.version,
                "allowed_tools": skill.metadata.allowed_tools
            }
            for skill in self.skills.values()
        ]

    def get_skill(self, name: str) -> Optional[Skill]:
        """获取Skill对象（如果未加载完整内容，仍只含元数据）"""
        return self.skills.get(name)

    def load_skill_content(self, name: str) -> Optional[str]:
        """按需加载Skill的完整内容"""
        skill = self.get_skill(name)
        if not skill:
            return None
        if name not in self.cache:
            self.cache[name] = skill.load_full_content()
        return self.cache[name]

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()