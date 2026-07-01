---
name: 界 (Jie)
description: "AI 浏览器 v2.0.2 — 让 AI 像人一样看界面、操作界面、理解界面。跨平台桌面自动化中枢 (Windows + Linux + macOS)。"
---

# 界 — AI 浏览器使用技能 v2.0.2

## 架构
```
用户指令 -> 界插件 -> 平台原生 API -> 桌面操作
                ↓                    ├─ Windows: pywin32 + ctypes + UIA
                ↓                    ├─ Linux: xdotool + scrot + xclip
                ↓                    └─ macOS: CoreGraphics + screencapture + pbcopy + osascript
                ↓
          截图反馈 ← PIL / screencapture / scrot
                ↓
          OCR 识别 ← Tesseract (pytesseract)
                ↓
          UI 元素 ← MS UI Automation (uiautomation)
                ↓
          前端展示 (React) — 截图预览/操作面板/窗口列表
```

## API 端点

基础路径: `/api/jie-browser`

### 基础操作
| 端点 | 方法 | 说明 |
|------|------|------|
| `/stats` | GET | 系统统计：版本/平台/屏幕/鼠标 |
| `/snapshot` | GET | 桌面快照：截图(base64) + 宽高 |
| `/click` | POST | 鼠标点击：{x, y, button, clicks} |
| `/type` | POST | 输入文本：{text} — 支持中文 |
| `/scroll` | POST | 滚动：{x, y, direction, wheel_times} |
| `/move` | POST | 移动鼠标：{x, y} |
| `/shortcut` | POST | 快捷键：{keys} |
| `/app` | POST | 启动应用：{name} |
| `/windows` | GET | 窗口列表 |
| `/cursor` | GET | 鼠标当前位置 |
| `/activate` | POST | 激活窗口：{name} |
| `/execute` | POST | 多步骤编排：{steps: [{action, ...}]} |

### OCR 识别（v2.0.2 新增）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/ocr` | POST | OCR识别屏幕文字：{x?, y?, width?, height?, lang?} |
| `/ocr/find-text` | POST | 查找文字返回坐标：{text, region?} |
| `/ocr/click-text` | POST | 识别文字并自动点击：{text, region?} |

### UI Automation 元素识别（v2.0.2 新增）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/ui/elements` | GET | 获取当前窗口 UI 元素树 |
| `/ui/find` | POST | 查找元素：{name, control_type?} |
| `/ui/click` | POST | 点击元素：{name, control_type?} |

### 录制回放（v2.0.2 持久化）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/record/start` | POST | 开始录制：{name} |
| `/record/stop` | POST | 停止录制并自动保存 JSON |
| `/records` | GET | 列出所有已保存的录制 |
| `/recordings/save` | POST | 保存当前录制到文件：{name} |
| `/recordings/load` | POST | 从文件加载录制：{name} |
| `/playback` | POST | 回放录制：{name, speed?} |

## 跨平台支持矩阵

| 功能 | Windows | Linux | macOS |
|------|---------|-------|-------|
| 截图 | ✅ PIL ImageGrab | ✅ scrot/gnome-screenshot | ✅ screencapture |
| 鼠标点击 | ✅ pywin32 | ✅ xdotool | ✅ CoreGraphics |
| 文本输入 | ✅ win32clipboard+Ctrl+V | ✅ xclip+xdotool | ✅ pbcopy+Cmd+V |
| 快捷键 | ✅ keybd_event (v2.0.1修复) | ✅ xdotool key | ✅ CoreGraphics |
| 多媒体键 | ✅ v2.0.2 新增 | ❌ | ❌ |
| 滚动 | ✅ mouse_event | ✅ xdotool | ✅ CoreGraphics |
| 窗口列表 | ✅ EnumWindows | ⚠️ 简化 | ✅ osascript |
| OCR 识别 | ✅ Tesseract | ✅ Tesseract | ✅ Tesseract |
| UI 自动化 | ✅ UIA (v2.0.2) | ❌ | ❌ |
| 录制持久化 | ✅ JSON (v2.0.2) | ✅ JSON | ✅ JSON |

## 快捷键键码（v2.0.2 扩展）

