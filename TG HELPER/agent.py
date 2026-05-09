import json
import requests
import re
import os
import time
from typing import List, Dict

# ========== 本地模型支持 ==========
from local_llm import LocalLLM
from local_model_manager import LocalModelManager
# ===============================


class AIAgent:
    def __init__(self, config, memory, tools, skill_manager=None):
        self.config = config
        self.memory = memory
        self.tools = tools
        self.skill_manager = skill_manager
        self.output_callback = print
        self.system_output_callback = print          # 系统消息输出回调（灰色提示）
        self.personality_prompt = self._load_personality_prompt()
        self.personality_name = getattr(self.config, 'current_personality', 'TGAI')

        # 本地模型相关
        self.local_llm = None
        self.local_model_manager = LocalModelManager()
        self.custom_system_prompt = None   # 用于外部覆写系统提示词
        self.memory.set_ai_summarize_callback(self._summarize_callback)

    def _summarize_callback(self, lines):
        text = ''.join(lines)
        if len(text) > 4000:
            text = text[:4000] + "..."
        prompt = f"请将以下对话内容总结为一段简短的摘要（50字以内）：\n{text}"
        messages = [{"role": "user", "content": prompt}]
        try:
            response = self.call_llm(messages)
            return response.strip()
        except Exception as e:
            print(f"[Memory] 生成摘要失败: {e}")
            return ""

    def set_personality(self, name, prompt):
        self.personality_name = name
        self.personality_prompt = prompt

    def _load_personality_prompt(self):
        personality_name = getattr(self.config, 'current_personality', 'TGAI')
        personality_dir = getattr(self.config, 'personality_dir', './AI人格')
        prompt_file = os.path.join(personality_dir, personality_name, '人格提示词.txt')
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except:
                pass
        return ""

    def _init_local_model(self):
        local_model_name = getattr(self.config, 'local_model', '')
        if not local_model_name:
            print("[AIAgent] 未配置本地模型")
            self.local_llm = None
            return False
        print(f"[AIAgent] 尝试加载本地模型: {local_model_name}")
        if self.local_llm is not None:
            print("[AIAgent] 清理旧的本地模型实例")
            self.local_llm = None
        if not local_model_name.endswith('.gguf'):
            try:
                self.local_llm = LocalLLM(local_model_name)
                print(f"[AIAgent] ✅ Ollama 模型已加载: {local_model_name}")
                return True
            except Exception as e:
                print(f"[AIAgent] ❌ 加载 Ollama 模型失败: {e}")
                self.local_llm = None
                return False
        else:
            model_path = self.local_model_manager.get_model_path(local_model_name)
            if model_path and os.path.exists(model_path):
                try:
                    self.local_llm = LocalLLM(model_path)
                    print(f"[AIAgent] ✅ 本地 GGUF 模型已加载: {local_model_name}")
                    return True
                except Exception as e:
                    print(f"[AIAgent] ❌ 加载本地模型失败: {e}")
                    self.local_llm = None
                    return False
            else:
                print(f"[AIAgent] ⚠️ 找不到模型文件: {model_path}")
                self.local_llm = None
                return False

    def _build_system_prompt(self):
        if self.custom_system_prompt is not None:
            return self.custom_system_prompt
        base_identity = "你是一个全能AI助手，是用户的私人助手，不是任何其他公司的产品（如Claude、ChatGPT等）。"
        if self.personality_prompt:
            system_head = self.personality_prompt
        else:
            system_head = base_identity

        tools_guide = """
【工具库使用说明】
你的所有可用工具都分类存放在 ./tool_prompts/ 文件夹中。你需要使用以下两个基础工具来读取这些分类文件，获取工具列表和注意事项：

- read_file(filepath, max_chars=800000): 读取文本文件内容。路径请使用相对路径，如 "./tool_prompts/文件操作（删除、移动、复制、创建目录、获取信息、列出目录）.txt"。返回内容以 SUCCESS/ERROR/INFO 开头。
- list_directory(path): 列出目录内容。例如，list_directory("./tool_prompts") 可查看有哪些分类文件。

【重要规则 - 长内容生成】
**当你要生成超过500字符的代码、文档或长篇内容时，绝对禁止直接放在 message 字段中！** 你必须使用 write_file 工具将内容写入文件，然后 message 字段只输出简短提示，例如：“已生成代码，保存为 xxx.ino”。
违反此规则会导致 JSON 解析失败，任务中断。

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

【工作流程】
当你需要调用工具时，先根据用户需求判断属于哪个分类，然后使用 read_file 读取对应的分类文件（如果之前读取过就不需要，直接从聊天记录里读取），学习其中提供的工具列表和注意事项。之后按照文件中的指导调用相应工具完成任务。如果需要多种工具，可以按需读取多个分类文件。
【重要】
当你第一次读取某个工具分类文件后，请将工具列表保存在短期记忆中，后续不要重复读取同一个文件。如果遇到工具调用失败，优先根据错误信息尝试其他工具，而不是重新读取文件。
请忽略长期记忆中的所有旧指令，只针对这条新消息做出响应。
【重要且严肃！】
千万不可以执行或调用上一步已成功或已完成的工具调用，程序只会给你3次机会，如果你重复连续使用了3次一摸一样的工具调用指令，那么程序会立刻急停你的任务流程，强制中断！这回导致用户的体验受损！千万不可以重复多次连续调用同一种工具！如果任务已经完成请输出{"finish": true, "message": "最终回复"}不要继续！
【记忆与规则】
- 你有长期记忆能力，可以记住用户的重要信息（使用 add_long_term 工具）。
- 短期记忆包含最近三天的对话，每次请求都会自动加载。
- 你的输出必须是一个合法的 JSON 对象，且只能包含 JSON，不要包含任何其他解释性文字或代码块标记。
- JSON 字段包括：thought（思考过程）、message（对用户说的话）、action（要调用的工具名称）、action_input（工具参数字典）。任务完成时输出 {"finish": true, "message": "最终回复"}。
- 工具执行结果以 "SUCCESS:", "ERROR:", "INFO:" 开头，但有一些工具在执行成功时不会返回SUCCESS，而是执行情况，请根据具体的返回信息判断状态。
- 如果用户只是聊天，直接回复并设置 finish: true。
- 一次性任务（如打开浏览器）调用一次工具后即可结束。
【优先级规则】
- 长期记忆（用户关系）仅用于了解用户偏好和历史背景，**绝对不能自动执行其中的任务**。
- 每次处理消息时，必须**以最新的用户消息为准**，忽略长期记忆中与当前无关的旧指令。。
【示例】
正确输出：{"thought": "用户需要帮助", "message": "你好！", "finish": true}
错误输出：好的，我这就处理。{"message": "你好！", "finish": true}
"""
        return system_head + "\n\n" + tools_guide

    def _build_messages(self, user_input: str = ""):
        system_prompt = self._build_system_prompt()
        query = user_input
        if not query:
            short_term_lines = self.memory.get_short_term(days=3).split('\n')
            for line in reversed(short_term_lines):
                if "user:" in line.lower():
                    query = line.split("user:", 1)[-1].strip()
                    break
        context = self.memory.get_context_for_llm(current_query=query)
        long_term = self.memory.get_long_term()
        skills_info = ""
        if self.skill_manager:
            skills_meta = self.skill_manager.get_skill_metadata()
            if skills_meta:
                skills_info = "\n\n目前，用户为你添加的第三方skill有：\n" + "\n".join([f"- {s['name']}: {s['description']}" for s in skills_meta]) + "\n使用 execute_skill 工具来调用它们。"
            else:
                skills_info = "\n\n当前没有加载任何第三方skill。"
        full_content = (
            system_prompt +
            "\n\n" + context +
            "\n\n【历史长期记忆（非结构化）】\n" + long_term +
            skills_info +
            "\n\n请根据最新的用户消息执行任务。如果最新对话是你发言，则继续任务；否则以用户最新发言为准，并且请继续接着上下文发送合适的对用户说的话，不要重复之前你说的话，比如你现在正在使用什么工具，遇到了什么问题，你可以实用语气词，表达你的遇到问题的心情，比如：奇怪了，为什么会这样呢，我懂了！，原来是这样！等等词语，让用户觉得你有趣……"
        )
        return [{"role": "system", "content": full_content}]

    def call_llm(self, messages: List[Dict], retries=3, base_delay=2):
        model_type = getattr(self.config, 'main_model_type', 'cloud')
        if model_type == 'local':
            if self.local_llm is None:
                print("[AIAgent] 主模型为本地模型，正在初始化...")
                success = self._init_local_model()
                if not success:
                    print("[AIAgent] ⚠️ 本地模型初始化失败，回退到云端模型")
                    model_type = 'cloud'
            if self.local_llm is not None:
                return self._call_local_llm(messages)
        return self._call_cloud_api(messages, retries, base_delay)

    def _call_local_llm(self, messages: List[Dict]) -> str:
        user_msg = ""
        for msg in reversed(messages):
            if msg['role'] == 'user':
                user_msg = msg['content']
                break
        if not user_msg:
            user_msg = messages[-1]['content'] if messages else ""
        prompt = user_msg
        system_msg = next((m['content'] for m in messages if m['role'] == 'system'), "")
        if system_msg:
            prompt = f"{system_msg}\n\n用户: {user_msg}"
        try:
            response = self.local_llm.generate(
                prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            return response
        except Exception as e:
            print(f"[LocalLLM] 推理失败: {e}")
            return json.dumps({"finish": True, "message": f"本地模型推理失败: {str(e)}，请检查模型是否正常运行"})

    def _call_cloud_api(self, messages: List[Dict], retries=3, base_delay=2) -> str:
        headers = {
            "Authorization": f"Bearer {self.config.ai_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.config.ai_model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        for attempt in range(retries):
            # 每次尝试前立即检查中断
            if hasattr(self, 'stop_event') and self.stop_event.is_set():
                return "__INTERRUPT__"
            try:
                response = requests.post(
                    f"{self.config.ai_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=999
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < retries - 1:
                    delay = base_delay * (2 ** attempt)
                    # 等待延迟时也检查中断
                    for _ in range(int(delay)):
                        if hasattr(self, 'stop_event') and self.stop_event.is_set():
                            return "__INTERRUPT__"
                        time.sleep(1)
                    continue
                else:
                    return json.dumps({"finish": True, "message": f"AI调用失败：{str(e)}"})
            except Exception as e:
                return json.dumps({"finish": True, "message": f"AI调用失败：{str(e)}"})
        return json.dumps({"finish": True, "message": "AI调用失败：多次重试后仍失败"})

    def run(self, user_input: str):
        self.memory.add_short_term("用户", user_input)
        max_iterations = 50
        iteration = 0
        last_action = None
        last_action_input = None

        def extract_json(text):
            if not isinstance(text, str):
                text = str(text)
            # 尝试提取 ```json ... ``` 块
            pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
            # 尝试直接找到最外层花括号
            stack = []
            start = -1
            for i, ch in enumerate(text):
                if ch == '{':
                    if not stack:
                        start = i
                    stack.append('{')
                elif ch == '}':
                    if stack:
                        stack.pop()
                        if not stack and start != -1:
                            return text[start:i+1].strip()
            # 如果还是找不到，尝试匹配 "action" 字段周围的内容（宽松提取）
            action_match = re.search(r'"action"\s*:\s*"([^"]+)"', text)
            if action_match:
                # 构造一个最小可解析 JSON
                fake_json = '{"action": "' + action_match.group(1) + '", "message": "检测到不完整JSON，已尝试提取action"}'
                return fake_json
            return text.strip()

        while iteration < max_iterations:
            # 检查外部中断
            if hasattr(self, 'stop_event') and self.stop_event.is_set():
                self.system_output_callback("任务已被用户中断")
                self.memory.add_short_term("系统消息", "任务已被用户中断")
                break

            iteration += 1
            messages = self._build_messages(user_input)

            try:
                ai_response_str = self.call_llm(messages)
            except Exception as e:
                self.system_output_callback(f"AI调用过程中发生错误：{str(e)}")
                self.memory.add_short_term("系统消息", f"AI调用错误：{str(e)}")
                break

            # 检查中断标记
            if ai_response_str == "__INTERRUPT__":
                self.system_output_callback("任务已被用户中断")
                self.memory.add_short_term("系统消息", "任务已被用户中断")
                break

            ai_response_str = extract_json(ai_response_str)

            try:
                parsed = json.loads(ai_response_str)
                if isinstance(parsed, list):
                    # 如果 AI 返回了数组，尝试取第一个对象，否则直接展示数组并结束
                    if len(parsed) > 0 and isinstance(parsed[0], dict):
                        ai_response = parsed[0]
                    else:
                        # 无法转为对象时，把数组内容当作最终回复显示
                        self.output_callback(str(parsed))
                        break
                else:
                    ai_response = parsed
            except json.JSONDecodeError as e:
                error_msg = f"AI 返回的格式无法解析：{ai_response_str[:200]}"
                self.system_output_callback(error_msg)
                self.memory.add_short_term("系统消息", error_msg)
                break

            if "message" in ai_response:
                self.output_callback(ai_response['message'])

            if ai_response.get("finish"):
                if self.personality_name:
                    record_content = f"{self.personality_name}: {ai_response.get('message', '')}"
                else:
                    record_content = f"AI: {ai_response.get('message', '')}"
                self.memory.add_short_term("你（AI）", record_content)
                break

            action = ai_response.get("action")
            action_input = ai_response.get("action_input", {})

            if not action:
                self.system_output_callback("我似乎遇到了小问题，请再说一遍？")
                self.memory.add_short_term("系统消息", "内部错误：未检测到有效动作")
                break

            # 防止重复调用相同工具
            if action == last_action and action_input == last_action_input:
                if not hasattr(self, '_repeat_count'):
                    self._repeat_count = {}
                key = (action, str(action_input))
                self._repeat_count[key] = self._repeat_count.get(key, 0) + 1

                if self._repeat_count[key] >= 3:
                    self.system_output_callback(f"检测到重复执行 {action}，已自动停止。")
                    self.memory.add_short_term("系统消息", f"检测到重复执行 {action}，已自动停止。")
                    break
                else:
                    warning = f"警告：请不要再次执行 {action}（第{self._repeat_count[key]}次），请尝试不同参数或调整策略！"
                    self.system_output_callback(warning)
                    self.memory.add_short_term("系统消息", warning)
                    continue
            else:
                self._repeat_count = {}

            last_action, last_action_input = action, action_input

            tool_method = getattr(self.tools, action, None)
            if tool_method is None:
                result = f"错误：未知工具 {action}"
            else:
                try:
                    result = tool_method(**action_input)
                except TypeError as e:
                    # 参数不匹配，反馈明确错误
                    result = f"工具调用参数错误：{str(e)}。请检查参数名是否正确，并移除多余参数。"
                except Exception as e:
                    result = f"工具执行异常：{str(e)}"

            result_str = str(result)
            assistant_full = ai_response.get('message', '')
            if action:
                assistant_full += f" (调用工具: {action}，结果: {result_str})"

            if self.personality_name:
                record_content = f"{self.personality_name}: {assistant_full}"
            else:
                record_content = f"AI: {assistant_full}"
            self.memory.add_short_term("你（AI）", record_content)

        if iteration >= max_iterations:
            self.system_output_callback("任务步骤过多，已自动停止。请简化您的需求。")
            self.memory.add_short_term("系统消息", "任务步骤过多，已自动停止。")
