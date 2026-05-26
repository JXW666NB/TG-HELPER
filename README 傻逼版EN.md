# TG HELPER v0.2.5 — You di 甚么都能干 AI 帮帮手/同做事/朋朋... 随便 you call it lah

<p align="center">
  <strong>桌面子 level AI 阿金特 — 文件搞搞 · 浏览自自 · IoT 家 · QQ 机人 · 主动脑脑</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.5-blue" alt="version">
  <img src="https://img.shields.io/badge/python-3.9+-green" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-orange" alt="license">
  <img src="https://img.shields.io/badge/tools-70+-brightgreen" alt="tools">
  <img src="https://img.shields.io/badge/Gitee-JXWNB666-red" alt="gitee">
</p>

---

## 🤔 This B thing is waht?

**TG HELPER** 是 run on Windows 的 one **AI 阿金特**. 注意听，no 那种 only can say "对不起 I no can do lah" 的 sha bi 客服机人 —— **这个thing is 真的 can do 手手**.

You say “把 wo 桌面子 上 de shit 山山 整整”, it go gogo 文件.
You say “go 亚麻孙 看看 today 什么 义乌 小dongxi 能 倒卖卖”, it 跳wall 冲冲.
You say “wo 出门 forgot close 冷气”, it 通过 IoT 给你 close 掉, 顺便 发条 QQ 信信 笑话你.

---

## ✨ 吹吹 part (但 全部是 truth de)

- 🤖 **两个 莫得尔 engine** — Cloud 莫得尔 随便 cut (Open爱 / Deep爱 / Kimi 等等等) + local Ollama 莫得尔 没网 run, you 电脑 冒烟 窝也 can 活活
- 🌐 **真真 surf 网网** — Playwright 驱 的 浏览 自自, 自带 反反爬 (random UA, pretend hand 抖, change 代理马甲). 就suan 亚麻孙 把 you 当 robot, 它 also can 混进去 steal 两张 pic 回来
- 🏠 **IoT 控控 center** — MQTT/TCP/UDP 全家 桶桶. add 设备, add 传感, 配 触发, AI also can **主动巡巡** find you forget close 灯 then 帮 you close, 比 you 麻麻 more 操心
- 🧠 **记性 比比 you 好** — 短 + 长 + 反想 三件套套 + SQLite 全文 search + or 向量 库库. 去年 you 问 的 傻傻 question 它 all 记记
- 🎭 **人格 splite 模式** — 塔戈 (warm warm man), 艾依 (傲傲 研究), TGAI (no 男 no 女 no 感) . 甚至 can 让 they 一起 群聊聊 互相喷喷, you 吃瓜子 看看 show
- 🧩 **插件 V2 世世界** — declare 权限, bring AI 翻译器器 把 OpenClaw 插件 一 click 搬过. no can write code just call AI write for you
- 📱 **QQ 机人 deep together** — connect 自己 QQ 号号. auto 收图/收video and 分分, 群聊 概概 回复 (even can 用 voice), auto agree 好友 apply
- 🎨 **17 种 skinn** — from 黑黑 mode to 粉粉 girly wind, 想 how 骚骚 just how 骚骚
- 🔒 **全全 ben地** — 所有 数数, 记记, config 文件 all in you harddisk. AI no 偷偷 you 东西 (除非 you let it 偷偷)
- 🛠️ **70+ 工具具** — cover 文件 管管, 办公 自动动, 嵌入入 (Arduino 烧录录), 媒体 编编, 键鼠 模模, Git 做做...

---

## 📦 快开开始 (3 seconds no 可能 装完完, 忍忍)

### 装装

```bash
git clone https://gitee.com/JXWNB666/TG-HELPER.git
cd TG_HELPER
pip install -r requirements.txt
playwright install chromium
```

### 开开

```bash
python "TG HELPER.py"
```

第一 first time 开开会 弹 一个 setup 向导导, fill you de API key (那 need 钱钱 de, no 钱 gun 去用 local 奥拉马). then you can 开始 戏戏.

> ⚠️ if you use local 大大模型, 笔记本 fan 会 飞飞. suggest no 让笔记本 run 70B 模型, unless you 想 煎 egg.

---

## 🤖 AI 引引擎

