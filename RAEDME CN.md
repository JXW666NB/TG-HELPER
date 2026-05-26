# TG HELPER v0.2.5 —— 你的全能型AI助手/同事/朋友……随便你怎么称呼罢

<p align="center">
  <strong>桌面级 AI 智能体 — 文件操作 · 浏览器自动化 · 物联网中心 · QQ 机器人 · 主动智能</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.5-blue" alt="version">
  <img src="https://img.shields.io/badge/python-3.9+-green" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-orange" alt="license">
  <img src="https://img.shields.io/badge/tools-70+-brightgreen" alt="tools">
  <img src="https://img.shields.io/badge/Gitee-JXWNB666-red" alt="gitee">
</p>

---

## 🤔 这 B 玩意儿是啥？

**TG HELPER** 是个跑在 Windows 上的 **AI 智能体（AI Agent）**。注意，不是那种只会说"对不起我不能这样"的傻逼客服机器人——**这玩意儿是真能动手的**。

你说"帮我把桌面上的屎山整理一下"，它就去扒拉文件。
你说"去亚马逊看看今天哪个义乌小商品能倒卖"，它翻墙就冲了。
你说"我出门忘关空调了"，它通过物联网给你关了，顺便发条 QQ 消息嘲讽你


---

## ✨ 吹牛逼环节（但确实是真的）

- 🤖 **双模型引擎** — 云端模型随便切（OpenAI / DeepSeek / Kimi 等）+ 本地 Ollama 模型离线跑，你电脑冒烟我也能苟
- 🌐 **真正的网上冲浪** — Playwright 驱动的浏览器自动化，自带反反爬虫（随机 UA、假装手抖、切换马甲代理），哪怕亚马逊把你当机器人，它也能混进去偷两张图
- 🏠 **物联网控制中心** — MQTT/TCP/UDP 全家桶，加设备、加传感器、配触发器，AI 还会**主动巡检**发现你忘了关灯然后帮你关，比你妈还操心
- 🧠 **记忆比你好** — 短期+长期+反思三件套 + SQLite 全文检索 + 可选向量库，你去年问过啥蠢问题它都记得
- 🎭 **人格分裂模式** — 塔戈（温柔暖男）、艾依（傲娇研究员）、TGAI（无性别性冷淡），还能让他们一起群聊互喷，你嗑瓜子看戏
- 🧩 **插件 V2 生态** — 声明式权限，自带 AI 翻译器把 OpenClaw 插件一键移民过来，不会写代码就叫 AI 替你写
- 📱 **QQ 机器人深度整合** — 接自己的 QQ 号，自动收图/收视频并分析，群聊概率性回复（甚至能用语音），自动同意好友申请
- 🎨 **17 种皮肤** — 从暗黑模式到粉嫩少女风，想怎么骚就怎么骚
- 🔒 **完全本地** — 所有数据、记忆、配置文件全在你硬盘上，AI 不会偷你东西（除非你让他偷）
- 🛠️ **70+ 工具** — 覆盖文件管理、办公自动化、嵌入式开发（Arduino 烧录）、多媒体编辑、键鼠模拟、Git 操作……

---

## 📦 快速开始（3 秒装不完，你忍忍）

### 安装

```bash
git clone https://gitee.com/JXWNB666/TG-HELPER.git
cd TG_HELPER
pip install -r requirements.txt
playwright install chromium
```

### 启动

```bash
python "TG HELPER.py"
```

首次启动会弹配置向导，填上你的 API Key（要钱的那种，没钱就滚去用本地 Ollama）。然后你就可以开始调戏了。

> ⚠️ 如果你用本地大模型，电脑风扇可能会起飞。建议不要让笔记本跑 70B 模型，除非你想煎鸡蛋。

---

## 🤖 AI 引擎

| 引擎 | 类型 | 说明 |
|------|------|------|
| `cloud` | 云端 | OpenAI 兼容格式，支持 DeepSeek、Kimi、硅基流动、OpenAI 等 |
| `local` | 本地 | Ollama 本地模型，无需 API 密钥，就是费电 |

### 配置示例 (config.json)

```json
{
  "ai_api_key": "your-api-key",
  "ai_base_url": "https://api.deepseek.com/v1",
  "ai_model": "deepseek-chat",
  "local_model": "qwen2.5:7b",
  "main_model_type": "cloud",
  "max_tokens": 2000,
  "temperature": 1.0
}
```

---

## 🔌 功能模块（按场景分类）

### 桌面操控（真·替身使者）

