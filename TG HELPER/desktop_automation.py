# -*- coding: utf-8 -*-
"""
Windows 桌面程序自动化 - 基于 UI Automation (UIA)
可操控任何 Windows 桌面应用：启动 EXE、查找窗口、读取 UI 控件树、
按名称精准点击按钮、输入文字、截图窗口。

依赖：pip install uiautomation
AI 通过读取 UI 树（类似 DOM 树）来理解界面结构，无需硬编码坐标。
"""
import os
import subprocess
import time
import uiautomation as auto


def _find_control_by_name(parent, name, search_depth=8, timeout=3):
    """在控件树中递归搜索匹配名称的子控件"""
    end_time = time.time() + timeout
    while time.time() < end_time:
        ctrl = _search_recursive(parent, name, 0, search_depth)
        if ctrl:
            return ctrl
        time.sleep(0.3)
    return None


def _search_recursive(control, name, depth, max_depth):
    if depth > max_depth:
        return None
    try:
        if control.Name and name in control.Name:
            return control
    except Exception:
        pass
    try:
        for child in control.GetChildren():
            result = _search_recursive(child, name, depth + 1, max_depth)
            if result:
                return result
    except Exception:
        pass
    return None


def _get_control_texts(control, depth=0, max_depth=3):
    """递归获取控件树文本摘要（限制深度）"""
    if depth > max_depth:
        return []
    lines = []
    try:
        indent = "  " * depth
        ctype = control.ControlTypeName or "Control"
        name = control.Name or ""
        auto_id = control.AutomationId or ""
        rect = control.BoundingRectangle
        pos = f"({rect.left},{rect.top})" if rect else ""
        label = f"{indent}[{ctype}]"
        if name:
            label += f" {name}"
        if auto_id:
            label += f" #{auto_id}"
        if pos:
            label += f" {pos}"
        lines.append(label)
        for child in control.GetChildren():
            lines.extend(_get_control_texts(child, depth + 1, max_depth))
    except Exception:
        pass
    return lines


def launch_app(exe_path: str, working_dir: str = None, args: str = None) -> str:
    """启动 Windows 程序（EXE 或其快捷方式）"""
    try:
        # 如果是 .lnk 快捷方式，先解析
        actual_exe = exe_path
        if exe_path.lower().endswith('.lnk'):
            import pythoncom
            from win32com.client import Dispatch
            pythoncom.CoInitialize()
            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(exe_path)
            actual_exe = shortcut.TargetPath
            if working_dir is None:
                working_dir = os.path.dirname(actual_exe)

        cmd = [actual_exe]
        if args:
            cmd.extend(args.split())
        if working_dir is None:
            working_dir = os.path.dirname(actual_exe) if os.path.dirname(actual_exe) else None
        subprocess.Popen(cmd, cwd=working_dir, shell=False)
        return f"SUCCESS: 已启动 {os.path.basename(actual_exe)}"
    except Exception as e:
        # 回退：直接 os.startfile
        try:
            os.startfile(exe_path)
            return f"SUCCESS: 已启动 {os.path.basename(exe_path)}（通过 startfile）"
        except Exception as e2:
            return f"ERROR: 启动失败: {e2}"


def find_window(title: str = None, class_name: str = None, timeout: int = 5) -> str:
    """查找匹配标题的窗口，返回其 UI 树摘要"""
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            if title:
                win = auto.WindowControl(searchDepth=1, Name=title)
            elif class_name:
                win = auto.WindowControl(searchDepth=1, ClassName=class_name)
            else:
                return "ERROR: 请指定 title 或 class_name"
            if win.Exists(0, 0):
                tree = _get_control_texts(win, max_depth=4)
                return f"SUCCESS: 找到窗口\n--- UI 控件树 ---\n" + "\n".join(tree[:80])
        except Exception:
            pass
        time.sleep(0.5)
    return f"ERROR: 未找到窗口（title='{title}', 超时 {timeout} 秒）"


