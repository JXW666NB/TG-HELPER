# TG HELPER v0.1.5 — Your All-in-One AI Assistant / Colleague / Buddy... Call It Whatever You Want

<p align="center">
  <strong>Desktop-level AI Agent — File Operations · Browser Automation · IoT Hub · QQ Bot · Proactive Intelligence</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.5-blue" alt="version">
  <img src="https://img.shields.io/badge/python-3.9+-green" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-orange" alt="license">
  <img src="https://img.shields.io/badge/tools-70+-brightgreen" alt="tools">
  <img src="https://img.shields.io/badge/Gitee-JXW666NB-red" alt="github">
</p>

---

## 🤔 What the Hell Is This Thing?

**TG HELPER** is an **AI Agent** that runs on Windows. Mind you, it's not one of those dumb customer-service bots that just says "Sorry, I can't do that" — **this thing actually gets its hands dirty.**

You say, "Tidy up the mess on my desktop," and it goes and sorts your files.
You say, "Go check Amazon and see which Yiwu knockoff I can flip today," and it busts through the firewall and charges in.
You say, "Shit, I left the AC on," and it turns it off via IoT, then sends you a QQ message to mock you for it.

---

## ✨ The Bragging Section (But It's All True)

- 🤖 **Dual-Model Engine** — Switch cloud models on the fly (OpenAI / DeepSeek / Kimi / etc.) + run local Ollama models offline. Even if the internet dies, I'll survive on your PC's fumes.
- 🌐 **Actual Web Surfing** — Playwright-powered browser automation with built-in anti-anti-bot measures (random user agents, simulated human-like jitter, proxy rotation). Even if Amazon marks you as a bot, it can still sneak in and steal a few pics.
- 🏠 **IoT Control Center** — Full MQTT/TCP/UDP stack. Add devices, add sensors, configure triggers. The AI also does **proactive inspections** — if it spots you left the lights on, it'll turn them off. More attentive than your mom.
- 🧠 **Memory Better Than Yours** — Short-term + long-term + reflection triple-layer memory + SQLite full-text search + optional vector store. It remembers every dumb question you asked last year.
- 🎭 **Split Personality Mode** — Tage (gentle warm guy), Ai (tsundere researcher), TGAI (genderless and emotionless). You can even throw them into a group chat to roast each other while you munch popcorn and watch.
- 🧩 **Plugin V2 Ecosystem** — Declarative permissions, built-in AI translator to one-click port OpenClaw plugins. Can't code? Just tell the AI to write it for you.
- 📱 **Deep QQ Bot Integration** — Hook up your own QQ account. Auto-download and analyze images/videos, probabilistic group-chat replies (even with voice), auto-accept friend requests.
- 🎨 **17 Skins** — From dark mode to pink pastel cuteness. Go as flamboyant as you want.
- 🔒 **Fully Local** — All data, memories, and config files live on your hard drive. The AI won't steal your stuff (unless you tell it to).
- 🛠️ **70+ Tools** — File management, office automation, embedded development (Arduino flashing), multimedia editing, keyboard/mouse simulation, Git operations… you name it.

---

## 📦 Quick Start (Won't Be Done in 3 Seconds, Bear with It)

### Installation

```bash
git clone https://gitee.com/JXWNB666/TG-HELPER.git
cd TG_HELPER
pip install -r requirements.txt
playwright install chromium
```

### Launch

```bash
python "TG HELPER.py"
```