| 模块 | 工具数 | 说明 |
|------|--------|------|
| 文件管理 | 9 | 读/写/删/移/搜/列目录/获取信息，管家该干的都干了 |
| 系统命令 | 3 | 执行命令、系统信息、装 Python 包 |
| 键鼠模拟 | 3 | 鼠标点击/移动、键盘输入（需用户确认） |
| 屏幕截图 | 1 | 全屏截图，pyautogui 一把梭 |

### 网络与浏览器（赛博冲浪模式）

| 模块 | 工具数 | 说明 |
|------|--------|------|
| 浏览器自动化 | 22+ | Playwright 驱动，导航/点击/填写/截图/JS 执行/上传文件/提取链接/下载图片/iframe 切换/工作流批量执行 |
| 网络工具 | 5 | 下载视频(yt-dlp)、批量下载、网页提取、Google 搜索、打开浏览器 |
| 代理翻墙 | 4 | 设置代理、安装 V2Ray、配置 Clash |

### 办公与创作

| 模块 | 工具数 | 说明 |
|------|--------|------|
| 办公自动化 | 5 | Excel 读写、邮件发送、生成 PDF、生成 Word |
| 多媒体编辑 | 3 | 图片(裁剪/旋转/滤镜)、音频(转换/剪辑/调音量)、视频(剪辑/合并/提音频) |
| 多模态分析 | 3 | 图片分析、视频分析、网络视频下载+分析 |

### 物联网与智能家居（真·钢铁侠管家）

| 模块 | 工具数 | 说明 |
|------|--------|------|
| 设备管理 | 4 | 查询设备、控制布尔设备、控制复杂设备、设备列表 |
| 传感器 | — | MQTT/TCP/UDP 监听，消息自动触发 |
| 触发器 | 3 | 传感器消息 → AI 通知/控制设备/QQ 通知，多任务串联 |
| 内置服务器 | 2 | 一键启动 MQTT Broker / TCP Server |
| 主动巡检 | — | 定时分析日志，自己创建自动化规则 |

### QQ 机器人

| 模块 | 工具数 | 说明 |
|------|--------|------|
| 消息收发 | 3 | 发消息、发文件、发语音 |
| 语音合成 | 3 | TTS 文字转语音、发送 TTS、网络音乐发送 |
| 好友/群管理 | 3 | 加好友、加群、撤回消息 |
| 群聊陪伴 | — | 概率性自动回复，可语音，防止冷群 |

### 嵌入式开发

| 模块 | 工具数 | 说明 |
|------|--------|------|
| Arduino 全流程 | 8 | 装 CLI → 装核心 → 装库 → 生成代码 → 编译 → 自动检测板子 → 上传 → 保存桌面 |

### 高级功能

| 模块 | 工具数 | 说明 |
|------|--------|------|
| 技能系统 | 1 | 加载 Skill 文件夹，执行脚本/查看说明 |
| 定时任务 | 3 | 基于 APScheduler，支持 cron/间隔/一次性 |
| 人格系统 | — | 内置塔戈/艾依/TGAI，可自定义创建 |
| 热闹模式 | — | 多人格同时群聊，AI 互喷，你吃瓜 |
| 记忆系统 | — | 短期+长期+反思+全文检索+向量库 |
| 多 Agent | — | Planner/Worker/Reviewer 协作（预留） |
| 插件 V2 | — | 声明式权限+事件总线+HostAPI |

---

## 🛡️ 安全机制

### 危险操作确认

所有危险操作（删文件、移动鼠标、执行代码等）默认弹窗确认，可在设置里单独关。安全的读取操作直接放行。

### 浏览器安全

JavaScript 执行默认开启安全模式，禁止 `eval`、`document.write`、`localStorage` 等骚操作。除非你自己关掉安全模式（不推荐，除非你清楚自己在干什么）。

### 权限提醒

这玩意儿能操作你电脑——**别在存敏感文件的设备上瞎搞**。从网上下载的 Skill/插件先用"安全检查"过一遍。

---

## 🎮 快捷操作

| 操作 | 说明 |
|------|------|
| 输入框发送 | 按 Enter 发送消息，Shift+Enter 换行 |
| 点击「🏠 TG Home」 | 打开物联网设备管理窗口 |
| 点击「⚙️ 收起设置」 | 折叠/展开右侧设置面板 |
| 点击「🔥 热闹模式」 | 切换多人格群聊模式 |
| 设置 → 主题选择 | 17 种皮肤随便换 |

