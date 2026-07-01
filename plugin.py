#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
界 (Jie) v2.0.1 — AI 浏览器
让 AI 像人一样「看」界面、「操作」界面、「理解」界面
跨平台桌面自动化中枢 (Windows + Linux+macOS)
"""

import base64
import io
import json
import logging
import os
import platform
import subprocess
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("qwenpaw.界")

# ── 平台检测 ───────────────────────────────────────────
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

logger.info(f"🖥️ 检测到平台: {platform.system()}")

# ── 平台特定导入 ───────────────────────────────────────
if IS_WINDOWS:
    try:
        import ctypes
        import ctypes.wintypes
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        HAS_CTYPES = True
    except Exception as e:
        logger.warning(f"Windows ctypes 导入失败: {e}")
        HAS_CTYPES = False
        
    try:
        import win32gui
        import win32con
        import win32api
        import win32clipboard as clip
        import win32ui
        HAS_PYWIN32 = True
    except ImportError:
        HAS_PYWIN32 = False
        logger.warning("pywin32 未安装，部分功能受限")
else:
    HAS_CTYPES = False
    HAS_PYWIN32 = False

# Linux 工具检测
if IS_LINUX:
    def _check_linux_tool(tool: str) -> bool:
        """检查 Linux 工具是否可用"""
        try:
            subprocess.run(['which', tool], capture_output=True, check=True)
            return True
        except:
            return False
    
    HAS_XDOTOOL = _check_linux_tool('xdotool')
    HAS_SCROT = _check_linux_tool('scrot')
    HAS_GNOME_SCREENSHOT = _check_linux_tool('gnome-screenshot')
    HAS_XCLIP = _check_linux_tool('xclip')
    
    logger.info(f"Linux 工具检测: xdotool={HAS_XDOTOOL}, scrot={HAS_SCROT}, gnome-screenshot={HAS_GNOME_SCREENSHOT}, xclip={HAS_XCLIP}")

# ── macOS CoreGraphics 设置 ─────────────────────────────
if IS_MAC:
    import ctypes.util
    import Quartz
    
    _cg = ctypes.cdll.LoadLibrary(ctypes.util.find_library('CoreGraphics') or '/System/Library/Frameworks/ApplicationServices.framework/Frameworks/CoreGraphics.framework/CoreGraphics')
    _kcore = ctypes.cdll.LoadLibrary(ctypes.util.find_library('CoreFoundation') or '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
    
    # CGEventType
    _kCGEventLeftMouseDown   = 1
    _kCGEventLeftMouseUp     = 2
    _kCGEventRightMouseDown  = 3
    _kCGEventRightMouseUp    = 4
    _kCGEventOtherMouseDown  = 25
    _kCGEventOtherMouseUp    = 26
    _kCGEventMouseMoved      = 5
    _kCGEventScrollWheel     = 22
    _kCGEventKeyDown         = 10
    _kCGEventKeyUp           = 11
    _kCGEventFlagMaskShift   = 0x020000
    _kCGEventFlagMaskControl = 0x040000
    _kCGEventFlagMaskAlternate = 0x080000
    _kCGEventFlagMaskCommand = 0x100000
    _kCGHIDEventTap = 0
    
    # CGMouseButton
    _kCGMouseButtonLeft   = 0
    _kCGMouseButtonRight  = 1
    _kCGMouseButtonCenter = 2
    
    # CGScrollEventUnit
    _kCGScrollEventUnitPixel = 0
    _kCGScrollEventUnitLine  = 1
    
    # --- CGSPoint / CGPoint ---
    class _CGS(ctypes.Structure):
        _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]
    
    # --- CGEvent ref type ---
    class _CGE(ctypes.Structure): pass
    _CGEventRef = ctypes.POINTER(_CGE)
    
    # --- CG function signatures ---
    _cg.CGDisplayPixelsWide.argtypes = [ctypes.c_uint32]
    _cg.CGDisplayPixelsWide.restype = ctypes.c_size_t
    _cg.CGDisplayPixelsHigh.argtypes = [ctypes.c_uint32]
    _cg.CGDisplayPixelsHigh.restype = ctypes.c_size_t
    _cg.CGMainDisplayID.argtypes = []
    _cg.CGMainDisplayID.restype = ctypes.c_uint32
    _cg.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, _CGS, ctypes.c_uint32]
    _cg.CGEventCreateMouseEvent.restype = _CGEventRef
    _cg.CGEventPost.argtypes = [ctypes.c_uint32, _CGEventRef]
    _cg.CGEventPost.restype = None
    _cg.CGEventCreateKeyboardEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool]
    _cg.CGEventCreateKeyboardEvent.restype = _CGEventRef
    _cg.CGEventSetFlags.argtypes = [_CGEventRef, ctypes.c_uint64]
    _cg.CGEventSetFlags.restype = None
    _cg.CGEventCreateScrollWheelEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32]
    _cg.CGEventCreateScrollWheelEvent.restype = _CGEventRef
    _cg.CGEventSetIntegerValueField.argtypes = [_CGEventRef, ctypes.c_int32, ctypes.c_int64]
    _cg.CGEventSetIntegerValueField.restype = None
    _cg.CGEventGetLocation.argtypes = [_CGEventRef]
    _cg.CGEventGetLocation.restype = _CGS
    _cg.CGEventCreate.argtypes = [ctypes.c_void_p]
    _cg.CGEventCreate.restype = _CGEventRef
    _cg.CFRelease.argtypes = [ctypes.c_void_p]
    _cg.CFRelease.restype = None
    
    # --- macOS 工具检测 ---
    def _check_mac_tool(tool):
        try:
            subprocess.run(['which', tool], capture_output=True, check=True)
            return True
        except:
            return False
    
    HAS_CLICLICK = _check_mac_tool('cliclick')
    
    logger.info(f"macOS 工具检测: CoreGraphics=✅, cliclick={HAS_CLICLICK}")
    
    # --- macOS 辅助函数 ---
    _MAC_KEY_CODES = {
        'return': 0x24, 'enter': 0x24, 'tab': 0x30, 'space': 0x31,
        'delete': 0x33, 'escape': 0x35, 'esc': 0x35,
        'command': 0x37, 'cmd': 0x37,
        'shift': 0x38, 'capslock': 0x39, 'option': 0x3A, 'alt': 0x3A,
        'control': 0x3B, 'ctrl': 0x3B,
        'rightshift': 0x3C, 'rightoption': 0x3D, 'rightcontrol': 0x3E,
        'left': 0x7B, 'right': 0x7C, 'down': 0x7D, 'up': 0x7E,
        'f1': 0x7A, 'f2': 0x78, 'f3': 0x63, 'f4': 0x76, 'f5': 0x60,
        'f6': 0x61, 'f7': 0x62, 'f8': 0x64, 'f9': 0x65, 'f10': 0x6D,
        'f11': 0x67, 'f12': 0x6F,
        'a': 0x00, 'b': 0x0B, 'c': 0x08, 'd': 0x02, 'e': 0x0E,
        'f': 0x03, 'g': 0x05, 'h': 0x04, 'i': 0x22, 'j': 0x26,
        'k': 0x28, 'l': 0x25, 'm': 0x2E, 'n': 0x2D, 'o': 0x1F,
        'p': 0x23, 'q': 0x0C, 'r': 0x0F, 's': 0x01, 't': 0x11,
        'u': 0x20, 'v': 0x09, 'w': 0x0D, 'x': 0x07, 'y': 0x10, 'z': 0x06,
        '0': 0x1D, '1': 0x12, '2': 0x13, '3': 0x14, '4': 0x15,
        '5': 0x17, '6': 0x16, '7': 0x1A, '8': 0x1C, '9': 0x19,
    }
    
    _MAC_MOD_FLAGS = {
        'shift': _kCGEventFlagMaskShift,
        'ctrl': _kCGEventFlagMaskControl,
        'control': _kCGEventFlagMaskControl,
        'alt': _kCGEventFlagMaskAlternate,
        'option': _kCGEventFlagMaskAlternate,
        'cmd': _kCGEventFlagMaskCommand,
        'command': _kCGEventFlagMaskCommand,
    }
    
    def _mac_mouse_event(evt_type, x, y, button):
        """macOS 鼠标事件底层"""
        pt = _CGS(float(x), float(y))
        evt = _cg.CGEventCreateMouseEvent(None, evt_type, pt, button)
        _cg.CGEventPost(_kCGHIDEventTap, evt)
        _cg.CFRelease(evt)
    
    def _mac_key_event(keycode, flags, down):
        """macOS 键盘事件底层"""
        evt = _cg.CGEventCreateKeyboardEvent(None, keycode, down)
        if flags:
            _cg.CGEventSetFlags(evt, flags)
        _cg.CGEventPost(_kCGHIDEventTap, evt)
        _cg.CFRelease(evt)

try:
    from PIL import Image, ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("Pillow 未安装，截图功能受限")

# ── 常量 ──────────────────────────────────────────────
if IS_WINDOWS:
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_WHEEL = 0x0800
    KEYEVENTF_KEYDOWN = 0x0000
    KEYEVENTF_KEYUP = 0x0002

# ── 动态路径检测 ──────────────────────────────────────
def _get_qwenpaw_home() -> Path:
    """自动检测QwenPaw主目录 - 支持多种安装方式"""
    if "QWENPAW_HOME" in os.environ:
        path = Path(os.environ["QWENPAW_HOME"])
        if path.exists():
            return path
    
    try:
        current_file = Path(__file__).resolve()
        qwenpaw_home = current_file.parent.parent.parent
        if (qwenpaw_home / "plugins").exists():
            return qwenpaw_home
    except Exception:
        pass
    
    user_home = Path.home()
    for name in [".copaw", ".qwenpaw", "qwenpaw"]:
        possible_path = user_home / name
        if possible_path.exists():
            return possible_path
    
    return user_home / ".qwenpaw"

QWENPAW_HOME = _get_qwenpaw_home()
PLUGINS_DIR = QWENPAW_HOME / "plugins"

# ── Pydantic 模型 ─────────────────────────────────────
class ClickRequest(BaseModel):
    x: int
    y: int
    button: str = "left"
    clicks: int = 1

class TypeRequest(BaseModel):
    text: str
    clear: bool = False
    press_enter: bool = False
    x: Optional[int] = None
    y: Optional[int] = None

class ScrollRequest(BaseModel):
    x: int
    y: int
    direction: str = "down"
    wheel_times: int = 1

class MoveRequest(BaseModel):
    x: int
    y: int

class ShortcutRequest(BaseModel):
    keys: str

class AppRequest(BaseModel):
    name: str

class ExecuteRequest(BaseModel):
    steps: List[Dict[str, Any]]

class ScheduleRequest(BaseModel):
    action: str
    interval: int
    count: int = -1
    params: Optional[Dict[str, Any]] = None

class OCRRequest(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    lang: str = "chi_sim+eng"

class SmartActionRequest(BaseModel):
    condition: str
    action_if_true: Optional[Dict[str, Any]] = None
    action_if_false: Optional[Dict[str, Any]] = None
    check_interval: float = 1.0
    timeout: float = 30.0

class RecordStartRequest(BaseModel):
    name: str

class PlaybackRequest(BaseModel):
    name: str
    speed: float = 1.0

# ── 跨平台实现 ──────────────────────────────────────────

def _get_screen_size() -> tuple:
    """获取屏幕尺寸 - 跨平台"""
    if IS_WINDOWS and HAS_CTYPES:
        return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
    elif IS_MAC:
        try:
            did = _cg.CGMainDisplayID()
            return (_cg.CGDisplayPixelsWide(did), _cg.CGDisplayPixelsHigh(did))
        except:
            pass
    elif IS_LINUX:
        try:
            # 使用 xdpyinfo 或 xrandr
            result = subprocess.run(['xdpyinfo'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'dimensions:' in line:
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and part[0].isdigit():
                            w, h = part.split('x')
                            return (int(w), int(h))
        except:
            pass
    return (1920, 1080)  # 默认

def _capture_screenshot() -> Dict[str, Any]:
    """截图 - 跨平台"""
    try:
        if IS_WINDOWS:
            if HAS_PIL:
                img = ImageGrab.grab()
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                return {"success": True, "image": img_str, "width": img.width, "height": img.height}
            else:
                return {"success": False, "error": "Pillow 未安装"}
        elif IS_LINUX:
            # Linux 截图
            timestamp = int(time.time())
            screenshot_path = f"/tmp/jie_screenshot_{timestamp}.png"
            
            if HAS_SCROT:
                subprocess.run(['scrot', screenshot_path], check=True)
            elif HAS_GNOME_SCREENSHOT:
                subprocess.run(['gnome-screenshot', '-f', screenshot_path], check=True)
            else:
                return {"success": False, "error": "未找到截图工具 (请安装 scrot 或 gnome-screenshot)"}
            
            with open(screenshot_path, 'rb') as f:
                img_str = base64.b64encode(f.read()).decode()
            
            img = Image.open(screenshot_path)
            os.remove(screenshot_path)
            
            return {"success": True, "image": img_str, "width": img.width, "height": img.height}
        elif IS_MAC:
            # macOS: screencapture 命令
            ts = int(time.time())
            path = f"/tmp/jie_screenshot_{ts}.png"
            subprocess.run(['screencapture', '-x', path], check=True)
            with open(path, 'rb') as f:
                img_data = f.read()
            os.remove(path)
            img = Image.open(io.BytesIO(img_data))
            return {"success": True, "image": base64.b64encode(img_data).decode(), "width": img.width, "height": img.height}
        else:
            return {"success": False, "error": f"不支持的平台: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _click(x: int, y: int, button: str = "left", clicks: int = 1) -> Dict[str, Any]:
    """点击 - 跨平台"""
    try:
        if IS_WINDOWS:
            if HAS_PYWIN32:
                win32api.SetCursorPos((x, y))
                button_code = win32con.MOUSEEVENTF_LEFTDOWN if button == "left" else \
                             win32con.MOUSEEVENTF_RIGHTDOWN if button == "right" else \
                             win32con.MOUSEEVENTF_MIDDLEDOWN
                button_up = win32con.MOUSEEVENTF_LEFTUP if button == "left" else \
                           win32con.MOUSEEVENTF_RIGHTUP if button == "right" else \
                           win32con.MOUSEEVENTF_MIDDLEUP
                
                for _ in range(clicks):
                    win32api.mouse_event(button_code, 0, 0, 0, 0)
                    win32api.mouse_event(button_up, 0, 0, 0, 0)
                return {"success": True, "x": x, "y": y, "button": button, "clicks": clicks}
            else:
                return {"success": False, "error": "pywin32 未安装"}
        elif IS_LINUX:
            if HAS_XDOTOOL:
                button_num = "1" if button == "left" else "3" if button == "right" else "2"
                for _ in range(clicks):
                    subprocess.run(['xdotool', 'mousemove', str(x), str(y)], check=True)
                    subprocess.run(['xdotool', 'click', button_num], check=True)
                return {"success": True, "x": x, "y": y, "button": button, "clicks": clicks}
            else:
                return {"success": False, "error": "xdotool 未安装 (sudo apt install xdotool)"}
        elif IS_MAC:
            # macOS: CoreGraphics 鼠标事件
            btn_map = {"left": _kCGMouseButtonLeft, "right": _kCGMouseButtonRight, "middle": _kCGMouseButtonCenter}
            cg_btn = btn_map.get(button, _kCGMouseButtonLeft)
            down_evt = _kCGEventLeftMouseDown if button == "left" else _kCGEventRightMouseDown if button == "right" else _kCGEventOtherMouseDown
            up_evt = _kCGEventLeftMouseUp if button == "left" else _kCGEventRightMouseUp if button == "right" else _kCGEventOtherMouseUp
            for _ in range(clicks):
                _mac_mouse_event(down_evt, x, y, cg_btn)
                _mac_mouse_event(up_evt, x, y, cg_btn)
            return {"success": True, "x": x, "y": y, "button": button, "clicks": clicks}
        else:
            return {"success": False, "error": f"不支持的平台: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _type_text(text: str) -> Dict[str, Any]:
    """输入文字 - 跨平台"""
    try:
        if IS_WINDOWS:
            if HAS_PYWIN32:
                # 用 win32clipboard 替代 pyperclip （零额外依赖）
                clip.OpenClipboard()
                clip.EmptyClipboard()
                clip.SetClipboardText(text)
                clip.CloseClipboard()
                win32api.keybd_event(0x11, 0, 0, 0)  # Ctrl
                win32api.keybd_event(0x56, 0, 0, 0)  # V
                win32api.keybd_event(0x56, 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
                return {"success": True, "text_length": len(text)}
            else:
                return {"success": False, "error": "pywin32 未安装"}
        elif IS_LINUX:
            if HAS_XDOTOOL and HAS_XCLIP:
                # 使用 xclip 复制到剪贴板
                proc = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
                proc.communicate(text.encode())
                subprocess.run(['xdotool', 'key', 'ctrl+v'], check=True)
                return {"success": True, "text_length": len(text)}
            else:
                # 直接输入
                subprocess.run(['xdotool', 'type', text], check=True)
                return {"success": True, "text_length": len(text)}
        elif IS_MAC:
            # macOS: pbcopy + Cmd+V
            proc = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            proc.communicate(text.encode('utf-8'))
            time.sleep(0.05)
            # 模拟 Cmd+V
            _mac_key_event(0x09, _kCGEventFlagMaskCommand, True)   # V down
            time.sleep(0.02)
            _mac_key_event(0x09, _kCGEventFlagMaskCommand, False)  # V up
            return {"success": True, "text_length": len(text)}
        else:
            return {"success": False, "error": f"不支持的平台: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _shortcut(keys: str) -> Dict[str, Any]:
    """快捷键 - 跨平台"""
    try:
        key_map = {
            'ctrl': 'Control',
            'alt': 'Alt',
            'shift': 'Shift',
            'enter': 'Return',
            'esc': 'Escape',
            'tab': 'Tab',
            'space': 'space',
        }
        
        if IS_WINDOWS and HAS_PYWIN32:
            # Windows 快捷键实现 — 真实按键
            _WIN_VK = {
                'ctrl': 0x11, 'control': 0x11,
                'alt': 0x12, 'menu': 0x12,
                'shift': 0x10,
                'win': 0x5B, 'lwin': 0x5B, 'rwin': 0x5C,
                'tab': 0x09, 'enter': 0x0D, 'return': 0x0D,
                'esc': 0x1B, 'escape': 0x1B,
                'space': 0x20, 'back': 0x08, 'backspace': 0x08,
                'delete': 0x2E, 'del': 0x2E, 'insert': 0x2D, 'ins': 0x2D,
                'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
                'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
                'caps': 0x14, 'capslock': 0x14, 'numlock': 0x90,
                'printscreen': 0x2C, 'prtsc': 0x2C, 'pause': 0x13,
                'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
                'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
                'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
                'plus': 0xBB, 'equal': 0xBB, 'minus': 0xBD,
                'comma': 0xBC, 'period': 0xBE, 'dot': 0xBE,
            }
            parts = keys.lower().split('+')
            mod_keys = [p for p in parts if p in ('ctrl','control','alt','menu','shift','win','lwin')]
            normal_keys = [p for p in parts if p not in ('ctrl','control','alt','menu','shift','win','lwin')]
            # 按下修饰键
            for mk in mod_keys:
                vk = _WIN_VK.get(mk, 0)
                if vk:
                    win32api.keybd_event(vk, 0, 0, 0)
            time.sleep(0.03)
            # 按下并释放普通键
            for nk in normal_keys:
                if nk in _WIN_VK:
                    vk = _WIN_VK[nk]
                elif len(nk) == 1 and 'a' <= nk <= 'z':
                    vk = 0x41 + (ord(nk) - ord('a'))
                elif len(nk) == 1 and '0' <= nk <= '9':
                    vk = 0x30 + int(nk)
                else:
                    continue
                win32api.keybd_event(vk, 0, 0, 0)
                time.sleep(0.02)
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.03)
            # 释放修饰键（逆序）
            for mk in reversed(mod_keys):
                vk = _WIN_VK.get(mk, 0)
                if vk:
                    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
            return {"success": True, "keys": keys}
        elif IS_LINUX and HAS_XDOTOOL:
            # Linux 快捷键
            xdo_keys = []
            for part in keys.lower().split('+'):
                xdo_keys.append(key_map.get(part, part))
            subprocess.run(['xdotool', 'key', '+'.join(xdo_keys)], check=True)
            return {"success": True, "keys": keys}
        elif IS_MAC:
            # macOS: CoreGraphics 快捷键
            parts = keys.lower().split('+')
            mods = [p for p in parts if p in _MAC_MOD_FLAGS]
            non_mods = [p for p in parts if p not in _MAC_MOD_FLAGS]
            flags = 0
            for m in mods:
                flags |= _MAC_MOD_FLAGS[m]
            # 按下修饰键
            for m in mods:
                kc = _MAC_KEY_CODES.get(m, 0)
                _mac_key_event(kc, flags, True)
            time.sleep(0.02)
            # 按下并释放目标键
            for k in non_mods:
                kc = _MAC_KEY_CODES.get(k, 0)
                _mac_key_event(kc, flags, True)
                time.sleep(0.02)
                _mac_key_event(kc, flags, False)
            time.sleep(0.02)
            # 释放修饰键
            for m in mods:
                kc = _MAC_KEY_CODES.get(m, 0)
                _mac_key_event(kc, flags, False)
            return {"success": True, "keys": keys}
        else:
            return {"success": False, "error": f"不支持的平台或工具: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _scroll(x: int, y: int, direction: str, wheel_times: int) -> Dict[str, Any]:
    """滚动 - 跨平台"""
    try:
        if IS_WINDOWS and HAS_PYWIN32:
            win32api.SetCursorPos((x, y))
            delta = 120 * wheel_times if direction == "down" else -120 * wheel_times
            win32api.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, delta, 0)
            return {"success": True, "x": x, "y": y, "direction": direction, "wheel_times": wheel_times}
        elif IS_LINUX and HAS_XDOTOOL:
            subprocess.run(['xdotool', 'mousemove', str(x), str(y)], check=True)
            button = "4" if direction == "up" else "5"
            for _ in range(wheel_times):
                subprocess.run(['xdotool', 'click', button], check=True)
            return {"success": True, "x": x, "y": y, "direction": direction, "wheel_times": wheel_times}
        elif IS_MAC:
            # macOS: CoreGraphics 滚轮事件
            delta = -3 * wheel_times if direction == "down" else 3 * wheel_times
            evt = _cg.CGEventCreateScrollWheelEvent(None, _kCGScrollEventUnitPixel, 1, delta, 0)
            _cg.CGEventPost(_kCGHIDEventTap, evt)
            _cg.CFRelease(evt)
            return {"success": True, "x": x, "y": y, "direction": direction, "wheel_times": wheel_times}
        else:
            return {"success": False, "error": f"不支持的平台: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _move_mouse(x: int, y: int) -> Dict[str, Any]:
    """移动鼠标 - 跨平台"""
    try:
        if IS_WINDOWS and HAS_PYWIN32:
            win32api.SetCursorPos((x, y))
            return {"success": True, "x": x, "y": y}
        elif IS_LINUX and HAS_XDOTOOL:
            subprocess.run(['xdotool', 'mousemove', str(x), str(y)], check=True)
            return {"success": True, "x": x, "y": y}
        elif IS_MAC:
            # macOS: CoreGraphics 鼠标移动
            pt = _CGS(float(x), float(y))
            evt = _cg.CGEventCreateMouseEvent(None, _kCGEventMouseMoved, pt, 0)
            _cg.CGEventPost(_kCGHIDEventTap, evt)
            _cg.CFRelease(evt)
            return {"success": True, "x": x, "y": y}
        else:
            return {"success": False, "error": f"不支持的平台: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _get_cursor_pos() -> Dict[str, Any]:
    """获取鼠标位置 - 跨平台"""
    try:
        if IS_WINDOWS and HAS_CTYPES:
            pt = ctypes.wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            return {"success": True, "x": pt.x, "y": pt.y}
        elif IS_LINUX and HAS_XDOTOOL:
            result = subprocess.run(['xdotool', 'getmouselocation'], capture_output=True, text=True)
            parts = result.stdout.strip().split()
            x = int(parts[0].split(':')[1])
            y = int(parts[1].split(':')[1])
            return {"success": True, "x": x, "y": y}
        elif IS_MAC:
            # macOS: CoreGraphics 获取鼠标位置
            evt = _cg.CGEventCreate(None)
            loc = _cg.CGEventGetLocation(evt)
            _cg.CFRelease(evt)
            return {"success": True, "x": int(loc.x), "y": int(loc.y)}
        else:
            return {"success": False, "error": f"不支持的平台: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _launch_app(name: str) -> Dict[str, Any]:
    """启动应用 - 跨平台"""
    try:
        if IS_WINDOWS:
            app_map = {
                "notepad": "notepad.exe",
                "calc": "calc.exe",
                "explorer": "explorer.exe",
            }
            # 浏览器常见安装路径
            _KNOWN_PATHS = [
                (r"C:\Program Files\Google\Chrome\Application\chrome.exe", "chrome.exe"),
                (r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", "chrome.exe"),
                (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "msedge.exe"),
                (r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", "msedge.exe"),
                (r"C:\Program Files\Mozilla Firefox\firefox.exe", "firefox.exe"),
                (r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe", "firefox.exe"),
            ]
            app_path = app_map.get(name, name)
            # 检查是否是已知浏览器但不在 PATH 中
            if name in ("chrome", "msedge", "firefox"):
                import os as _os
                for full_path, exe_name in _KNOWN_PATHS:
                    if exe_name.lower().startswith(name) and _os.path.exists(full_path):
                        app_path = full_path
                        break
            subprocess.Popen(app_path, shell=True)
            return {"success": True, "action": "launch", "name": name}
        elif IS_LINUX:
            app_map = {
                "notepad": "gedit",
                "calc": "gnome-calculator",
                "firefox": "firefox",
                "chrome": "google-chrome",
            }
            app_path = app_map.get(name, name)
            subprocess.Popen([app_path])
            return {"success": True, "action": "launch", "name": name}
        elif IS_MAC:
            # macOS: open 命令
            app_map = {
                "notepad": "TextEdit",
                "calc": "Calculator",
                "explorer": "Finder",
                "chrome": "Google Chrome",
                "firefox": "Firefox",
                "safari": "Safari",
                "terminal": "Terminal",
            }
            app_name = app_map.get(name.lower(), name)
            subprocess.Popen(['open', '-a', app_name])
            return {"success": True, "action": "launch", "name": name}
        else:
            return {"success": False, "error": f"不支持的平台: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _get_window_info() -> List[Dict[str, Any]]:
    """获取窗口信息 - 跨平台"""
    try:
        if IS_WINDOWS and HAS_PYWIN32:
            windows = []
            def callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        rect = win32gui.GetWindowRect(hwnd)
                        windows.append({
                            "hwnd": hwnd,
                            "title": title,
                            "x": rect[0],
                            "y": rect[1],
                            "width": rect[2] - rect[0],
                            "height": rect[3] - rect[1]
                        })
            win32gui.EnumWindows(callback, None)
            return windows
        elif IS_LINUX:
            # Linux 窗口列表简化实现
            return [{"title": "Linux 窗口列表", "note": "请安装 wmctrl 获取完整支持"}]
        elif IS_MAC:
            # macOS: osascript (AppleScript) 获取窗口列表
            script = '''
            tell application "System Events"
                set windowList to {}
                set procs to (every process whose visible is true)
                repeat with proc in procs
                    set procName to name of proc
                    try
                        set wins to (every window of proc)
                        repeat with w in wins
                            set winName to name of w
                            set winPos to position of w
                            set winSize to size of w
                            set end of windowList to procName & " | " & winName & " | " & (item 1 of winPos as text) & "," & (item 2 of winPos as text) & " | " & (item 1 of winSize as text) & "x" & (item 2 of winSize as text)
                        end repeat
                    end try
                end repeat
                return windowList
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
            windows = []
            for line in result.stdout.strip().split(', '):
                parts = line.split(' | ')
                if len(parts) >= 4:
                    pos_parts = parts[2].split(',')
                    size_parts = parts[3].split('x')
                    try:
                        windows.append({
                            "title": parts[1],
                            "app": parts[0],
                            "x": int(pos_parts[0]),
                            "y": int(pos_parts[1]),
                            "width": int(size_parts[0]),
                            "height": int(size_parts[1])
                        })
                    except (ValueError, IndexError):
                        pass
            return windows
        else:
            return []
    except Exception as e:
        logger.error(f"获取窗口信息失败: {e}")
        return []

def _activate_window(title: str) -> Dict[str, Any]:
    """激活窗口（按标题匹配）- 跨平台"""
    try:
        if IS_WINDOWS and HAS_PYWIN32:
            hwnd = win32gui.FindWindow(None, title)
            if hwnd:
                win32gui.SetForegroundWindow(hwnd)
                return {"success": True, "title": title}
            # 模糊匹配
            def callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    wtitle = win32gui.GetWindowText(hwnd)
                    if title.lower() in wtitle.lower():
                        win32gui.SetForegroundWindow(hwnd)
                        return False
                return True
            win32gui.EnumWindows(callback, None)
            return {"success": True, "title": title, "note": "模糊匹配"}
        elif IS_MAC:
            # macOS: osascript 激活窗口
            script = f'''
            tell application "System Events"
                set procs to (every process whose visible is true)
                repeat with proc in procs
                    try
                        set wins to (every window of proc)
                        repeat with w in wins
                            if name of w contains "{title}" then
                                set frontmost of proc to true
                                return "found"
                            end if
                        end repeat
                    end try
                end repeat
            end tell
            return "not found"
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
            if "found" in result.stdout:
                return {"success": True, "title": title}
            return {"success": False, "error": f"未找到窗口: {title}"}
        elif IS_LINUX and HAS_XDOTOOL:
            subprocess.run(['xdotool', 'search', '--name', title, 'windowactivate'], check=True)
            return {"success": True, "title": title}
        else:
            return {"success": False, "error": f"不支持的平台: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── 录制回放功能 ──────────────────────────────────────
import threading

_current_recording = None
_recorded_actions = []
_record_lock = threading.Lock()

def _record_action(action: Dict[str, Any]):
    """记录操作"""
    global _current_recording, _recorded_actions
    with _record_lock:
        if _current_recording:
            action["timestamp"] = time.time()
            _recorded_actions.append(action)

# ── FastAPI 路由 ───────────────────────────────────────
router = APIRouter()

@router.get("/stats")
async def get_stats():
    """获取系统状态 - 跨平台"""
    screen_w, screen_h = _get_screen_size()
    cursor = _get_cursor_pos()
    
    # 获取插件和工具数量（从QwenPaw API）
    plugins_count = 0
    tools_count = 0
    try:
        import os
        plugins_dir = _get_qwenpaw_home() / "plugins"
        if plugins_dir.exists():
            plugins_count = len([d for d in plugins_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])
    except:
        pass
    
    return {
        "status": "ok",
        "version": "2.0.1",
        "platform": platform.system(),
        "plugins_count": plugins_count,
        "tools_count": tools_count,
        "screen": {"width": screen_w, "height": screen_h},
        "cursor": cursor,
        "has_pil": HAS_PIL,
        "has_windows_api": HAS_PYWIN32 if IS_WINDOWS else False,
        "has_linux_tools": {
            "xdotool": HAS_XDOTOOL if IS_LINUX else False,
            "scrot": HAS_SCROT if IS_LINUX else False,
        } if IS_LINUX else None,
        "has_mac_tools": {
            "coregraphics": True if IS_MAC else False,
            "cliclick": HAS_CLICLICK if IS_MAC else False,
            "screencapture": True if IS_MAC else False,
        } if IS_MAC else None,
    }

@router.post("/click")
async def post_click(req: ClickRequest):
    """点击"""
    return _click(req.x, req.y, req.button, req.clicks)

@router.post("/type")
async def post_type(req: TypeRequest):
    """输入文字"""
    if req.x is not None and req.y is not None:
        _click(req.x, req.y)
        time.sleep(0.1)
    return _type_text(req.text)

@router.post("/scroll")
async def post_scroll(req: ScrollRequest):
    """滚动"""
    return _scroll(req.x, req.y, req.direction, req.wheel_times)

@router.post("/move")
async def post_move(req: MoveRequest):
    """移动鼠标"""
    return _move_mouse(req.x, req.y)

@router.post("/shortcut")
async def post_shortcut(req: ShortcutRequest):
    """快捷键"""
    return _shortcut(req.keys)

@router.post("/app")
async def post_app(req: AppRequest):
    """启动应用"""
    return _launch_app(req.name)

@router.get("/snapshot")
async def get_snapshot():
    """截图"""
    return _capture_screenshot()

@router.get("/windows")
async def get_windows():
    """获取窗口列表"""
    windows = _get_window_info()
    return {"success": True, "count": len(windows), "windows": windows[:20]}

@router.post("/activate")
async def post_activate(req: AppRequest):
    """激活窗口（按标题或应用名匹配）"""
    return _activate_window(req.name)

@router.get("/cursor")
async def get_cursor():
    """获取鼠标位置"""
    return _get_cursor_pos()

@router.post("/execute")
async def post_execute(req: ExecuteRequest):
    """执行多步骤"""
    results = []
    for i, step in enumerate(req.steps):
        action = step.get("action")
        try:
            if action == "click":
                r = _click(step.get("x", 0), step.get("y", 0), step.get("button", "left"))
            elif action == "type":
                r = _type_text(step.get("text", ""))
            elif action == "shortcut":
                r = _shortcut(step.get("keys", ""))
            elif action == "scroll":
                r = _scroll(step.get("x", 0), step.get("y", 0), step.get("direction", "down"), step.get("wheel_times", 1))
            elif action == "move":
                r = _move_mouse(step.get("x", 0), step.get("y", 0))
            elif action == "app":
                r = _launch_app(step.get("name", ""))
            elif action == "wait":
                time.sleep(step.get("seconds", 1))
                r = {"success": True, "action": "wait"}
            elif action == "screenshot":
                r = _capture_screenshot()
            else:
                r = {"success": False, "error": f"未知操作: {action}"}
            results.append({"step": i, "action": action, "success": r.get("success", False)})
        except Exception as e:
            results.append({"step": i, "action": action, "success": False, "error": str(e)})
    return {"success": True, "steps": len(req.steps), "results": results}

# ── v2.0.0 新增功能占位 ─────────────────────────────
@router.post("/ocr")
async def post_ocr(req: OCRRequest):
    """OCR识别 - 需要安装 tesseract"""
    return {"success": False, "error": "OCR功能需要安装 tesseract-ocr (Linux: sudo apt install tesseract-ocr)"}

@router.post("/schedule")
async def post_schedule(req: ScheduleRequest):
    """定时任务 - 占位"""
    return {"success": False, "error": "定时任务功能开发中"}

@router.post("/record/start")
async def post_record_start(req: RecordStartRequest):
    """开始录制 - 占位"""
    return {"success": False, "error": "录制功能开发中"}

@router.post("/record/stop")
async def post_record_stop():
    """停止录制 - 占位"""
    return {"success": False, "error": "录制功能开发中"}

@router.get("/records")
async def get_records():
    """获取录制列表 - 占位"""
    return {"success": True, "records": []}

@router.post("/playback")
async def post_playback(req: PlaybackRequest):
    """回放录制 - 占位"""
    return {"success": False, "error": "回放功能开发中"}

@router.post("/smart-action")
async def post_smart_action(req: SmartActionRequest):
    """智能决策 - 占位"""
    return {"success": False, "error": "智能决策功能开发中"}

# ── 插件注册 ───────────────────────────────────────────
class JiePlugin:
    """界插件 - AI 浏览器 v2.0.1 (跨平台版: Windows + Linux + macOS)"""

    def register(self, api):
        api.register_http_router(router, prefix="/jie-browser", tags=["jie-browser"])
        logger.info(f"✅ 界 v2.0.1 已加载 — AI 浏览器就绪 (作者: 0+1+2≠3 Team 115886, 平台: {platform.system()})")

plugin = JiePlugin()
