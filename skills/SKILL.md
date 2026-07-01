---
name: 界 (Jie)
description: "AI 浏览器 v2.0.1 — 让 AI 像人一样看界面、操作界面、理解界面。跨平台桌面自动化中枢 (Windows + Linux + macOS)。"
---

# 界 — AI 浏览器使用技能

## 架构
```
用户指令 → 界插件 → 平台原生 API → 桌面操作
                ↓                    ├─ Windows: pywin32 + ctypes
                ↓                    ├─ Linux: xdotool + scrot + xclip
                ↓                    └─ macOS: CoreGraphics + screencapture + pbcopy + osascript
                ↓
          截图反馈 ← PIL / screencapture / scrot
                ↓
          前端展示 (React) — 截图预览/操作面板/窗口列表
```

## API 端点

基础路径: `/api/jie-browser`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/stats` | GET | 系统统计：插件数/工具数/屏幕分辨率/鼠标位置 |
| `/snapshot` | GET | 桌面快照：截图(base64) + 窗口列表 + 活动窗口 |
| `/click` | POST | 鼠标点击：{x, y, button, clicks} |
| `/type` | POST | 输入文本：{text} — 支持中文/日文/韩文 |
| `/scroll` | POST | 滚动：{x, y, direction, wheel_times} |
| `/move` | POST | 移动鼠标：{x, y} |
| `/shortcut` | POST | 快捷键：{keys} — 如 "ctrl+c", "alt+tab", "cmd+c"(macOS) |
| `/app` | POST | 启动/切换应用：{name} |
| `/windows` | GET | 窗口列表：所有可见窗口 |
| `/cursor` | GET | 鼠标当前位置 |
| `/activate` | POST | 激活窗口：{name} — 按标题匹配并前置 |
| `/execute` | POST | 多步骤编排：{steps: [{action, ...}]} |

## 跨平台支持矩阵

| 功能 | Windows | Linux | macOS |
|------|---------|-------|-------|
| 截图 | ✅ PIL ImageGrab | ✅ scrot/gnome-screenshot | ✅ screencapture (系统内置) |
| 鼠标点击 | ✅ pywin32 | ✅ xdotool | ✅ CoreGraphics (原生) |
| 文本输入 | ✅ pyperclip+Ctrl+V | ✅ xclip+xdotool | ✅ pbcopy+Cmd+V (系统内置) |
| 快捷键 | ✅ keybd_event | ✅ xdotool key | ✅ CoreGraphics (原生) |
| 滚动 | ✅ mouse_event WHEEL | ✅ xdotool click 4/5 | ✅ CoreGraphics scroll (原生) |
| 窗口列表 | ✅ EnumWindows | ️ 简化实现 | ✅ osascript (AppleScript) |
| 窗口激活 | ✅ SetForegroundWindow | ✅ xdotool windowactivate | ✅ osascript (AppleScript) |
| 应用启动 | ✅ subprocess | ✅ subprocess | ✅ open 命令 (系统内置) |
| 鼠标移动 | ✅ SetCursorPos | ✅ xdotool mousemove | ✅ CoreGraphics (原生) |
| 鼠标位置 | ✅ GetCursorPos | ✅ xdotool getmouselocation | ✅ CGEventGetLocation (原生) |

## 工作循环：观察 → 思考 → 行动 → 验证

### 步骤1: 观察
```
GET /api/jie-browser/snapshot
→ 获取桌面截图 + 窗口列表 + 鼠标位置
→ AI "看" 见当前界面
```

### 步骤2: 思考
```
分析截图中的 UI 元素位置
→ 确定需要操作的目标坐标
→ 规划操作步骤
```

### 步骤3: 行动
```
POST /api/jie-browser/move   {x, y}     — 移动到目标
POST /api/jie-browser/click  {x, y}     — 点击
POST /api/jie-browser/type   {text}     — 输入文本
POST /api/jie-browser/shortcut {keys}   — 快捷键
POST /api/jie-browser/app    {name}     — 启动应用
POST /api/jie-browser/activate {name}   — 激活窗口
POST /api/jie-browser/execute {steps}   — 批量执行
```

### 步骤4: 验证
```
GET /api/jie-browser/snapshot  — 再次截图确认结果
→ 对比操作前后状态
→ 必要时修正并重试
```

## 使用示例

### 示例1: 查看桌面
```bash
curl -s "http://127.0.0.1:64857/api/jie-browser/snapshot"
# 返回截图 + 窗口列表
```

### 示例2: 打开记事本并输入 (Windows)
```bash
# 1. 启动记事本
curl -X POST "http://127.0.0.1:64857/api/jie-browser/app" -d '{"name": "notepad"}'
# 2. 等待
curl -X POST "http://127.0.0.1:64857/api/jie-browser/execute" -d '{"steps": [{"action": "wait", "seconds": 1}]}'
# 3. 输入文本
curl -X POST "http://127.0.0.1:64857/api/jie-browser/type" -d '{"text": "Hello, 世界!"}'
# 4. 截图验证
curl -s "http://127.0.0.1:64857/api/jie-browser/snapshot"
```

### 示例3: macOS 操作
```bash
# 1. 打开 TextEdit
curl -X POST "http://127.0.0.1:64857/api/jie-browser/app" -d '{"name": "notepad"}'
# 2. 输入文本 (pbcopy + Cmd+V)
curl -X POST "http://127.0.0.1:64857/api/jie-browser/type" -d '{"text": "你好世界"}'
# 3. 保存 (Cmd+S)
curl -X POST "http://127.0.0.1:64857/api/jie-browser/shortcut" -d '{"keys": "cmd+s"}'
# 4. 截图验证
curl -s "http://127.0.0.1:64857/api/jie-browser/snapshot"
```

### 示例4: 多步骤编排
```bash
curl -X POST "http://127.0.0.1:64857/api/jie-browser/execute" \
  -H "Content-Type: application/json" \
  -d '{"steps": [
    {"action": "click", "x": 500, "y": 300},
    {"action": "wait", "seconds": 1},
    {"action": "type", "text": "Hello"},
    {"action": "shortcut", "keys": "enter"}
  ]}'
```

## macOS 特别说明

### 权限要求
macOS 需要在「系统设置 → 隐私与安全性」中授予以下权限：
- **辅助功能 (Accessibility)** — 鼠标/键盘控制必需
- **屏幕录制 (Screen Recording)** — 截图必需

### 零依赖设计
macOS 版使用系统内置工具，无需额外安装：
- `CoreGraphics` — 鼠标/键盘/滚动 (via ctypes)
- `screencapture` — 截图
- `pbcopy` — 剪贴板 (中文输入)
- `osascript` — AppleScript (窗口管理)
- `open` — 应用启动

### 快捷键映射
macOS 快捷键使用 `cmd` 代替 Windows 的 `ctrl`：
- `cmd+c` = 复制
- `cmd+v` = 粘贴
- `cmd+s` = 保存
- `cmd+z` = 撤销
- `cmd+tab` = 切换应用
- `cmd+q` = 退出应用

## 注意事项
- 截图返回 base64，前端直接显示
- 文本输入使用剪贴板方案，支持中日韩文字
- Windows/Linux: Ctrl+V，macOS: Cmd+V
- 快捷键支持组合键 (ctrl+shift+esc / cmd+shift+4)，用 `+` 分隔
- 窗口激活: Windows 用 SetForegroundWindow，macOS 用 AppleScript
- 所有操作异步执行，自动延迟300ms后截图更新
- macOS 需要授予辅助功能和屏幕录制权限
