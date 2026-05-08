# TG HELPER v0.1.5 — Your all-can-do AI helper / work-mate / friend... suibian you call it ba

<p align="center">
  <strong>Desktop-level AI smart body — File do-do · Browser auto · IoT home · QQ robot · Proactive brain</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.5-blue" alt="version">
  <img src="https://img.shields.io/badge/python-3.9+-green" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-orange" alt="license">
  <img src="https://img.shields.io/badge/tools-70+-brightgreen" alt="tools">
  <img src="https://img.shields.io/badge/Gitee-JXWNB666-red" alt="gitee">
</p>

---

## 🤔 This B thing is what?

**TG HELPER** is one run on Windows de **AI Smart Body (AI Agent)**. Notice, not that kind only can say "sorry I cannot do this" de sha bi customer-service robot — **this thing really can do hands**.

You say "help me tidy shit mountain on desktop", it go baba file.
You say "go Amazon see today which Yiwu small thing can daomai", it jump wall just go.
You say "I go out forget close AC", it through IoT help you close, shunbian send one QQ message laugh you.

---

## ✨ Brag moment (but it's all real)

- 🤖 **Double model engine** — Cloud model suibian cut (OpenAI / DeepSeek / Kimi dengdeng) + local Ollama model run without net, your computer smoke I still can live
- 🌐 **Real go online** — Playwright drive de browser auto, bring anti-anti-crawl (random UA, pretend hand shake, change proxy). Even Amazon think you robot, it still can mix in and steal two pictures back
- 🏠 **IoT control center** — MQTT/TCP/UDP whole family. Add shebei, add sensor, make trigger, AI also can **zhudong xuncha** find you forget close light then close it, more cao xin than your mom
- 🧠 **Memory better than you** — Short + long + rethink three-piece + SQLite full-text search + maybe vector bank. What silly question you ask last year it all remember
- 🎭 **Personality fencrack mode** — Tage (warm soft man), Ai (tsundere yanjiu yuan), TGAI (no boy no girl no feeling). Can even let them group chat and fight each other, you eat gua zi watch show
- 🧩 **Chajian V2 world** — Declare permission, bring AI 翻译器 to move OpenClaw chajian over with one click. No can write code just call AI write for you
- 📱 **QQ robot deep in** — Connect your own QQ number. Auto receive pic/video and fenxi, group chat sometimes reply (even can use voice), auto agree friend add
- 🎨 **17 kinds skin** — From dark black mode to pink girly style, how sao you want, just how sao
- 🔒 **All ben di** — All data, memory, config file all in your harddrive. AI no steal your thing (unless you tell it to steal)
- 🛠️ **70+ tools** — Cover file manage, office auto, qianrushi (Arduino shao lu), media edit, keyboard mouse fangzhen, Git do...

---

## 📦 Quick start (3 seconds can not finish, please bear)

### Anzhuang

```bash
git clone https://gitee.com/JXWNB666/TG-HELPER.git
cd TG_HELPER
pip install -r requirements.txt
playwright install chromium
```

### Start

```bash
python "TG HELPER.py"
```

First time start will pop a setup wizard, fill in your API key (that need money kind, if no money then gun to use local Ollama). Then you can begin tiaoxi.

> ⚠️ If you use local big model, your notebook fan maybe take-off. Suggest don't let notebook run 70B model, unless you want make fried egg.

---

## 🤖 AI Engine

| Engine | Type | Shuo ming |
|--------|------|-----------|
| `cloud` | Cloud | OpenAI jianrong style, support DeepSeek, Kimi, SiliconFlow, OpenAI dengdeng |
| `local` | Ben di | Ollama local model, no need API key, just fei dian |

### Peizhi example (config.json)

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

## 🔌 Function bits (by where you use)

### Desktop caokong (True stand-user)

| Module | Tools count | Shuo ming |
|--------|-------------|-----------|
| File guanli | 9 | Read / write / delete / move / search / list dir / get info, what a house-keeper should do all done |
| System mingling | 3 | Run command, system info, install Python bao |
| Keyboard mouse fangzhen | 3 | Mouse click / move, keyboard input (need user say ok) |
| Screenshot | 1 | Full-screen pic, pyautogui one stroke |

