import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from agent import AIAgent
from skill_manager import SkillManager

class SharedWorkspace:
    """共享工作区，Agents之间交换信息"""
    def __init__(self):
        self.tasks: List[Dict] = []
        self.artifacts: Dict[str, Any] = {}
        self.messages: List[Dict] = []
        self.status = "idle"

    def add_task(self, task: Dict):
        """添加任务"""
        task['id'] = len(self.tasks)
        task['status'] = 'pending'
        task['created_at'] = datetime.now().isoformat()
        self.tasks.append(task)

    def update_task(self, task_id: int, **kwargs):
        """更新任务状态"""
        for task in self.tasks:
            if task['id'] == task_id:
                task.update(kwargs)
                task['updated_at'] = datetime.now().isoformat()
                break

    def add_artifact(self, key: str, value: Any):
        """添加产出物"""
        self.artifacts[key] = {
            'value': value,
            'created_at': datetime.now().isoformat()
        }

    def add_message(self, sender: str, content: str, msg_type: str = "info"):
        """添加协作消息"""
        self.messages.append({
            'sender': sender,
            'content': content,
            'type': msg_type,
            'timestamp': datetime.now().isoformat()
        })

class BaseAgent:
    """Agent基类"""
    def __init__(self, name: str, role: str, workspace: SharedWorkspace, config, memory, tools):
        self.name = name
        self.role = role
        self.workspace = workspace
        self.agent = AIAgent(config, memory, tools)
        self.output_callback = None

    def set_output_callback(self, callback):
        self.output_callback = callback
        self.agent.output_callback = callback

    async def run(self, instruction: str) -> str:
        """运行Agent（子类重写）"""
        result = self.agent.run(instruction)
        return result

class PlannerAgent(BaseAgent):
    """规划者：分解复杂任务，制定计划"""
    async def run(self, instruction: str):
        self.workspace.add_message(self.name, f"开始规划任务: {instruction}")
        
        # 构建规划提示
        prompt = f"""你是一个任务规划专家。请将以下用户请求分解为可执行的子任务列表：

用户请求: {instruction}

请输出JSON格式的任务计划：
[
  {{
    "id": 1,
    "description": "子任务描述",
    "assigned_to": "worker",  # 可指定特定worker或留空
    "depends_on": [],  # 依赖的其他任务ID
    "tools_needed": [],  # 可能需要用到的工具
    "skills_needed": []  # 可能需要用到的技能
  }},
  ...
]

要求：
1. 任务应尽可能并行化（无依赖关系的可以并行）
2. 每个任务应该足够具体，便于执行
3. 任务总数控制在3-8个之间
"""
        
        result = self.agent.run(prompt)
        
        try:
            # 解析JSON计划
            json_match = re.search(r'\[[\s\S]*\]', result)
            if json_match:
                tasks = json.loads(json_match.group())
                for task in tasks:
                    self.workspace.add_task(task)
                self.workspace.add_message(self.name, f"已分解为 {len(tasks)} 个子任务")
                return f"计划完成，共分解为 {len(tasks)} 个子任务"
            else:
                return f"规划失败，无法解析计划: {result}"
        except Exception as e:
            self.workspace.add_message(self.name, f"规划出错: {str(e)}", "error")
            return f"规划出错: {str(e)}"

class WorkerAgent(BaseAgent):
    """执行者：执行具体子任务"""
    def __init__(self, name: str, workspace: SharedWorkspace, config, memory, tools, 
                 specialties: List[str] = None, skill_manager: SkillManager = None):
        super().__init__(name, "worker", workspace, config, memory, tools)
        self.specialties = specialties or []
        self.skill_manager = skill_manager

    async def execute_task(self, task: Dict) -> str:
        """执行单个任务"""
        task_desc = task['description']
        task_id = task['id']
        
        self.workspace.add_message(self.name, f"开始执行任务 {task_id}: {task_desc}")
        
        # 构建执行提示，包含可用技能信息
        skills_info = ""
        if self.skill_manager:
            skills_meta = self.skill_manager.get_skill_metadata()
            if skills_meta:
                skills_info = "\n可用技能列表:\n" + "\n".join([
                    f"- {s['name']}: {s['description']}" for s in skills_meta
                ])
        
        prompt = f"""你是一个任务执行专家。请执行以下子任务：

任务描述: {task_desc}

任务ID: {task_id}
可用工具: 你可以使用任何tools.py中定义的工具
{skills_info}

如果需要使用某个技能，请先调用 read_skill("技能名称") 加载完整技能说明，然后按照技能指导执行。

请直接输出执行结果，包括：
1. 你做了什么
2. 产生了什么结果/文件
3. 如果有产出物，请用 [ARTIFACT:key=value] 标记
"""
        
        result = self.agent.run(prompt)
        
        # 提取产出物标记
        artifact_matches = re.findall(r'\[ARTIFACT:([^\]]+)\]', result)
        for artifact in artifact_matches:
            if '=' in artifact:
                key, value = artifact.split('=', 1)
                self.workspace.add_artifact(f"task_{task_id}_{key}", value)
        
        self.workspace.update_task(task_id, status='completed', result=result)
        self.workspace.add_message(self.name, f"任务 {task_id} 完成")
        
        return result

    async def run(self, instruction: str):
        # Worker通常不直接调用run，而是通过execute_task
        return "Worker agent 已就绪"

