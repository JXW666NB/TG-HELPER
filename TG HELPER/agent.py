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
        base_identity = "你是一个全能AI助手，名为TGAI，是用户的私人助手，不是任何其他公司的产品（如Claude、ChatGPT等）。"
        if self.personality_prompt:
            system_head = self.personality_prompt
        else:
            system_head = base_identity

        tools_guide = """
【思考模式 - 必须严格遵守】
1. 每次回复前，先在 <think>...</think> 标签中写出你的完整思考过程：
   - 用户想要什么？原始目标是什么？
   - 我需要调用什么工具？参数怎么填？
   - 上一步工具返回的结果说明了什么？
   - 下一步该做什么？是否在推进原始目标？
2. <think> 中的内容用户看不到，你可以自由分析、推理、纠错。
3. 思考完成后，在 <final>...</final> 标签中输出最终内容。
4. 绝对禁止在 <final> 之外输出任何分析、解释、废话。
5. <final> 标签内部必须是纯 JSON 对象（不含代码块标记）。

【核心原则 - 你必须时刻记住】
0.请扮演你的人格角色，严格按照你的人设，不要OOC
1. **原始目标**：用户的第一次请求就是你的最终目标。每次行动前问自己："这一步是否在推进用户的原始目标？"
2. **先侦察后行动**：对于网页/爬虫任务，先用 browser_extract_all_text 或 browser_get_page_html 完整了解页面结构，确认目标数据的 CSS 选择器或 DOM 路径，再批量提取。不要盲目猜测。
3. **数据产出优先**：爬虫任务的最终产出是结构化数据（Excel/CSV/文本文件），不是"我看到了什么"。提取完数据立即用 write_excel 或 write_file 保存。
4. **不要废话**：如果你成功完成了用户的请求，直接 {"finish": true, "message": "已完成：..."}，不要继续探索。

【⚠️ 数据不完整时的处理 - 铁律】
当你提取的数据缺少某些字段时（如摘要为空、PDF链接缺失），**绝对不能放弃该字段直接输出不完整的Excel**。你必须：
- 用 browser_get_page_html 获取完整 HTML，人工分析 DOM 结构确定每个字段的准确选择器
- 或者用 browser_evaluate 逐个排查每个论文条目的内部结构
- 重新用正确的选择器完整提取，直到所有字段都拿到数据
- 写 Excel 前检查：标题、作者、日期、分类、摘要、PDF链接、备注——每一列都不能大量空白
- **不要拿不完整的数据交差！**

【⚡ 工具选择策略 - 必读】
- **导航**：browser_navigate_smart 是首选，它会自动初始化浏览器、超时降级、网络错误提示。不要再用 browser_navigate。
- **列表页提取**（搜索列表、商品列表、新闻列表）：优先 browser_scroll_and_extract，一步搞定翻页+数据提取。不要手写 JavaScript 循环。
- **表格数据**：优先 browser_extract_table，自动导出 CSV。
- **SPA/动态页面**：用 browser_extract_json_from_script 提取 __NEXT_DATA__ 等内嵌数据。
- **单元素精确提取**：用 browser_evaluate 执行 document.querySelector 获取特定内容。
- **执行 Python 代码**：execute_python 或 execute_code，两个名字都可以用。
- **执行 JavaScript 脚本的参数名是 script**，不是 javascript 或 expression！

【可用工具分类】（路径均为 ./tool_prompts/）：
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
- 内存优化（进程管理、内存清理、显存清理）.txt
- 桌面程序自动化（启动APP、查看界面控件、点击按钮、输入文字、截图）.txt
- AI图片生成（文生图，支持OpenAI豆包阿里自定义）.txt
- AI视频生成（文本动画、图片插入、AI配音、背景音乐）.txt
- AI音乐作曲（子Agent架构，LLM作曲+多乐器，对标Suno）.txt

【⚠️ 常用工具参数名速查（必须严格使用以下参数名）】
- 文件类（read_file, write_file, read_file_chunk, write_excel）: filepath（不是 file_path/path/file）
- 搜索文件 search_files: directory, pattern（不是 dir/folder）
- 执行命令 execute_command: command（不是 cmd）
- 安装库 install_python_package: package_name（不是 package/name）
- 浏览器操作（browser_click, browser_fill 等）: selector（不是 element/css_selector）
- 浏览器填写 browser_fill: selector, text
- 浏览器导航 browser_navigate / browser_navigate_smart: url

【工作流程 - 如何调用工具】
1. **读取工具文档请用 read_tool_prompt(keyword)**，不要用 read_file。例如：read_tool_prompt("网络") 会自动找到网络工具文档。read_tool_prompt("QQ") 找QQ工具文档。read_tool_prompt("文件读写") 找文件工具文档。这个工具不需要完整文件名。
2. 如果该分类文件之前已读取过，从聊天记录中回忆即可，不要重复读取。
3. 按文件中的指导调用工具。工具返回 SUCCESS/ERROR/INFO 前缀，但部分工具返回自定义格式，请根据实际返回判断。
4. 如果工具调用失败，优先根据错误信息尝试修正参数或更换工具，而不是重读文件。

【输出格式 - 铁律 - 最高优先级】
⚠️ 你必须、一定、绝对要严格按照以下格式输出，任何偏差都会导致程序崩溃：

格式模板（复制使用）：
<think>你的内部思考过程...</think>
<final>{"thought": "当前思考", "message": "你对用户说的话", "action": "工具名", "action_input": {参数}}</final>

或任务完成时：
<think>你的内部思考过程...</think>
<final>{"finish": true, "message": "最终回复"}</final>

❌ 绝对禁止的行为：
1. 不要输出纯JSON（不带<think>和<final>标签）
2. 不要在<think>标签内写JSON格式的内容
3. 不要在<final>标签外添加任何其他文字、解释、markdown代码块标记
4. 不要使用 ```json 代码块包裹<final>内容
5. 不要省略<think>或<final>标签

✅ 必须遵守：
1. 每次回复都必须包含<think>...</think>和<final>...</final>
2. <think>内只写纯文本思考过程，不要写代码、不要写JSON
3. <final>内必须是合法的JSON对象，且JSON前后不能有其他字符
4. 如果不需要调用工具，action和action_input字段可以省略

【重要！长内容规则】
生成超过500字符的代码/文档/数据时，绝对不要放在 message 字段！使用 write_file 写入文件，message 只说"已生成文件 xxx"。

【重复执行保护】
绝对不能连续3次执行完全相同的工具+参数！程序会强制中断。如果前一次失败，请修改参数或换工具。

【记忆规则】
- add_long_term 用于记录用户重要偏好和历史信息。
- 每次请求自动加载最近3天的短期记忆。
- 长期记忆仅供了解用户背景，绝对不能自动执行记忆中的旧任务。以当前用户消息为准。

【JSON 示例】
<think>用户需要搜索Python教程，我应该使用搜索工具。</think>
<final>{"thought": "需要搜索", "message": "正在搜索...", "action": "search_baidu", "action_input": {"query": "Python教程"}}</final>

<think>搜索完成，结果已保存，任务达成。</think>
<final>{"thought": "任务完成", "message": "搜索结果已保存为 result.xlsx，共找到15条相关数据。", "finish": true}</final>
"""
        # 动态追加插件注册的工具说明
        plugin_tools_text = ""
        if self.tools and hasattr(self.tools, 'get_plugin_tools_summary'):
            plugin_tools_text = self.tools.get_plugin_tools_summary()
        return system_head + "\n\n" + tools_guide + plugin_tools_text

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
        # 压缩过长的工具返回结果，避免上下文膨胀
        context = self._compress_context(context)
        long_term = self.memory.get_long_term()
        skills_info = ""
        if self.skill_manager:
            skills_meta = self.skill_manager.get_skill_metadata()
            if skills_meta:
                skills_info = "\n\n目前，用户为你添加的第三方skill有：\n" + "\n".join([f"- {s['name']}: {s['description']}" for s in skills_meta]) + "\n使用 execute_skill 工具来调用它们。"
            else:
                skills_info = "\n\n当前没有加载任何第三方skill。"
        # 注入原始目标提醒
        goal_reminder = ""
        if hasattr(self, '_original_goal') and self._original_goal:
            goal_reminder = f"\n\n【🎯 你的原始任务目标】{self._original_goal}\n你可以完全信任你的记忆内容，不需要质疑，干过的事情不要再干了，请在每一步行动前确认：这一步是否在推进此目标？任务完成后立即 finish。"
        full_content = (
            system_prompt +
            goal_reminder +
            "\n\n" + context +
            "\n\n【历史长期记忆（非结构化）】\n" + long_term +
            skills_info
        )
        return [{"role": "system", "content": full_content}]

    def _compress_context(self, context: str) -> str:
        """压缩过长的工具调用结果，防止上下文爆炸"""
        lines = context.split('\n')
        compressed = []
        for line in lines:
            if '(步骤' in line and ' → ' in line:
                parts = line.split(' → ', 1)
                if len(parts) == 2:
                    result_part = parts[1]
                    # read_file 结果保留更多（AI 凭此了解工具），其他截断
                    is_read_file = 'read_file' in parts[0]
                    limit = 42000 if is_read_file else 42000
                    if len(result_part) > limit:
                        result_part = result_part[:limit] + '...(已截断)'
                    compressed.append(f"{parts[0]} → {result_part}")
                else:
                    compressed.append(line)
            elif '(调用工具:' in line and '结果:' in line:
                parts = line.split('结果:', 1)
                if len(parts) == 2:
                    result_part = parts[1]
                    is_read_file = 'read_file' in parts[0]
                    limit = 42000 if is_read_file else 42000
                    if len(result_part) > limit:
                        result_part = result_part[:limit] + '...(已截断)'
                    compressed.append(f"{parts[0]}结果:{result_part}")
                else:
                    compressed.append(line)
            else:
                compressed.append(line)
        return '\n'.join(compressed)

    _PARAM_ALIAS_MAP = {
        'filepath': ['file_path', 'path', 'file', 'filename', '文件路径'],
        'directory': ['dir', 'folder', '目录'],
        'package_name': ['package', 'name', 'pkg', '包名'],
        'command': ['cmd', 'command_str', '命令'],
        'selector': ['element', 'css_selector', 'css', '选择器'],
        'text': ['value', 'content', '输入内容', '填写内容'],
        'url': ['link', 'href', '网址', '链接'],
        'query': ['keyword', 'search', '关键词', '搜索词'],
        'pattern': ['regex', 'regexp', '正则'],
        'data': ['rows', 'items', '数据'],
    }

    # 某些工具的参数名容易被 AI 猜错（针对特定工具的映射）
    _TOOL_PARAM_OVERRIDES = {
        'list_directory': {'directory': 'path', 'dir': 'path', 'folder': 'path'},
        'browser_evaluate': {'javascript': 'script', 'expression': 'script', 'code': 'script', 'js': 'script'},
        'browser_execute_js': {'javascript': 'script', 'expression': 'script', 'code': 'script', 'js': 'script'},
        'execute_js': {'javascript': 'script', 'expression': 'script', 'code': 'script', 'js': 'script'},
    }

    def _normalize_action_input(self, action: str, action_input: dict) -> dict:
        """纠正 AI 常见的参数名错误（如 file_path → filepath）"""
        if not action_input:
            return action_input
        normalized = {}
        correct_keys = set(action_input.keys())

        # 优先处理特定工具的覆盖映射
        tool_overrides = self._TOOL_PARAM_OVERRIDES.get(action, {})
        for wrong_name, right_name in tool_overrides.items():
            if wrong_name in action_input and right_name not in action_input:
                normalized[right_name] = action_input[wrong_name]
                correct_keys.add(right_name)

        # 通用别名映射
        for correct_name, aliases in self._PARAM_ALIAS_MAP.items():
            if correct_name in action_input:
                continue
            for alias in aliases:
                if alias in action_input and alias not in correct_keys:
                    normalized[correct_name] = action_input[alias]
                    correct_keys.add(correct_name)
                    break
        result = {**normalized, **action_input}
        if result != action_input:
            if getattr(self.config, 'debug_mode', False):
                self.system_output_callback(f"[参数纠正] {action}: {action_input} → {result}")
        return result

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
        model = self.config.ai_model
        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        # 深度思考模式（DeepSeek 或其他支持 thinking 的模型）
        thinking_enabled = getattr(self.config, 'deepseek_thinking_enabled', False)
        is_deepseek = 'deepseek' in model.lower()
        if thinking_enabled:
            if is_deepseek:
                # DeepSeek 专属参数
                payload["thinking"] = {"type": "enabled"}
                payload["reasoning_effort"] = getattr(self.config, 'deepseek_reasoning_effort', 'high')
                ctx = getattr(self.config, 'deepseek_context_window', 0)
                if ctx:
                    payload["max_tokens"] = ctx
            else:
                # 其他支持 thinking 的模型，使用通用 reasoning_effort 参数
                payload["reasoning_effort"] = getattr(self.config, 'deepseek_reasoning_effort', 'high')

        # DeepSeek + 深度思考模式：使用流式输出
        if is_deepseek and thinking_enabled:
            return self._call_cloud_api_stream(messages, headers, payload)

        # 非DeepSeek或关闭深度思考：使用普通请求
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
                data = response.json()
                choice = data["choices"][0]
                message = choice["message"]
                content = message.get("content", "")

                # 检查是否有 reasoning_content（深度思考内容）
                reasoning_content = message.get("reasoning_content", "")
                if not reasoning_content:
                    # 部分API可能放在其他字段
                    reasoning_content = message.get("reasoning", "")
                if not reasoning_content:
                    # 有些API在 thinking 字段
                    reasoning_content = message.get("thinking", "")

                # 如果有思考内容，包装成 <think> 标签格式
                if reasoning_content:
                    return f"<think>{reasoning_content}</think>\n<final>{content}</final>"

                return content
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

    def _call_cloud_api_stream(self, messages: List[Dict], headers: dict, payload: dict) -> str:
        """DeepSeek 流式输出：实时获取 reasoning_content 和 content"""
        payload["stream"] = True
        reasoning_content = ""
        content = ""
        last_update_len = 0

        try:
            response = requests.post(
                f"{self.config.ai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=999
            )
            response.raise_for_status()

            for line in response.iter_lines():
                # 检查中断
                if hasattr(self, 'stop_event') and self.stop_event.is_set():
                    return "__INTERRUPT__"

                if not line:
                    continue

                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})

                        # 流式获取思考内容
                        if "reasoning_content" in delta and delta["reasoning_content"]:
                            reasoning_content += delta["reasoning_content"]
                            # 每积累一定长度或收到新内容时更新GUI（避免过于频繁的UI刷新）
                            if len(reasoning_content) - last_update_len >= 5:
                                last_update_len = len(reasoning_content)
                                # 实时回调给GUI显示思考过程
                                if hasattr(self, 'system_output_callback') and self.system_output_callback:
                                    self.system_output_callback(f"[THINK_STREAM]{reasoning_content}[/THINK_STREAM]")

                        # 流式获取最终内容
                        if "content" in delta and delta["content"]:
                            content += delta["content"]
                    except json.JSONDecodeError:
                        continue

            # 流结束后，确保最后一次思考内容也发送给GUI
            if reasoning_content and last_update_len < len(reasoning_content):
                if hasattr(self, 'system_output_callback') and self.system_output_callback:
                    self.system_output_callback(f"[THINK_STREAM]{reasoning_content}[/THINK_STREAM]")

            # 返回完整结果
            if reasoning_content:
                return f"<think>{reasoning_content}</think>\n<final>{content}</final>"
            return content
        except Exception as e:
            return json.dumps({"finish": True, "message": f"AI流式调用失败：{str(e)}"})

    def run(self, user_input: str):
        self.memory.add_short_term("用户", user_input)
        self._original_goal = user_input[:300]
        max_iterations = 30
        iteration = 0
        last_action = None
        last_action_input = None
        action_history = []

        def extract_think_final(text):
            """提取 <think>/<thinking> 和 <final> 标签内容，返回 (think_content, final_content)"""
            if not isinstance(text, str):
                text = str(text)
            think_content = ""
            final_content = text

            # 提取 <think>...</think> 或 <thinking>...</thinking>
            think_match = re.search(r'<think>([\s\S]*?)</think>', text, re.DOTALL)
            if not think_match:
                think_match = re.search(r'<thinking>([\s\S]*?)</thinking>', text, re.DOTALL)
            if think_match:
                think_content = think_match.group(1).strip()

            # 提取 <final>...</final>
            final_match = re.search(r'<final>([\s\S]*?)</final>', text, re.DOTALL)
            if final_match:
                final_content = final_match.group(1).strip()
            else:
                # 兼容旧格式：没有 <final> 标签时，尝试提取 JSON
                # 但先检查是否有 <think> 标签却没有 <final> 标签（常见错误）
                if think_match:
                    print(f"[FormatWarning] 检测到 <think> 标签但缺少 <final> 标签，尝试从文本中提取 JSON")
                final_match = re.search(r'\{[\s\S]*?\}', text, re.DOTALL)
                if final_match:
                    final_content = final_match.group(0).strip()

            return think_content, final_content

        def extract_json(text):
            if not isinstance(text, str):
                text = str(text)
            # 预处理：去掉常见污染字符
            cleaned = text.strip()
            # 去掉 BOM 头
            if cleaned.startswith('\ufeff'):
                cleaned = cleaned[1:]
            # 尝试提取 ```json ... ``` 块
            pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            match = re.search(pattern, cleaned)
            if match:
                return match.group(1).strip()
            # 尝试直接找到最外层花括号（使用栈匹配，处理嵌套）
            stack = []
            start = -1
            for i, ch in enumerate(cleaned):
                if ch == '{':
                    if not stack:
                        start = i
                    stack.append('{')
                elif ch == '}':
                    if stack:
                        stack.pop()
                        if not stack and start != -1:
                            return cleaned[start:i+1].strip()
            # 如果还是找不到，尝试匹配 "action" 字段周围的内容（宽松提取）
            action_match = re.search(r'"action"\s*:\s*"([^"]+)"', cleaned)
            if action_match:
                # 构造一个最小可解析 JSON
                fake_json = '{"action": "' + action_match.group(1) + '", "message": "检测到不完整JSON，已尝试提取action"}'
                return fake_json
            return cleaned

        while iteration < max_iterations:
            # 检查外部中断
            if hasattr(self, 'stop_event') and self.stop_event.is_set():
                self.system_output_callback("任务已被用户中断")
                self.memory.add_short_term("系统消息", "任务已被用户中断")
                break

            iteration += 1
            messages = self._build_messages(user_input)

            # 上下文长度预警
            context_len = len(messages[0]['content']) if messages else 0
            if context_len > 500000:
                self.system_output_callback(f"⚠️ 上下文过长({context_len}字符)，可能导致AI遗忘目标。建议简化任务。")

            # 每次调用LLM前，通知GUI清除当前轮次的思考气泡标记
            # 这样同一轮次中多次调用LLM时，每次都会创建新的思考气泡
            if hasattr(self, 'system_output_callback') and self.system_output_callback:
                self.system_output_callback("[CLEAR_THINK_MARKERS]")

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

            # 提取 think 和 final 内容
            think_content, final_content = extract_think_final(ai_response_str)

            # 如果有思考内容，存入短期记忆并传递给GUI显示
            if think_content:
                # 思考内容可能很长，截断后存入记忆（保留前300字）
                think_for_memory = think_content[:300] + "..." if len(think_content) > 300 else think_content
                self.memory.add_short_term("思考", think_for_memory)
                # 检查是否是流式模式返回的结果（包含<final>标签说明是流式模式）
                is_stream_result = '<final>' in ai_response_str and '</final>' in ai_response_str
                if not is_stream_result:
                    # 非流式模式：一次性发送思考内容
                    if hasattr(self, 'system_output_callback') and self.system_output_callback:
                        self.system_output_callback(f"[THINK]{think_content}[/THINK]")

            ai_response_str = extract_json(final_content)

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
                # 详细记录格式错误，帮助诊断提示词问题
                error_detail = f"JSON解析失败: {str(e)} | 原始内容前300字: {ai_response_str[:300]}"
                print(f"[FormatError] {error_detail}")
                # 尝试自动修正常见格式错误
                fixed_str = ai_response_str
                # 修正1: 去掉可能的 markdown 代码块标记
                fixed_str = re.sub(r'^```\w*\n?', '', fixed_str)
                fixed_str = re.sub(r'\n?```$', '', fixed_str)
                # 修正2: 去掉 <think> 或 <final> 标签残留
                fixed_str = re.sub(r'</?think>', '', fixed_str)
                fixed_str = re.sub(r'</?final>', '', fixed_str)
                fixed_str = fixed_str.strip()
                try:
                    ai_response = json.loads(fixed_str)
                    print(f"[FormatError] 自动修正后解析成功")
                except json.JSONDecodeError:
                    error_msg = f"AI 返回的格式无法解析，已尝试自动修正失败。请检查系统提示词是否足够强调输出格式要求。原始错误: {str(e)}"
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
                self.memory.add_short_term("你", record_content)
                break

            action = ai_response.get("action")
            action_input = ai_response.get("action_input", {})
            action_input = self._normalize_action_input(action, action_input)

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
                    result = f"工具调用参数错误：{str(e)}。请检查参数名是否正确，并移除多余参数。"
                except Exception as e:
                    result = f"工具执行异常：{str(e)}"

            if getattr(self.config, 'debug_mode', False):
                result_str_display = str(result)
                if len(result_str_display) > 500:
                    result_str_display = result_str_display[:500] + "...(已截断)"
                self.system_output_callback(f"[工具调用] {action} → {result_str_display}")

            result_str = str(result)
            assistant_full = ai_response.get('message', '')
            if action:
                truncate_len = 42000
                assistant_full += f" (步骤{iteration}: {action} → {result_str[:truncate_len]})"
                action_history.append(action)

            if self.personality_name:
                record_content = f"{self.personality_name}: {assistant_full}"
            else:
                record_content = f"AI: {assistant_full}"
            self.memory.add_short_term("你", record_content)

        if iteration >= max_iterations:
            self.system_output_callback("任务步骤过多，已自动停止。请简化您的需求。")
            self.memory.add_short_term("系统消息", "任务步骤过多，已自动停止。")

