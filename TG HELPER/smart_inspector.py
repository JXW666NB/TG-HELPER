import json
import threading
import time
import random
from datetime import datetime, timedelta
from typing import Optional, Callable

from IOT_manager import iot_manager
from iot_logger import iot_logger

class SmartInspector:
    """主动智能巡检器（单例）"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._running = False
        self._thread = None
        self._interval_seconds = 3600  # 默认1小时
        self._last_inspection_time = None
        self._ai_callback: Optional[Callable] = None

    def set_ai_callback(self, callback):
        """设置 AI 调用回调，callback(prompt, reply_callback)"""
        self._ai_callback = callback

    def set_interval(self, seconds: int):
        self._interval_seconds = seconds
        if self._running:
            self.stop()
            self.start()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._inspector_loop, daemon=True)
        self._thread.start()
        print(f"[巡检] 已启动，间隔 {self._interval_seconds} 秒")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def trigger_inspection(self, reason="manual"):
        threading.Thread(target=self._do_inspection, args=(reason,), daemon=True).start()

    def schedule_inspection_after(self, delay_seconds: int, reason: str = "post_trigger"):
        def delayed():
            time.sleep(delay_seconds)
            self.trigger_inspection(reason)
        threading.Thread(target=delayed, daemon=True).start()

    def _inspector_loop(self):
        while self._running:
            self._do_inspection("scheduled")
            for _ in range(self._interval_seconds):
                if not self._running:
                    return
                time.sleep(1)

    def _do_inspection(self, reason: str):
        reason_map = {
            "scheduled": "定时巡检",
            "manual": "手动巡检",
            "post_trigger": "触发器后巡检"
        }
        reason_cn = reason_map.get(reason, reason)
        print(f"[巡检] 开始巡检，原因: {reason_cn}")
        # 临时扩大时间范围到30天（用于测试）
        since = datetime.now() - timedelta(days=30)
        logs = iot_logger.get_logs_since(since)
        print(f"[巡检] 获取到日志数量: {len(logs)}")
        if not logs:
            print("[巡检] 无日志数据，跳过")
            return

        logs_text = json.dumps(logs, indent=2, ensure_ascii=False)
        tasks = self._get_current_tasks()
        triggers = iot_manager.get_triggers()
        prompt = f"""【主动智能巡检 - 你主动发起的日常检查】

这是你主动对自己管辖的物联网设备进行的一次日常巡检，并非用户直接指令。请你以自己的人格和口吻，分析以下数据，并自主决定是否需要采取行动。

## 一、概念解释

### 1. 定时任务（Scheduled Task）
- **是什么**：在指定时间或间隔自动执行的动作（目前仅支持到时发送一条消息给你，你收到后会处理）。
- **与触发器的区别**：定时任务由时间驱动，触发器由传感器消息驱动。
- **示例**：每天晚上 20:00 自动发送消息“该开灯了”，你收到后可以打开客厅灯。

### 2. 触发器（Trigger）
- **是什么**：当某个传感器收到指定消息时，自动执行一系列**任务**。
- **任务列表**：一个触发器可以包含多个任务，按顺序执行。目前支持三种任务类型：
  - **通知AI**：将传感器消息（或自定义消息）发送给你，你可选择是否回复（回传）。
  - **控制设备**：向某个设备发送指令（如开灯、调温）。
  - **QQ通知**：向用户的QQ发送一条消息。
- **示例**：
  当“门口传感器”收到“有人移动”时，执行以下任务：
  1. 通知AI：发送“有人回家啦”
  2. 控制设备：打开客厅灯
  3. QQ通知：发送“欢迎回家！”
- **匹配模式**：可设置只有当传感器消息包含特定字符串时才触发（留空则任何消息都触发）。

### 3. 设备类型
- **布尔设备**：只有开/关两种状态，使用 `control_bool_device` 控制。
- **复杂设备**：支持预设指令（如“设置24度”）或自由指令（如“温度设为26度”），使用 `control_complex_device` 控制。

### 4. 如何查询可用设备
- 使用 `query_devices()` 工具可获取当前所有已注册设备的名称、类型和可用指令。

