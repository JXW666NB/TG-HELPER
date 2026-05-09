# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 获取当前 spec 文件所在的目录（项目根目录）
PROJECT_ROOT = os.path.dirname(SPECPATH)

# 需要包含的隐藏导入
hiddenimports = [
    # ttkbootstrap 相关
    'ttkbootstrap',
    'ttkbootstrap.style',
    'ttkbootstrap.themes',
    # PIL 图片格式支持
    'PIL._tkinter_finder',
    'PIL.ImageTk',
    # 加密库
    'Crypto',
    'Crypto.Cipher',
    'Crypto.Cipher.AES',
    'Crypto.Random',
    'cryptography',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.primitives.ciphers',
    # MQTT
    'paho.mqtt.client',
    # WebSocket
    'websocket',
    'websockets',
    # 音视频处理
    'pydub',
    'edge_tts',
    'yt_dlp',
    'mutagen',
    'brotli',
    # 数据处理
    'pandas',
    'numpy',
    # 网络请求
    'requests',
    'urllib3',
    'certifi',
    # 任务调度
    'apscheduler',
    'apscheduler.schedulers.background',
    # 文件监控
    'watchdog',
    'watchdog.observers',
    'watchdog.events',
    # 向量数据库
    'chromadb',
    'sentence_transformers',
    # 自动化
    'pyautogui',
    'playwright',
    # 串口
    'serial',
    # Word 文档
    'docx',
    # HTML 解析
    'bs4',
    # PDF 生成
    'reportlab',
    # Git
    'git',
    # 终端颜色
    'colorama',
    # 二维码
    'qrcode',
    'PIL',
    # 本地模块
    'plugin_v2',
    'plugin_v2.base',
    'plugin_v2.manager',
    'plugin_v2.host_api',
    'plugin_v2.events',
    'plugin_v2.capabilities',
    'plugin_v2.adapters',
    'plugin_v2.adapters.base_adapter',
    'plugin_v2.adapters.openclaw_adapter',
    'plugin_v2.adapters.xiaoli_adapter',
    'plugin_v2.adapters.node_bridge',
    'plugin_v2.converter',
    'plugin_v2.converter.ai_converter',
    # GUI 相关
    'tkinter',
    'tkinter.font',
    'tkinter.scrolledtext',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.ttk',
    # 其他可能缺失的模块
    'json',
    'uuid',
    'hashlib',
    'base64',
    'asyncio',
    'aiohttp',
    'multiprocessing',
    'queue',
    'concurrent.futures',
    'sqlite3',
    'csv',
    # 邮件相关（必需，因为 urllib 依赖）
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'email.encoders',
    'email.utils',
    'email.header',
    'email.charset',
]

# 需要一起打包的数据文件
datas = [
    ('icon', 'icon'),
    ('plugin_v2/ai_generator', 'plugin_v2/ai_generator'),
    ('skills', 'skills'),
    ('model_recommendations.json', '.'),
    ('AI人格', 'AI人格'),
]

# 二进制文件
binaries = []

# 排除不必要的模块（从 excludes 中移除 'email' 和所有标准库模块）
excludes = [
    'matplotlib',
    'scipy',
    'IPython',
    'jupyter',
    'notebook',
    'tkinter.test',
    'lib2to3',
    'pydoc',
    'setuptools',
    'pip',
    # 不要排除 'email', 'http', 'xml', 'html' 等标准库模块
]

a = Analysis(
    ['TG HELPER.py'],
    pathex=[PROJECT_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TG_HELPER',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon/TGAI.ico',
)