| 引引擎 | type | 说说 |
|--------|------|------|
| `cloud` | 云端 | OpenAI 容容 format, support DeepSeek, Kimi, 硅流, OpenAI 等等 |
| `local` | ben地 | Ollama local 模型, no need API key, just 费电电 |

### 配置 例例 (config.json)

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

## 🔌 功功 块块 (按 哪用用)

### 桌面 控控 (真真·替身 使使)

| 模块块 | 工具 数数 | 说说 |
|--------|--------|------|
| 文件 管管 | 9 | read/write/delete/move/search/list 目/get info, 管家 该 do 的 all done |
| 系统 命命 | 3 | run command, system info, 装 Python 包包 |
| 键鼠 模模 | 3 | mouse click/move, 键盘 input (need user say yes) |
| 截截 | 1 | full-screen 截图, pyautogui 一 suō |

### 网网 & 浏览 (Cyber surf 模模)

| 模块块 | 工具 数数 | 说说 |
|--------|--------|------|
| 浏览 自动动 | 22+ | Playwright 驱: 导/click/fill/截/run JS/上文件/extract link/down 图/切 iframe/工作流 batch run |
| 网 tools | 5 | 下 video(yt-dlp), batch down, 网页 extract, Google search, open browser |
| 代理 跳墙墙 | 4 | set 代理, 装 V2Ray, 配 Clash |

### 办公 & 创创作

| 模块块 | 工具 数数 | 说说 |
|--------|--------|------|
| 办公 自自 | 5 | Excel read/write, send mail, make PDF, make Word |
| 媒体 编编 | 3 | pic(裁/转/filter), audio(转/剪/音音), video(剪/合/extract 音) |
| 多模 分分 | 3 | pic 分分, video 分分, net video down+分分 |

### IoT & 智家 (真真·铁人 管家)

| 模块块 | 工具 数数 | 说说 |
|--------|--------|------|
| 设备 管管 | 4 | 找设备, control bool 设备, control complex 设备, 设备 list |
| 传感感 | — | MQTT/TCP/UDP listen, message auto trigger |
| 触发 trigger | 3 | 传感 message → AI notify/控设备/QQ notify, multi-job 串 |
| 内建 server | 2 | one-click start MQTT Broker / TCP Server |
| 主动巡巡 | — | 定时 analyze log, auto make 自动化 rules |

### QQ 机机人

| 模块块 | 工具 数数 | 说说 |
|--------|--------|------|
| 信信 send/get | 3 | send 信, send 文件, send voice |
| 语音 sheng成 | 3 | TTS 字转voice, send TTS, send net 音乐 |
| 好友/群 管管 | 3 | add 友, add 群, 撤回 信信 |
| 群聊 陪陪 | — | 概率 auto re, can voice, stop 群 die quiet |

### 嵌入入 开开

| 模块块 | 工具 数数 | 说说 |
|--------|--------|------|
| Arduino 全流 | 8 | install CLI → install core → install lib → make code → build → auto find board → 上传 → save to 桌面子 |

### 高高 功功

| 模块块 | 工具 数数 | 说说 |
|--------|--------|------|
| 技能 system | 1 | Load 技能 folder, run script/看 docs |
| 定时 job | 3 | base on APScheduler, support cron/间隔/一shot |
| 人格 system | — | inside 塔戈/艾依/TGAI, DIY make |
| 热闹 mode | — | 多人格 same time 群聊, AI mutual spray, you eat melon |
| 记记 system | — | short+long+rethink+fulltext search+向量 store |
| 多 Agent | — | Planner/Worker/Reviewer 一起 (预预) |
| Plugin V2 | — | declare 权限+event bus+HostAPI |

---

## 🛡️ 安安 机机

### danger 操 认认

all danger 操 (delete file, move 鼠, run code etc) default pop ask you agree. can 关 in settings. safe read 操 direct pass.

### 浏览 安安

JS run default on safe mode, no let `eval`, `document.write`, `localStorage` 这种 sao sao 动作. unless you self close safe mode (no recommend, unless you know you在做什么).

### 权限 tixing

this thing 能 do you 电脑 — **别 on 有 sensitive file de 设备 上 乱搞**. from net download de 技能/plugin first use "safe check" go through.

---

## 🎮 快快 操