---

## 🏗️ 项目结构

```
TG HELPER/
├── TG HELPER.py              # 启动器（依赖检查+环境配置+启动 GUI）
├── main_gui.py               # 主界面 AgentGUI（聊天+设置+集成所有子系统）
├── agent.py                  # AI 对话循环（LLM 调用+JSON 解析+工具调度）
├── tools.py                  # 🔧 70+ 工具函数（整个项目的核心）
├── memory.py                 # 三级记忆系统+全文检索+向量库
├── config.py                 # 全局配置
├── config_manager.py         # 首次运行配置向导
├── tg_home.py                # 物联网设备管理独立窗口
├── IOT_manager.py            # 物联网设备管理器（MQTT/TCP/UDP）
├── smart_inspector.py        # 主动智能巡检
├── qq_bot.py                 # QQ 机器人 WebSocket 处理器
├── task_scheduler.py         # 定时任务调度
├── skill_manager.py          # 技能包管理器
├── multi_agent.py            # 多 Agent 协作（预留）
├── api_server.py             # Flask API 服务器
├── builtin_servers.py        # 内置 MQTT/TCP 服务器
├── hardware_detector.py      # 硬件检测+模型推荐
├── local_llm.py              # 本地模型推理
├── local_model_manager.py    # 本地模型下载/管理
├── gui_handlers.py           # GUI 设置页构建函数
├── plugin_base.py            # 旧版插件基类
├── plugin_manager.py         # 旧版插件管理器
├── plugin_v2/                # 🧩 新版插件系统 V2
│   ├── base.py               # PluginV2 基类
│   ├── manager.py            # 插件管理器
│   ├── host_api.py           # HostAPI 安全接口
│   ├── events.py             # 事件总线
│   ├── capabilities.py       # 权限声明
│   ├── adapters/             # 第三方适配器
│   ├── converter/            # AI 插件翻译器
│   └── compat/               # 旧版兼容
├── AI人格/                   # 人格配置
│   ├── TGAI/                 # 默认人格
│   ├── 塔戈/                  # 暖男人格
│   └── 艾依/                  # 傲娇人格
├── tool_prompts/             # 工具分类提示词
├── device_configs/           # 物联网设备持久化
├── plugins/                  # 旧版插件
├── screenshots/              # 截图保存
├── downloads/                # 下载文件
├── icon/                     # 图标资源
├── requirements.txt          # Python 依赖
├── LICENSE                   # MIT 许可证
├── README.md                 # 你正在看的这玩意儿
└── THIRD_PARTY_NOTICES.md    # 第三方依赖+许可证声明
```

---

## 🧪 开发与调试

开启调试模式后，AI 回复下方会显示工具调用详情。在设置 → 调试页勾选即可。

```bash
# 检查 Python 环境
python -c "import sys; print(sys.version)"

# 单独测试工具
python -c "from tools import Tools; print(dir(Tools))"
```

---

## 🧩 插件开发示例

### 旧版插件（plugin_base）

```python
class BasePlugin:
    def __init__(self, gui, tools, config):
        self.gui = gui
        self.tools = tools
        self.config = config

    def on_load(self):
        pass

    def on_unload(self):
        pass

    def register_command(self, command, handler):
        self._commands[command] = handler
```

### 新版插件 V2（plugin.json + main.py）

```json
{
  "id": "com.example.myplugin",
  "name": "我的插件",
  "version": "1.0.0",
  "description": "插件描述",
  "capabilities": ["ui.display"],
  "permissions": ["ui.display"],
  "entry_point": "main.py"
}
```

---

## 🤝 贡献与反馈

觉得这项目烂得清奇，或者想把自己写的屎山合并进来？欢迎提 Issue、PR，或者进 QQ 群 **1082708943** 开喷。如果你被这项目逗笑了，请点个 Star ⭐️，作者会感动到多吃一碗泡面。

---

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。随便改、随便卖、随便塞进毕设里——**但得把原作者名字留着**，否则半夜会有 AI 爬你窗户。

本项目使用了大量第三方开源软件，完整列表及许可证见 [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md)。

---

## 🔗 链接

- 📦 Gitee: https://gitee.com/JXWNB666/TG_HELPER
- 📖 [用户手册](./TG%20HELPER%20V0.1.5用户手册.docx)
- 📋 [第三方依赖声明](./THIRD_PARTY_NOTICES.md)

---

**踏马的终于肝完力**
—— JXW, 2026 年某个通宵的凌晨