On first launch, a setup wizard will pop up — fill in your API key (the kind that costs money; if you're broke, go use local Ollama). Then you can start messing around.

> ⚠️ If you use a local large model, your laptop fans might take off. Do NOT try to run a 70B model on a notebook unless you want to fry an egg on it.

---

## 🤖 AI Engine

| Engine | Type | Description |
|--------|------|-------------|
| `cloud` | Cloud | OpenAI-compatible format, supports DeepSeek, Kimi, SiliconFlow, OpenAI, etc. |
| `local` | Local | Ollama local models, no API key needed, just a lot of electricity |

### Config Example (config.json)

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

## 🔌 Feature Modules (Grouped by Scenario)

### Desktop Control (A True Stand User)

| Module | Tools | Description |
|--------|-------|-------------|
| File Management | 9 | Read/write/delete/move/search/list directory/get info. Everything a butler should do. |
| System Commands | 3 | Execute commands, system info, install Python packages. |
| Mouse & Keyboard Simulation | 3 | Mouse click/move, keyboard input (requires user confirmation). |
| Screenshot | 1 | Full-screen screenshot, powered by pyautogui. |

### Network & Browser (Cyber Surfing Mode)

| Module | Tools | Description |
|--------|-------|-------------|
| Browser Automation | 22+ | Playwright-driven: navigation, click, fill, screenshot, JS execution, file upload, link extraction, image download, iframe switching, workflow batch execution. |
| Network Tools | 5 | Download video (yt-dlp), batch download, webpage extraction, Google search, open browser. |
| Proxy & Circumvention | 4 | Set proxy, install V2Ray, configure Clash. |

### Office & Creativity

| Module | Tools | Description |
|--------|-------|-------------|
| Office Automation | 5 | Read/write Excel, send email, generate PDF, generate Word. |
| Multimedia Editing | 3 | Image (crop/rotate/filter), Audio (convert/trim/adjust volume), Video (trim/merge/extract audio). |
| Multimodal Analysis | 3 | Image analysis, video analysis, online video download + analysis. |

### IoT & Smart Home (The Real Iron Man Butler)

| Module | Tools | Description |
|--------|-------|-------------|
| Device Management | 4 | Query devices, control boolean devices, control complex devices, device list. |
| Sensors | — | MQTT/TCP/UDP listening, automatic message-triggered actions. |
| Triggers | 3 | Sensor messages → AI notifications / device control / QQ notifications, multi-task chaining. |
| Built-in Servers | 2 | One-click start MQTT Broker / TCP Server. |
| Proactive Inspection | — | Scheduled log analysis, auto-creates automation rules. |

### QQ Bot

| Module | Tools | Description |
|--------|-------|-------------|
| Message Sending & Receiving | 3 | Send messages, send files, send voice. |
| Speech Synthesis | 3 | TTS text-to-speech, send TTS, send online music. |
| Friend/Group Management | 3 | Add friend, join group, recall messages. |
| Group Chat Companion | — | Probabilistic auto-reply, supports voice, prevents dead silence in groups. |

### Embedded Development

| Module | Tools | Description |
|--------|-------|-------------|
| Arduino Full Flow | 8 | Install CLI → install cores → install libraries → generate code → compile → auto-detect board → upload → save to desktop. |

### Advanced Features

| Module | Tools | Description |
|--------|-------|-------------|
| Skill System | 1 | Load skill folders, execute scripts/read documentation. |
| Scheduled Tasks | 3 | Based on APScheduler, supports cron/interval/one-shot. |
| Personality System | — | Built-in Tage, Ai, TGAI; create custom ones. |
| Bustling Mode | — | Multiple personalities group-chatting simultaneously, AI roasting each other while you spectate. |
| Memory System | — | Short-term + long-term + reflection + full-text search + vector store. |
| Multi-Agent | — | Planner/Worker/Reviewer collaboration (reserved). |
| Plugin V2 | — | Declarative permissions + event bus + HostAPI. |

---

## 🛡️ Security Mechanisms

### Dangerous Operation Confirmation

All dangerous operations (deleting files, moving mouse, executing code, etc.) will pop up a confirmation dialog by default. You can disable this individually in settings. Safe read-only operations are allowed straight through.

### Browser Security

JavaScript execution is sandboxed by default, blocking `eval`, `document.write`, `localStorage`, and other shady calls. Unless you turn off safe mode (not recommended, unless you really know what you're doing).

### Permission Notice

This thing can control your computer — **don't mess around on devices containing sensitive files**. Always run a "Safety Check" on Skills/plugins downloaded from the internet first.

---

## 🎮 Quick Operations

| Action | Description |
|--------|-------------|
| Input box send | Press Enter to send, Shift+Enter for newline. |
| Click 「🏠 TG Home」 | Open the IoT device management window. |
| Click 「⚙️ Collapse Settings」 | Collapse/expand the right-side settings panel. |
| Click 「🔥 Bustling Mode」 | Toggle multi-personality group-chat mode. |
| Settings → Theme Selection | 17 skins to switch between at will. |

---

## 🏗️ Project Structure

```
TG HELPER/
├── TG HELPER.py              # Launcher (dependency check + env config + start GUI)
├── main_gui.py               # Main GUI AgentGUI (chat + settings + integrates all subsystems)
├── agent.py                  # AI conversation loop (LLM calls + JSON parsing + tool dispatch)
├── tools.py                  # 🔧 70+ tool functions (the core of the entire project)
├── memory.py                 # Three-tier memory system + full-text search + vector store
├── config.py                 # Global configuration
├── config_manager.py         # First-run configuration wizard
├── tg_home.py                # Independent IoT device management window
├── IOT_manager.py            # IoT device manager (MQTT/TCP/UDP)
├── smart_inspector.py        # Proactive intelligent inspection
├── qq_bot.py                 # QQ Bot WebSocket handler
├── task_scheduler.py         # Scheduled task scheduler
├── skill_manager.py          # Skill package manager
├── multi_agent.py            # Multi-Agent collaboration (reserved)
├── api_server.py             # Flask API server
├── builtin_servers.py        # Built-in MQTT/TCP servers
├── hardware_detector.py      # Hardware detection + model recommendation
├── local_llm.py              # Local model inference
├── local_model_manager.py    # Local model download/management
├── gui_handlers.py           # GUI settings page builder functions
├── plugin_base.py            # Old plugin base class
├── plugin_manager.py         # Old plugin manager
├── plugin_v2/                # 🧩 New plugin system V2
│   ├── base.py               # PluginV2 base class
│   ├── manager.py            # Plugin manager
│   ├── host_api.py           # HostAPI secure interface
│   ├── events.py             # Event bus
│   ├── capabilities.py       # Capability declarations
│   ├── adapters/             # Third-party adapters
│   ├── converter/            # AI plugin translator
│   └── compat/               # Backward compatibility
├── AI personalities/         # Personality configs
│   ├── TGAI/                 # Default personality
│   ├── Tage/                 # Warm-guy personality
│   └── Ai/                   # Tsundere personality
├── tool_prompts/             # Tool category prompts
├── device_configs/           # IoT device persistence
├── plugins/                  # Old plugins
├── screenshots/              # Screenshot storage
├── downloads/                # Downloaded files
├── icon/                     # Icon resources
├── requirements.txt          # Python dependencies
├── LICENSE                   # MIT License
├── README.md                 # The thing you're reading right now
└── THIRD_PARTY_NOTICES.md    # Third-party dependencies + license notices
```

---

## 🧪 Development & Debugging

When debug mode is enabled, tool call details will be shown below the AI's reply. Check the option under Settings → Debug tab.

```bash
# Check Python environment
python -c "import sys; print(sys.version)"

# Test a tool individually
python -c "from tools import Tools; print(dir(Tools))"
```

---

## 🧩 Plugin Development Examples

### Old Plugin (plugin_base)

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
  "name": "My Plugin",
  "version": "1.0.0",
  "description": "Plugin description",
  "capabilities": ["ui.display"],
  "permissions": ["ui.display"],
  "entry_point": "main.py"
}
```

---

## 🤝 Contribution & Feedback

Think this project is spectacularly crappy, or want to merge your own pile of spaghetti code? Issues, PRs, or come scream in the QQ group **1082708943**. If this project made you chuckle, give it a Star ⭐️ and the author will be so moved he'll treat himself to an extra bowl of instant noodles.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). Feel free to modify, sell, or stuff it into your graduation thesis — **but you have to keep the original author's name**, otherwise an AI will climb through your window at midnight.

This project uses a large number of third-party open-source software; for the full list and licenses, see [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

---

## 🔗 Links

- 📦 Gitee: https://gitee.com/JXWNB666/TG_HELPER
- 📖 [User Manual](./TG%20HELPER%20V0.1.5用户手册.docx)
- 📋 [Third-Party Notices](./THIRD_PARTY_NOTICES.md)


**Holy shit, finally done.**
— JXW, on a sleepless night in 2026