| 操作作 | 说说 |
|------|------|
| input box send | press Enter 发信, Shift+Enter 换 line |
| click 「🏠 TG Home」 | open IoT device manage window |
| click 「⚙️ 收 setting」 | fold/unfold right setting board |
| click 「🔥 闹闹 mode」 | switch 多人格聊 mode |
| 设置 → theme choose | 17 skins 随便换 |

---

## 🏗️ project 结结

```
TG HELPER/
├── TG HELPER.py              # 启器 (dep check + env set + start GUI)
├── main_gui.py               # main 面 AgentGUI (chat + setting + all system in)
├── agent.py                  # AI 话 loop (LLM call + JSON parse + tool 调)
├── tools.py                  # 🔧 70+ tool func (whole project 心)
├── memory.py                 # 3-level 记 system + fulltext search + vector store
├── config.py                 # 全局 set
├── config_manager.py         # first-run set 导
├── tg_home.py                # IoT device manage alone window
├── IOT_manager.py            # IoT device manager (MQTT/TCP/UDP)
├── smart_inspector.py        # 主动智能 巡巡
├── qq_bot.py                 # QQ 机人 WebSocket handler
├── task_scheduler.py         # 定时 job 调
├── skill_manager.py          # 技能 pack manager
├── multi_agent.py            # 多Agent 合 (预)
├── api_server.py             # Flask API server
├── builtin_servers.py        # 内建 MQTT/TCP servers
├── hardware_detector.py      # 硬 check + model recommend
├── local_llm.py              # 本地 model think
├── local_model_manager.py    # 本地 model down/manage
├── gui_handlers.py           # GUI set page build func
├── plugin_base.py            # old plugin base father
├── plugin_manager.py         # old plugin manager
├── plugin_v2/                # 🧩 new plugin V2
│   ├── base.py               # PluginV2 父
│   ├── manager.py            # Plugin manager
│   ├── host_api.py           # HostAPI safe 接口
│   ├── events.py             # Event bus
│   ├── capabilities.py       # 权限 declare
│   ├── adapters/             # third-party 适配
│   ├── converter/            # AI plugin 翻译器
│   └── compat/               # old 兼容
├── AI 人格/                  # 人格 set
│   ├── TGAI/                 # default 人格
│   ├── 塔戈/                  # warm man 人格
│   └── 艾依/                  # tsundere 人格
├── tool_prompts/             # tool 类 hints
├── device_configs/           # IoT device 持
├── plugins/                  # old plugins
├── screenshots/              # 截 save place
├── downloads/                # 下 files
├── icon/                     # icon 源
├── requirements.txt          # Python deps
├── LICENSE                   # MIT 许
├── README.md                 # you 在 read 的 this one
└── THIRD_PARTY_NOTICES.md    # 3rd-party deps + 许
```

---

## 🧪 开开 & 调调

open debug mode, AI reply under will show tool call detail. go settings → debug page tick.

```bash
# check Python env
python -c "import sys; print(sys.version)"

# alone test tool
python -c "from tools import Tools; print(dir(Tools))"
```

---

## 🧩 插件 开 show

### old plugin (plugin_base)

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

### new Plugin V2 (plugin.json + main.py)

```json
{
  "id": "com.example.myplugin",
  "name": "wo di plugin",
  "version": "1.0.0",
  "description": "plugin desc",
  "capabilities": ["ui.display"],
  "permissions": ["ui.display"],
  "entry_point": "main.py"
}
```

---

## 🤝 贡 & 反反馈

jude 此 project bad 但 fun, or 想 把 own shit mountain merge in? welcome 提 Issue, PR, or enter QQ 群 **1082708943** 喷喷. if this thing make you laugh, pls click Star ⭐️, author will 感动 to eat one more bowl 泡面面.

---

## 📄 许许证

this project use [MIT License](LICENSE). 随便 change, 随便 sell, 随便 stuff into 毕设 — **but must keep author name**, else midnight will have AI climb you window.

this project use many many 3rd-party open 源 stuff, full list & license see [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

---

## 🔗 link

- 📦 Gitee: https://gitee.com/JXWNB666/TG_HELPER
- 📖 [user 手册](./TG%20HELPER%20V0.1.5用户手册.docx)
- 📋 [3rd-party notice](./THIRD_PARTY_NOTICES.md)


**ta ma de finally 肝完完 li**
— JXW, 2026 some tongxiao early morning
