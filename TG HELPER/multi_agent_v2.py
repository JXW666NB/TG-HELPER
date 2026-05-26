# multi_agent_v2.py —— 多Agent协作调度器（重构修复版）

import json
import re
import traceback
import threading
from typing import List, Dict, Optional, Callable

from agent import AIAgent
from memory import Memory
from tools import Tools
from config import config


class TaskItem:
    def __init__(self, index: int, description: str):
        self.index = index
        self.description = description
        self.status = "pending"      # pending | running | completed
        self.result = ""


class ReadOnlyTools:
    """仅暴露只读工具给 Planner"""
    def __init__(self, base_tools: Tools):
        self._base = base_tools
        self._allowed = {"read_file", "list_directory", "search_files", "get_file_info"}

    def __getattr__(self, name):
        if name in self._allowed:
            return getattr(self._base, name)
        raise AttributeError(f"Planner 不允许使用工具 '{name}'，只能查看文件。")


class MultiAgentOrchestrator:
    def __init__(self, gui):
        self.gui = gui
        self.task_list: List[TaskItem] = []
        self.current_agent = None          # "planner", "worker", "reviewer"
        self.is_running = False
        self.stop_event = threading.Event()
        self.agents: Dict[str, AIAgent] = {}
        self.memories: Dict[str, Memory] = {}
        self.personalities: Dict[str, str] = {}
        self.original_request = ""

        # GUI 回调
        self.on_task_list_updated: Callable = None
        self.on_agent_message: Callable = None
        self.on_finished: Callable = None

    # ==================== 配置 ====================
    def configure(self, enable: bool, planner_persona: str, worker_persona: str, reviewer_persona: str):
        if not enable:
            return
        if len({planner_persona, worker_persona, reviewer_persona}) < 3:
            raise ValueError("三个 Agent 人格不能相同，以免记忆错乱")

        self.personalities = {
            "planner": planner_persona,
            "worker": worker_persona,
            "reviewer": reviewer_persona,
        }

        for role in self.personalities:
            persona = self.personalities[role]
            memory = Memory(mind_dir=config.memory_dir, persona_name=persona)
            self.memories[role] = memory

            # 创建完整工具集
            full_tools = Tools(
                memory,
                confirm_callback=self.gui.request_confirmation,
                output_callback=lambda msg: None
            )

            if role == "planner":
                # Planner 仅拥有只读工具 + 自定义系统提示
                tools = ReadOnlyTools(full_tools)
                agent = AIAgent(config, memory, tools)
                agent.set_personality(persona, self._load_persona_prompt(persona))
                agent.custom_system_prompt = self._build_planner_system_prompt(persona)
            else:
                # Worker / Reviewer 保持默认行为（但会使用各自人格记忆）
                tools = full_tools
                agent = AIAgent(config, memory, tools)
                agent.set_personality(persona, self._load_persona_prompt(persona))
            self.agents[role] = agent

    def _load_persona_prompt(self, name: str) -> str:
        import os
        path = os.path.join(getattr(config, 'personality_dir', './AI人格'), name, '人格提示词.txt')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return ""

    def _build_planner_system_prompt(self, persona_prompt: str) -> str:
        return f"""{persona_prompt}

【你的角色】你是任务规划专家（Planner）。你不能直接执行任务，只能分析和制定计划。
【可用工具】你只能使用以下只读工具：
- read_file(filepath, max_chars=800000) : 读取文件内容
- list_directory(path) : 列出目录内容
- search_files(directory, pattern) : 搜索文件
- get_file_info(path) : 获取文件/文件夹详细信息

【工作流程】
1. 首先了解所有可用的工具分类。
所有可用工具都分类存放在 ./tool_prompts/ 文件夹中：
【可用的工具分类文件】（路径均为 ./tool_prompts/）：
- 文件操作（删除、移动、复制、创建目录、获取信息、列出目录）.txt
- 文件读写（读取、分块读取、写入、搜索文件）.txt
- 系统命令与信息（执行命令、系统信息、py库安装）.txt
- 网络与下载还有浏览器自动化网页操作（下载视频、批量下载、网页提取、搜索、打开浏览器，导航、截图、获取文本、点击、填写、执行js脚本、关闭）.txt
- 键盘鼠标模拟（点击、输入、移动）.txt
- 办公文档处理（Excel、PDF、邮件，生成 Word 文档）.txt
- 多媒体编辑（图片、音频、视频）.txt
- 开发辅助（执行py代码、Git操作）.txt
- 硬件通信（串口、延时）.txt
- 记忆管理（添加长期记忆）.txt
- QQ交互（发送文件、撤回消息、加好友、加群，发送QQ语音，语音合成，向指定QQ或QQ群发送消息和表情包，从网络下载音乐并以语音形式发送到QQ）.txt
- 技能系统（执行技能）.txt
- 定时任务（添加、列表、删除）.txt
- 嵌入式开发仅限ARDUINO（安装CLI、核心、生成代码、编译、上传、检测、保存桌面、安装库）.txt
- 图像视频分析（分析图片、分析视频、QQ视频接收）.txt
- 屏幕截图（截图）.txt
- 物联网智能家居设备控制（查询设备，发送控制设备指令）.txt

在这些文件夹中包含了全部可用工具的详细介绍

2. 然后根据用户需求制定任务计划。
3. **最终输出**必须是一个 JSON 对象，格式如下：
   {{
     "finish": true,
     "message": ["任务一", "任务二", "任务三"]
   }}
   message 是一个 JSON 数组，每个元素是一条简短的任务描述。"""

    # ==================== 公共接口 ====================
    def start(self, user_input: str):
        if self.is_running:
            return
        self.is_running = True
        self.stop_event.clear()
        self.original_request = user_input
        threading.Thread(target=self._run_workflow, daemon=True).start()

    def stop(self):
        self.stop_event.set()
        self.is_running = False

    # ==================== 内部辅助 ====================
    def _say(self, role: str, msg: str):
        persona = self.personalities.get(role, "系统")
        if role in self.memories:
            self.memories[role].add_short_term(f"{persona}({role})", msg)
        if self.on_agent_message:
            self.on_agent_message(persona, msg, role)

    def _update_ui(self):
        if self.on_task_list_updated:
            self.on_task_list_updated()

    def _call_agent(self, role: str, user_prompt: str) -> str:
        agent = self.agents[role]
        memory = self.memories[role]
        persona = self.personalities[role]

        # 收集 AI 输出
        result = [""]
        orig_out = agent.output_callback

        def capture(msg):
            result[0] = msg
            self._say(role, msg)
        agent.output_callback = capture
        agent.stop_event = self.stop_event

        # 临时替换记忆记录的角色名，避免出现重复的“用户”
        orig_add = memory.add_short_term
        def new_add(role_str, content):
            if role_str == "用户":
                # 用 人格(角色) 代替“用户”
                orig_add(f"{persona}({role})", content)
            else:
                orig_add(role_str, content)
        memory.add_short_term = new_add

        try:
            agent.run(user_prompt)          # agent.run 内部会调用 memory.add_short_term("用户", user_prompt)
        finally:
            agent.output_callback = orig_out
            memory.add_short_term = orig_add
        return result[0]

    # ==================== 工作流 ====================
    def _run_workflow(self):
        try:
            # 阶段1: Planner
            tasks_ok = self._phase_planner()
            if not tasks_ok:
                self._say("planner", "抱歉，我没能分析出可行的任务步骤。")
                return

            # 阶段2: Worker 逐条执行
            self.current_agent = "worker"
            self._update_ui()
            for task in self.task_list:
                if self.stop_event.is_set():
                    return
                task.status = "running"
                self._update_ui()
                self._say("worker", f"🔄 开始执行任务 {task.index}：{task.description}")
                result = self._execute_task(task)
                if self.stop_event.is_set():
                    return
                if self._is_replan_request(result):
                    self._say("worker", f"@Planner 任务 {task.index} 遇到问题：{result}")
                    new_tasks = self._replan_with_error(result)
                    if new_tasks:
                        self._say("planner", f"任务已重新编排：{new_tasks}")
                        self.task_list = new_tasks
                        self._update_ui()
                        # 简单粗暴：重新执行整个列表（可优化为续传）
                        return self._run_workflow_worker_loop()
                    else:
                        self._say("planner", "重排失败，任务中止。")
                        return
                task.status = "completed"
                task.result = result
                self._update_ui()
                self._say("worker", f"✅ 任务 {task.index} 完成。")

            # 阶段3: Reviewer
            self.current_agent = "reviewer"
            self._update_ui()
            review_msg = self._phase_reviewer()
            if self._needs_rework(review_msg):
                self._say("reviewer", f"@Worker 审查未通过：{review_msg}")
                self._say("reviewer", "请重新执行未完成的任务。")
                # 此处简化处理：直接重置所有任务为 pending，让 Reviewer 提示用户手动重试
                for t in self.task_list:
                    t.status = "pending"
                self._update_ui()
            else:
                self._say("reviewer", "🎉 所有任务均已完成并通过审查。")
                self._say("reviewer", review_msg)
        except Exception as e:
            traceback.print_exc()
            if self.on_agent_message:
                self.on_agent_message("系统", f"多Agent工作流异常：{e}", "system")
        finally:
            self.is_running = False
            self.current_agent = None
            self._update_ui()
            if self.on_finished:
                self.on_finished()

    # 重新执行 worker 循环的辅助函数（重规划后复用）
    def _run_workflow_worker_loop(self):
        self.current_agent = "worker"
        for task in self.task_list:
            if self.stop_event.is_set():
                return
            task.status = "running"
            self._update_ui()
            self._say("worker", f"🔄 执行任务 {task.index}：{task.description}")
            result = self._execute_task(task)
            if self.stop_event.is_set():
                return
            if self._is_replan_request(result):
                self._say("worker", f"@Planner 任务 {task.index} 再次遇到问题：{result}")
                new_tasks = self._replan_with_error(result)
                if new_tasks:
                    self._say("planner", f"任务已重新编排：{new_tasks}")
                    self.task_list = new_tasks
                    self._update_ui()
                    return self._run_workflow_worker_loop()
                else:
                    self._say("planner", "重排失败，任务中止。")
                    return
            task.status = "completed"
            task.result = result
            self._update_ui()
            self._say("worker", f"✅ 任务 {task.index} 完成。")

    # ---------- Planner ----------
    def _phase_planner(self) -> bool:
        self.current_agent = "planner"
        self._update_ui()
        self._say("planner", "开始分析任务，查阅工具目录...")

        planner_prompt = (
            f"用户需求：{self.original_request}\n"
            "请严格按照你的系统提示工作，输出包含任务列表的 JSON 对象。"
        )
        raw = self._call_agent("planner", planner_prompt)
        # 尝试从 raw（即 AI 的 message 字段）中提取任务数组
        tasks = self._extract_task_list(raw)
        if not tasks:
            self._say("planner", "解析任务失败，重试一次...")
            raw = self._call_agent("planner", "请直接输出格式：{\"finish\":true, \"message\":\"['任务1','任务2']\"}")
            tasks = self._extract_task_list(raw)
        if tasks:
            self.task_list = [TaskItem(i + 1, d) for i, d in enumerate(tasks)]
            self._update_ui()
            return True
        return False

    def _extract_task_list(self, text: str) -> List[str]:
        # 1. 尝试从文本中提取 JSON 对象，拿到 message 数组
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                obj = json.loads(match.group())
                if isinstance(obj, dict) and "message" in obj:
                    msg = obj["message"]
                    if isinstance(msg, list):
                        return [str(item) for item in msg]
                    if isinstance(msg, str):
                        return [msg]
            except (json.JSONDecodeError, Exception):
                pass
        # 2. 尝试直接提取 JSON 数组
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                arr = json.loads(match.group())
                if isinstance(arr, list):
                    return [str(item) for item in arr]
            except (json.JSONDecodeError, Exception):
                pass
        # 3. 备用：按行分割并清理序号
        lines = [l.strip().lstrip("-*1234567890. ").rstrip(",") for l in text.splitlines() if l.strip()]
        if lines:
            return lines[:10]
        return []

    # ---------- Worker ----------
    def _execute_task(self, task: TaskItem) -> str:
        prompt = (
            f"原始需求：{self.original_request}\n"
            f"当前任务：{task.description}\n"
            "请执行该任务，完成后简短报告结果。如果遇到无法解决的困难，用 '@Planner' 开头说明问题。"
            f"""所有可用工具都分类存放在 ./tool_prompts/ 文件夹中。你k可以使用以下两个基础工具来读取这些分类文件，获取工具列表和注意事项：

- read_file(filepath, max_chars=800000): 读取文本文件内容。路径请使用相对路径，如 "./tool_prompts/文件操作（删除、移动、复制、创建目录、获取信息、列出目录）.txt"。返回内容以 SUCCESS/ERROR/INFO 开头。
- list_directory(path): 列出目录内容。例如，list_directory("./tool_prompts") 可查看有哪些分类文件。

【可用的工具分类文件】（路径均为 ./tool_prompts/）：
- 文件操作（删除、移动、复制、创建目录、获取信息、列出目录）.txt
- 文件读写（读取、分块读取、写入、搜索文件）.txt
- 系统命令与信息（执行命令、系统信息、py库安装）.txt
- 网络与下载还有浏览器自动化网页操作（下载视频、批量下载、网页提取、搜索、打开浏览器，导航、截图、获取文本、点击、填写、执行js脚本、关闭）.txt
- 键盘鼠标模拟（点击、输入、移动）.txt
- 办公文档处理（Excel、PDF、邮件，生成 Word 文档）.txt
- 多媒体编辑（图片、音频、视频）.txt
- 开发辅助（执行py代码、Git操作）.txt
- 硬件通信（串口、延时）.txt
- 记忆管理（添加长期记忆）.txt
- QQ交互（发送文件、撤回消息、加好友、加群，发送QQ语音，语音合成，向指定QQ或QQ群发送消息和表情包，从网络下载音乐并以语音形式发送到QQ）.txt
- 技能系统（执行技能）.txt
- 定时任务（添加、列表、删除）.txt
- 嵌入式开发仅限ARDUINO（安装CLI、核心、生成代码、编译、上传、检测、保存桌面、安装库）.txt
- 图像视频分析（分析图片、分析视频、QQ视频接收）.txt
- 屏幕截图（截图）.txt
- 物联网智能家居设备控制（查询设备，发送控制设备指令）.txt

在这些文件夹中包含了全部可用工具的详细介绍
"""
        )
        return self._call_agent("worker", prompt)

    # ---------- Reviewer ----------
    def _phase_reviewer(self) -> str:
        completed = [f"{t.index}. {t.description} → 结果: {t.result or '无'}" for t in self.task_list]
        prompt = (
            f"原始需求：{self.original_request}\n"
            f"任务执行情况：\n{chr(10).join(completed)}\n\n"
            "请审查：是否所有任务已真实完成？产物是否符合需求？如果发现未完成或错误，用 '@Worker' 开头指出问题；否则给出最终成功回复。"
        )
        return self._call_agent("reviewer", prompt)

    # ---------- 重规划 ----------
    def _replan_with_error(self, error_msg: str) -> List[str]:
        prompt = (
            f"原始需求：{self.original_request}\n"
            f"Worker 遇到问题：{error_msg}\n"
            "请重新生成 JSON 任务列表，仅数组。"
        )
        raw = self._call_agent("planner", prompt)
        tasks = self._extract_task_list(raw)
        return [TaskItem(i + 1, d) for i, d in enumerate(tasks)] if tasks else []

    # ---------- 辅助判断 ----------
    def _is_replan_request(self, text: str) -> bool:
        return "@Planner" in text or "重新规划" in text

    def _needs_rework(self, text: str) -> bool:
        return "@Worker" in text or "未完成" in text or "没有生成" in text