def get_ui_tree(title: str = None, max_depth: int = 3) -> str:
    """获取指定窗口（或顶层窗口）的 UI 控件树，AI 通过它理解按钮和输入框的位置"""
    try:
        if title:
            win = auto.WindowControl(searchDepth=1, Name=title)
            if not win.Exists(0, 0):
                # 尝试模糊匹配
                matches = []
                for w in auto.GetRootControl().GetChildren():
                    try:
                        if w.Name and title.lower() in w.Name.lower():
                            win = w
                            matches.append(w)
                            break
                    except Exception:
                        pass
                if not matches:
                    return f"ERROR: 未找到包含 '{title}' 的窗口"
        else:
            # 取顶层可见窗口列表
            wins = []
            for w in auto.GetRootControl().GetChildren():
                try:
                    if w.Name and w.ControlTypeName == "WindowControl":
                        wins.append(w.Name)
                except Exception:
                    pass
            if wins:
                return "当前打开的窗口:\n" + "\n".join(f"  - {n}" for n in wins[:20]) + "\n\n请指定 title 以查看某窗口的控件树"
            return "ERROR: 未找到任何顶层窗口"

        tree = _get_control_texts(win, max_depth=max_depth)
        title_text = win.Name or "(无标题)"
        return f"窗口 '{title_text}' 的 UI 控件树:\n" + "\n".join(tree[:80])
    except Exception as e:
        return f"ERROR: 获取 UI 树失败: {e}"


def _invoke_background(control):
    """纯后台点击：不移动鼠标、不抢焦点，通过 UIA InvokePattern 触发"""
    try:
        invoke = control.GetPattern(auto.PatternId.InvokePattern)
        if invoke:
            invoke.Invoke()
            return True
    except Exception:
        pass
    try:
        legacy = control.GetPattern(auto.PatternId.LegacyIAccessiblePattern)
        if legacy:
            legacy.DoDefaultAction()
            return True
    except Exception:
        pass
    try:
        control.Click(simulateMove=False)
        return True
    except Exception:
        pass
def click_button(window_title: str = None, button_text: str = None, button_id: str = None, timeout: int = 5) -> str:
    """
    精准点击桌面程序中的按钮（纯后台，不动鼠标）。
    例如：click_button(button_text="启动游戏") 会在顶层窗口中找到并点击"启动游戏"按钮。
    """
    try:
        if window_title:
            win = auto.WindowControl(searchDepth=1, Name=window_title)
            if not win.Exists(0, 0):
                for w in auto.GetRootControl().GetChildren():
                    try:
                        if w.Name and window_title.lower() in w.Name.lower():
                            win = w
                            break
                    except Exception:
                        pass
                if not win.Exists(0, 0):
                    return f"ERROR: 未找到窗口 '{window_title}'"
        else:
            win = auto.GetRootControl()

        if button_id:
            ctrl = win.ButtonControl(AutomationId=button_id)
            if ctrl.Exists(0, 0):
                _invoke_background(ctrl)
                return f"SUCCESS: 已点击按钮 #{button_id}"
            ctrl = _find_control_by_name(win, button_id, search_depth=8, timeout=timeout)

        if button_text:
            ctrl = win.ButtonControl(searchDepth=16, Name=button_text)
            if ctrl.Exists(0, 0):
                _invoke_background(ctrl)
                return f"SUCCESS: 已点击按钮 '{button_text}'"
            ctrl = _find_control_by_name(win, button_text, search_depth=8, timeout=timeout)

        if ctrl is None:
            search_for = button_text or button_id
            return f"ERROR: 未找到控件 '{search_for}'。请先用 app_get_ui_tree 查看窗口控件列表。"

        if _invoke_background(ctrl):
            return f"SUCCESS: 已点击控件 '{button_text or button_id}'"
        return f"ERROR: 控件 '{button_text or button_id}' 不支持后台点击，请手动操作"
    except Exception as e:
        return f"ERROR: 点击失败: {e}"