### Network & Liulanqi (Cyber surf mode)

| Module | Tools count | Shuo ming |
|--------|-------------|-----------|
| Browser auto | 22+ | Playwright drive: go page / click / fill / screenshot / run JS / upload file / get link / download pic / iframe change / workflow batch run |
| Network tools | 5 | Download video (yt-dlp), batch download, webpage tiqv, Google search, open browser |
| Proxy fanqiang | 4 | Set proxy, install V2Ray, peizhi Clash |

### Office & chuangzuo

| Module | Tools count | Shuo ming |
|--------|-------------|-----------|
| Office auto | 5 | Excel read/write, mail send, make PDF, make Word |
| Media edit | 3 | Pic (crop/rotate/lvjing), sound (convert/edit/volume), video (cut/merge/get sound) |
| Duomotai fenxi | 3 | Pic fenxi, video fenxi, online video download + fenxi |

### IoT & Smart home (True Iron Man housekeeper)

| Module | Tools count | Shuo ming |
|--------|-------------|-----------|
| Shebei guanli | 4 | Find shebei, control true-false shebei, control complex shebei, shebei list |
| Sensor | — | MQTT/TCP/UDP listen, message auto trigger |
| Chufa qi | 3 | Sensor message → AI notice / control shebei / QQ notice, multi-job link |
| Built-in server | 2 | One-click start MQTT Broker / TCP Server |
| Zhudong xuncha | — | Every some time fenxi log, auto make its own auto rules |

### QQ Robot

| Module | Tools count | Shuo ming |
|--------|-------------|-----------|
| Message send/get | 3 | Send message, send file, send voice |
| Yuyin hecheng | 3 | TTS word-to-voice, send TTS, send net music |
| Friend/group guanli | 3 | Add friend, add group, take back message |
| Group chat pei ban | — | Maybe auto reply, can voice, stop group die-quiet |

### Qianrushi kaifa

| Module | Tools count | Shuo ming |
|--------|-------------|-----------|
| Arduino whole flow | 8 | Install CLI → install core → install library → make code → build → auto find board → shangchuan → save to desktop |

### Gaoji gongneng

| Module | Tools count | Shuo ming |
|--------|-------------|-----------|
| Jineng system | 1 | Load Skill folder, run script / see shuoming |
| Ding shi job | 3 | Based on APScheduler, support cron / every-x-seconds / one-time |
| Renge system | — | Inside build-in Tage, Ai, TGAI, can also DIY |
| Renao mode | — | Many renge same time group chat, AI fight each other, you chi gua |
| Jiyi system | — | Short + long + rethink + full-text search + vector bank |
| Multi-Agent | — | Planner/Worker/Reviewer work together (yuliu) |
| Plugin V2 | — | Declare permission + event bus + HostAPI |

---

## 🛡️ Safe machine-zhi

### Danger do confirm

All danger do (delete file, move mouse, run code dengdeng) default pop-up ask you ok. Can single close in settings. Safe read-only do just go directly.

### Browser safe

JavaScript run default open safe mode, no allow `eval`, `document.write`, `localStorage` these sao do. Unless you self close safe mode (not suggest, unless you know what you doing).

### Quanxian tixing

This thing can do your computer — **don't play on device that have sensitive file**. From net download de Skill/plugin first use "Safe check" go through.

---

## 🎮 Quick cao zuo

| Do | Shuo ming |
|----|-----------|
| Input box send | Press Enter send message, Shift+Enter new line |
| Click 「🏠 TG Home」 | Open IoT shebei guanli window |
| Click 「⚙️ Fold settings」 | Fold / unfold right side settings board |
| Click 「🔥 Renao mode」 | Change many-personality group chat mode |
| Settings → Theme choose | 17 skins suibian huan |

---

## 🏗️ Project jiegou