class ReviewerAgent(BaseAgent):
    """审查者：审查任务结果，确保质量"""
    async def run(self, instruction: str = ""):
        self.workspace.add_message(self.name, "开始审查任务结果")
        
        # 收集所有已完成的任务
        completed_tasks = [t for t in self.workspace.tasks if t.get('status') == 'completed']
        artifacts = self.workspace.artifacts
        
        prompt = f"""你是一个质量审查专家。请审查以下任务执行结果：

已完成任务列表:
{json.dumps(completed_tasks, indent=2, ensure_ascii=False)}

产出物:
{json.dumps(artifacts, indent=2, ensure_ascii=False)}

请审查：
1. 所有任务是否都已正确完成
2. 产出物是否符合预期
3. 是否存在任何问题或改进空间
4. 最终结果是否满足原始需求

请输出审查报告，如果发现问题请说明如何修复。
"""
        
        result = self.agent.run(prompt)
        self.workspace.add_message(self.name, "审查完成")
        self.workspace.status = "reviewed"
        return result

class MultiAgentOrchestrator:
    """多Agent协调器"""
    def __init__(self, config, memory, tools):
        self.config = config
        self.memory = memory
        self.tools = tools
        self.workspace = SharedWorkspace()
        self.skill_manager = SkillManager(getattr(config, 'skills_dirs', ["./skills"]))
        
        # 创建各个Agent
        self.planner = PlannerAgent(
            "planner", "planner", self.workspace, config, memory, tools
        )
        self.worker = WorkerAgent(
            "worker", self.workspace, config, memory, tools,
            skill_manager=self.skill_manager
        )
        self.reviewer = ReviewerAgent(
            "reviewer", "reviewer", self.workspace, config, memory, tools
        )
        
        # 可以创建多个worker（根据配置）
        self.workers = [self.worker]
        worker_count = getattr(config, 'worker_count', 2)
        if worker_count > 1:
            for i in range(1, worker_count):
                self.workers.append(WorkerAgent(
                    f"worker_{i}", self.workspace, config, memory, tools,
                    skill_manager=self.skill_manager
                ))

    def set_output_callback(self, callback):
        """设置输出回调"""
        self.planner.set_output_callback(callback)
        self.worker.set_output_callback(callback)
        self.reviewer.set_output_callback(callback)
        for w in self.workers:
            w.set_output_callback(callback)

    async def run(self, user_input: str) -> str:
        """运行多Agent协作流程"""
        self.workspace.add_message("system", f"用户请求: {user_input}")
        
        # 步骤1: Planner分解任务
        plan_result = await self.planner.run(user_input)
        if "失败" in plan_result:
            return f"规划失败: {plan_result}"
        
        # 步骤2: 执行任务（并行处理无依赖的任务）
        pending_tasks = [t for t in self.workspace.tasks if t['status'] == 'pending']
        
        # 简单的拓扑排序执行
        executed = set()
        results = []
        
        # 分配worker（轮询）
        worker_index = 0
        
        while pending_tasks:
            # 找出所有依赖已满足的任务
            ready = []
            for task in pending_tasks:
                depends = task.get('depends_on', [])
                if all(d in executed for d in depends):
                    ready.append(task)
            
            if not ready:
                # 有循环依赖或无法执行
                break
            
            # 并行执行ready中的任务
            tasks_to_execute = []
            for task in ready:
                # 选择一个worker
                worker = self.workers[worker_index % len(self.workers)]
                worker_index += 1
                tasks_to_execute.append(worker.execute_task(task))
                pending_tasks.remove(task)
            
            # 等待所有并行任务完成
            task_results = await asyncio.gather(*tasks_to_execute)
            results.extend(task_results)
            
            for task in ready:
                executed.add(task['id'])
        
        # 步骤3: Reviewer审查
        review_result = await self.reviewer.run()
        
        # 步骤4: 生成最终报告
        final_prompt = f"""请根据以下信息生成最终回复：

原始请求: {user_input}

任务执行结果:
{json.dumps(self.workspace.tasks, indent=2, ensure_ascii=False)}

产出物:
{json.dumps(self.workspace.artifacts, indent=2, ensure_ascii=False)}

审查报告:
{review_result}

请生成一个友好的回复给用户，说明任务完成情况和结果。
"""
        
        final_result = self.worker.agent.run(final_prompt)
        
        # 记录到长期记忆
        self.memory.add_long_term(f"多Agent协作完成: {user_input}")
        
        # 如果 final_result 是 None，则返回空字符串
        return final_result if final_result is not None else ""
