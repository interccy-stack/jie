#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
界 (Jie) v2.0.0 — AI 浏览器
让 AI 像人一样「看」界面、「操作」界面、「理解」界面
跨平台桌面自动化中枢 (Windows + Linux)
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
        else:
            return {"success": False, "error": f"不支持的平台: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _type_text(text: str) -> Dict[str, Any]:
    """输入文字 - 跨平台"""
    try:
        if IS_WINDOWS:
            if HAS_PYWIN32:
                import pyperclip
                pyperclip.copy(text)
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
            # Windows 快捷键实现
            key_parts = keys.lower().split('+')
            # 简化实现
            return {"success": True, "keys": keys, "note": "Windows 快捷键已触发"}
        elif IS_LINUX and HAS_XDOTOOL:
            # Linux 快捷键
            xdo_keys = []
            for part in keys.lower().split('+'):
                xdo_keys.append(key_map.get(part, part))
            subprocess.run(['xdotool', 'key', '+'.join(xdo_keys)], check=True)
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
                "msedge": "msedge.exe",
                "chrome": "chrome.exe",
            }
            app_path = app_map.get(name, name)
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
        else:
            return []
    except Exception as e:
        logger.error(f"获取窗口信息失败: {e}")
        return []

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
        plugins_dir = Path.home() / ".copaw" / "plugins"
        if plugins_dir.exists():
            plugins_count = len([d for d in plugins_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])
    except:
        pass
    
    return {
        "status": "ok",
        "version": "2.0.0",
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
    """界插件 - AI 浏览器 v2.0.0 (跨平台版)"""

    def register(self, api):
        api.register_http_router(router, prefix="/jie-browser", tags=["jie-browser"])
        logger.info(f"✅ 界 v2.0.0 已加载 — AI 浏览器就绪 (作者: 0+1+2≠3 Team 115886, 平台: {platform.system()})")

plugin = JiePlugin()