```
TG HELPER/
├── TG HELPER.py              # Launcher (check need-thing + set env + start GUI)
├── main_gui.py               # Main jiemian AgentGUI (chat + settings + all system in)
├── agent.py                  # AI talk loop (LLM call + JSON jiexi + tool diaodu)
├── tools.py                  # 🔧 70+ tool function (whole project heart)
├── memory.py                 # Three-level jiyi system + full-text search + vector bank
├── config.py                 # World peizhi
├── config_manager.py         # First-run peizhi wizard
├── tg_home.py                # IoT shebei guanli alone window
├── IOT_manager.py            # IoT shebei manager (MQTT/TCP/UDP)
├── smart_inspector.py        # Active brain xuncha
├── qq_bot.py                 # QQ robot WebSocket handler
├── task_scheduler.py         # Ding shi job diaodu
├── skill_manager.py          # Jineng bao manager
├── multi_agent.py            # Multi-Agent together (yuliu)
├── api_server.py             # Flask API server
├── builtin_servers.py        # Built-in MQTT/TCP server
├── hardware_detector.py      # Hardware check + model suggest
├── local_llm.py              # Local model think
├── local_model_manager.py    # Local model download/guanli
├── gui_handlers.py           # GUI settings page build function
├── plugin_base.py            # Old plugin base father
├── plugin_manager.py         # Old plugin manager
├── plugin_v2/                # 🧩 New plugin system V2
│   ├── base.py               # PluginV2 father
│   ├── manager.py            # Plugin manager
│   ├── host_api.py           # HostAPI safe jiekou
│   ├── events.py             # Event bus
│   ├── capabilities.py       # Quanxian shengming
│   ├── adapters/             # Third-party shi pei qi
│   ├── converter/            # AI plugin fanyi qi
│   └── compat/               # Old version jianrong
├── AI renge/                 # Renge peizhi
│   ├── TGAI/                 # Default renge
│   ├── Tage/                 # Warm man renge
│   └── Ai/                   # Tsundere renge
├── tool_prompts/             # Tool sort hints
├── device_configs/           # IoT shebei keep
├── plugins/                  # Old chajian
├── screenshots/              # Screenshot save place
├── downloads/                # Download file
├── icon/                     # Icon stuff
├── requirements.txt          # Python need-package
├── LICENSE                   # MIT License
├── README.md                 # This thing you reading
└── THIRD_PARTY_NOTICES.md    # Third-party need + license say
```

---

## 🧪 Kaifa & debug

Open debug mode, AI reply under will show tool call details. In settings → debug page tick on.

```bash
# Check Python world
python -c "import sys; print(sys.version)"

# Alone test tool
python -c "from tools import Tools; print(dir(Tools))"
```

---

## 🧩 Plugin kaifa show

### Old plugin (plugin_base)

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

### New Plugin V2 (plugin.json + main.py)

```json
{
  "id": "com.example.myplugin",
  "name": "My plugin",
  "version": "1.0.0",
  "description": "Plugin describe",
  "capabilities": ["ui.display"],
  "permissions": ["ui.display"],
  "entry_point": "main.py"
}
```

---

## 🤝 Give & feedback

Feel this project bad but funny, or want put your own shit mountain together? Welcome Issue, PR, or come QQ group **1082708943** to shout. If this thing make you laugh, please click Star ⭐️, author will feel deep and eat one more bowl pao mian.

---

## 📄 Xuke zheng

This project use [MIT License](LICENSE). Suibian change, suibian sell, suibian put into bi ye she ji — **but must keep author name**, or midnight will have AI climb your window.

This project use many many third-party open-source stuff, full list and license see [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

---

## 🔗 Link

- 📦 Gitee: https://gitee.com/JXWNB666/TG_HELPER
- 📖 [User shouce](./TG%20HELPER%20V0.1.5用户手册.docx)
- 📋 [Third-party notice](./THIRD_PARTY_NOTICES.md)

---

**Ta ma de finally done li**
— JXW, 2026 some-tongxiao-night morning