def type_into_app(text: str, window_title: str = None, field_name: str = None) -> str:
    """
    在指定输入框中输入文字（纯后台，不动鼠标键盘）。
    优先使用 UIA ValuePattern.SetValue；不支持则回退到剪贴板粘贴。
    """
    try:
        if window_title:
            win = auto.WindowControl(searchDepth=1, Name=window_title)
            if not win.Exists(0, 0):
                for w in auto.GetRootControl().GetChildren():
                    try:
                        if w.Name and window_title.lower() in w.Name.lower():
                            win = w
                            break
                    except Exception:
                        pass

        ctrl = None
        if field_name and window_title:
            ctrl = _find_control_by_name(win, field_name, search_depth=6, timeout=3)
            if ctrl is None:
                return f"ERROR: 未找到输入框 '{field_name}'"

        # 优先用 ValuePattern 直接设值（后台，不抢焦点）
        if ctrl:
            try:
                val = ctrl.GetPattern(auto.PatternId.ValuePattern)
                if val:
                    val.SetValue(text)
                    return f"SUCCESS: 已输入文字（ValuePattern）"
            except Exception:
                pass

        # 回退：设剪贴板 + 通知用户手动粘贴
        if ctrl:
            try:
                ctrl.SetFocus()
                time.sleep(0.1)
                auto.SendKeys(text, interval=0.02)
                return f"SUCCESS: 已输入文字"
            except Exception:
                pass

        # 彻底回退：设剪贴板
        _set_clipboard_silent(text)
        return f"INFO: 已将文字复制到剪贴板，请手动 Ctrl+V 粘贴，或先用 app_click_button 点进输入框再调用 app_type_text"
    except Exception as e:
        return f"ERROR: 输入失败: {e}"


def _set_clipboard_silent(text: str):
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.clipboard().setText(text)
            return
    except Exception:
        pass
    try:
        import pyperclip
        pyperclip.copy(text)
    except ImportError:
        pass


def set_clipboard(text: str) -> str:
    """设置剪贴板内容"""
    _set_clipboard_silent(text)
    return "SUCCESS: 已设置剪贴板"


def press_keys(keys: str) -> str:
    """发送键盘快捷键（UIA 方式，不通过 pyautogui）"""
    try:
        auto.SendKeys("{" + keys.replace("+", "}{") + "}" if "+" in keys else "{" + keys + "}", interval=0.01)
        return f"SUCCESS: 已发送快捷键 {keys}"
    except Exception as e:
        return f"ERROR: 快捷键失败: {e}"


def app_screenshot(window_title: str = None, save_path: str = None) -> str:
    """截取指定窗口或全屏（不抢焦点，不移动鼠标）"""
    os.makedirs("./screenshots", exist_ok=True)
    if save_path is None:
        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"./screenshots/app_{ts}.png"

    if window_title:
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32

            hwnd = user32.FindWindowW(None, window_title)
            if not hwnd:
                # 模糊匹配
                def _enum_callback(h, lParam):
                    name_buf = ctypes.create_unicode_buffer(256)
                    user32.GetWindowTextW(h, name_buf, 256)
                    if window_title.lower() in name_buf.value.lower():
                        lParam[0] = h
                        return False
                    return True
                result = [0]
                user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.py_object)(_enum_callback), result)
                hwnd = result[0] if result[0] else None

            if hwnd:
                # 后台截取（不 SetForegroundWindow）
                rect = wintypes.RECT()
                ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if w > 0 and h > 0:
                    hdc_screen = user32.GetDC(None)
                    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
                    bmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
                    gdi32.SelectObject(hdc_mem, bmp)
                    # PrintWindow 支持后台窗口截图
                    ctypes.windll.user32.PrintWindow(hwnd, hdc_mem, 2)
                    import struct, array
                    bmpinfo = struct.pack('IiiHHIIiiII', 44, w, h, 1, 32, 0, w * h * 4, 0, 0, 0, 0)
                    buf = (ctypes.c_char * (w * h * 4))()
                    gdi32.GetDIBits(hdc_mem, bmp, 0, h, buf, bmpinfo, 0)
                    gdi32.DeleteDC(hdc_mem)
                    gdi32.DeleteObject(bmp)
                    user32.ReleaseDC(None, hdc_screen)
                    from PIL import Image
                    img = Image.frombuffer('RGBA', (w, h), bytes(buf[:]), 'raw', 'BGRA', 0, 1)
                    img = img.convert('RGB')
                    img.save(save_path)
                    return f"SUCCESS: 窗口截图已保存: {save_path}"

        except Exception as e:
            print(f"[app_screenshot] 窗口截图失败: {e}")

    # 回退：pyautogui 全屏（不动鼠标，只截图）
    import pyautogui
    pyautogui.screenshot(save_path)
    return f"SUCCESS: 全屏截图已保存: {save_path}"