### 基础键
`ctrl`, `alt`, `shift`, `win`, `tab`, `enter`, `esc`, `space`, `back`
`f1`~`f24`, `up`/`down`/`left`/`right`
`home`, `end`, `pageup`, `pagedown`, `delete`, `insert`

### 多媒体键（v2.0.2 新增）
`volumemute`, `volumedown`, `volumeup`
`nexttrack`, `prevtrack`, `playpause`, `mediastop`
`launchmail`, `launchmedia`, `launchapp1`, `launchapp2`

### 浏览器键（v2.0.2 新增）
`browser_back`, `browser_forward`, `browser_refresh`
`browser_stop`, `browser_search`, `browser_favorites`, `browser_home`

## 使用示例

### 示例1: OCR 识别文字并点击
```bash
# 1. 截取当前屏幕并识别文字
curl -s "http://127.0.0.1:64857/api/jie-browser/ocr" -d '{"lang": "chi_sim+eng"}'
# 2. 查找"确定"按钮位置
curl -s "http://127.0.0.1:64857/api/jie-browser/ocr/find-text" -d '{"text": "确定"}'
# 3. 自动点击"确定"按钮
curl -s "http://127.0.0.1:64857/api/jie-browser/ocr/click-text" -d '{"text": "确定"}'
```

### 示例2: UI Automation 定位按钮
```bash
# 1. 获取当前窗口的 UI 元素树
curl -s "http://127.0.0.1:64857/api/jie-browser/ui/elements"
# 2. 查找"保存"按钮
curl -s "http://127.0.0.1:64857/api/jie-browser/ui/find" -d '{"name": "保存", "control_type": "Button"}'
# 3. 点击"保存"按钮
curl -s "http://127.0.0.1:64857/api/jie-browser/ui/click" -d '{"name": "保存"}'
```

### 示例3: 录制与回放持久化
```bash
# 1. 开始录制（命名为"login_flow"）
curl -X POST "http://127.0.0.1:64857/api/jie-browser/record/start" -d '{"name": "login_flow"}'
# 2. 执行一系列操作（自动录制）
curl -X POST "http://127.0.0.1:64857/api/jie-browser/click" -d '{"x": 500, "y": 300}'
curl -X POST "http://127.0.0.1:64857/api/jie-browser/type" -d '{"text": "myaccount"}'
# 3. 停止录制（自动保存到 recordings/login_flow.json）
curl -X POST "http://127.0.0.1:64857/api/jie-browser/record/stop"
# 4. 列出所有录制
curl -s "http://127.0.0.1:64857/api/jie-browser/records"
# 5. 回放录制
curl -X POST "http://127.0.0.1:64857/api/jie-browser/playback" -d '{"name": "login_flow"}'
```

### 示例4: 扩展快捷键
```bash
# 音量控制
curl -X POST "http://127.0.0.1:64857/api/jie-browser/shortcut" -d '{"keys": "volumemute"}'
curl -X POST "http://127.0.0.1:64857/api/jie-browser/shortcut" -d '{"keys": "volumeup"}'

# 媒体控制
curl -X POST "http://127.0.0.1:64857/api/jie-browser/shortcut" -d '{"keys": "playpause"}'
curl -X POST "http://127.0.0.1:64857/api/jie-browser/shortcut" -d '{"keys": "nexttrack"}'

# 浏览器控制
curl -X POST "http://127.0.0.1:64857/api/jie-browser/shortcut" -d '{"keys": "browser_refresh"}'
curl -X POST "http://127.0.0.1:64857/api/jie-browser/shortcut" -d '{"keys": "browser_home"}'
```

## 依赖安装

```bash
# 基础依赖（必装）
pip install Pillow httpx

# OCR 支持（可选，建议安装）
pip install pytesseract
# Windows 还需安装: https://github.com/UB-Mannheim/tesseract/wiki

# UI Automation 支持（可选，仅 Windows）
pip install uiautomation
```

## 注意事项
- OCR 需要安装 Tesseract-OCR 引擎（Windows 需额外下载安装包）
- UI Automation 仅 Windows 平台可用，需 `pip install uiautomation`
- 录制文件保存在 `plugins/jie-browser/recordings/` 目录下
- 快捷键 v2.0.2 支持扩展多媒体键和浏览器键（仅 Windows）
- 截图返回 base64，前端直接显示