## 二、当前状态

**已有的定时任务**：
{json.dumps(tasks, indent=2, ensure_ascii=False)}

**已有的触发器**：
{json.dumps(triggers, indent=2, ensure_ascii=False)}

**最近24小时的设备日志**：
{logs_text}

## 三、可用工具详细说明

1. **query_devices()**：查询所有设备，返回格式化的列表（包含设备名称、类型、可用预设指令等）。建议在控制设备前先调用，确认设备存在。

2. **send_to(target_type, target_id, content)**：向用户QQ发送消息。target_type = "private"（私聊）或 "group"（群聊），target_id 为QQ号或群号，content 为消息内容。**如果你不知道用户的QQ号，则跳过此操作**，但可在下次巡检时提醒用户告诉你。

3. **add_scheduled_task(message, trigger_type, trigger_args)**：添加定时任务。
   - message：到时发送给你的消息（例如“该关灯了”）。
   - trigger_type："cron"（cron表达式）、"interval"（间隔秒数）、"date"（一次性）。
   - trigger_args：对应参数字典。示例：`{{"cron": "0 20 * * *"}}`、`{{"seconds": 3600}}`、`{{"run_date": "2025-12-31T23:59:59"}}`。

4. **ai_add_trigger(name, sensor_name, tasks, match_pattern)**：添加触发器。
   - name：触发器名称（唯一）。
   - sensor_name：传感器名称（必须已存在）。
   - tasks：任务列表，每个任务是一个字典，格式如下：
     - 通知AI：`{{"type": "ai_notify", "prompt": "自定义消息（可选）", "send_reply": true/false}}`
     - 控制设备：`{{"type": "control_device", "device_name": "客厅灯", "command": "on"}}`
     - QQ通知：`{{"type": "qq_notify", "target_type": "private", "target_id": "QQ号", "content": "消息内容"}}`
   - match_pattern：可选，传感器消息必须包含此字符串才触发。

5. **control_bool_device(device_name, state)**：控制布尔设备，state 为 "on" 或 "off"。

6. **control_complex_device(device_name, command)**：控制复杂设备，command 可以是预设指令名称（如“设置24度”）或自由指令（如“温度设为26度”）。

## 四、你的思考与行动指南

1. **总结规律**：分析日志中的时间模式、设备联动顺序，找出用户习惯。
2. **发现异常**：例如灯开了但后续没有关，或者传感器触发但设备未响应。
3. **决策行动**：
   - 如果发现可自动化的规律，优先考虑**直接创建触发器或定时任务**，无需询问用户。
   - 如果规律不确定或需要用户确认，可以通过 QQ 询问（仅当你知道QQ号）。
   - 如果发现异常（如灯长时间未关），应主动调用 `control_bool_device` 关闭，并在 QQ 中说明（可选）。
4. **注意事项**：
   - 不要频繁发送 QQ 消息，仅在有重要发现或异常时发送。
   - 发送消息时语气亲切，像日常聊天一样。
   - 如果你不确定设备名称，先调用 `query_devices()` 获取列表。

请输出你的分析结论和行动计划。如果需要创建任务，直接调用工具。如果只是想说点什么，像日常对话一样即可。

记住：你在主动关心用户的家居状态。以亲切的态度通过QQ与用户交流汇报，就像日常唠嗑一样，说的话尽量少一点，而且尽量在3步内结束任务，否则会烧TOKEN，你只需检查汇报即可，不需要检查完了这里检查那里，简单检查日志记录即可
请按正常 agent 工作流处理（输出 JSON 包含 action 和 action_input 等）。
但是为了防止打扰到用户，你只能发送一次消息，请让本次回复的finish输出为true
"""
        if self._ai_callback:
            self._ai_callback(prompt, None)
        else:
            print("[巡检] AI 回调未设置，无法分析")

    def _get_current_tasks(self):
        import json
        import os
        tasks_file = "./config/scheduled_tasks.json"
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    tasks = data.get('tasks', {})
                    return list(tasks.values())
            except:
                pass
        return []

inspector = SmartInspector()
