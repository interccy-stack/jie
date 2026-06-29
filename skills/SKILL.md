---
name: 界 (Jie)
description: "AI 浏览器 v2.0.0 — 让 AI 像人一样看界面、操作界面、理解界面。基于 Windows API 的桌面自动化中枢。"
---

# 界 — AI 浏览器使用技能

## 架构
```
用户指令 → 界插件 → Windows API (pywin32+ctypes) → 桌面操作
                ↓
          截图反馈 ← PIL ImageGrab
                ↓
          前端展示 (React) — 截图预览/操作面板/窗口列表
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/界/stats` | GET | 系统统计：插件数/工具数/屏幕分辨率/鼠标位置 |
| `/api/界/snapshot` | GET | 桌面快照：截图(base64) + 窗口列表 + 活动窗口 |
| `/api/界/click` | POST | 鼠标点击：{x, y, button, clicks} |
| `/api/界/type` | POST | 输入文本：{text} — 支持中文 |
| `/api/界/scroll` | POST | 滚动：{x, y, clicks, direction} |
| `/api/界/move` | POST | 移动鼠标：{x, y} |
| `/api/界/shortcut` | POST | 快捷键：{keys} — 如 "ctrl+c", "alt+tab" |
| `/api/界/app` | POST | 启动/切换应用：{name, args} |
| `/api/界/windows` | GET | 窗口列表：所有可见窗口 |
| `/api/界/cursor` | GET | 鼠标当前位置 |
| `/api/界/execute` | POST | 多步骤编排：{steps: [{action, ...}]} |

## 工作循环：观察 → 思考 → 行动 → 验证

### 步骤1: 观察
```
GET /api/界/snapshot
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
POST /api/界/move   {x, y}     — 移动到目标
POST /api/界/click  {x, y}     — 点击
POST /api/界/type   {text}     — 输入文本
POST /api/界/shortcut {keys}   — 快捷键
POST /api/界/app    {name}     — 启动应用
POST /api/界/execute {steps}   — 批量执行
```

### 步骤4: 验证
```
GET /api/界/snapshot  — 再次截图确认结果
→ 对比操作前后状态
→ 必要时修正并重试
```

## 使用示例

### 示例1: 查看桌面
```python
# AI 发请求
GET /api/界/snapshot
# 返回截图 + 窗口列表
```

### 示例2: 打开记事本并输入
```python
# 1. 启动记事本
POST /api/界/app  {"name": "notepad"}
# 2. 等待
POST /api/界/execute {"steps": [{"action": "wait", "seconds": 1}]}
# 3. 输入文本
POST /api/界/type {"text": "Hello, 世界!"}
# 4. 截图验证
GET /api/界/snapshot
```

### 示例3: 一键操作（前端）
```
在"桌面"标签页:
1. 截图 → 查看当前桌面
2. 输入坐标 → 点击左键/右键/双击
3. 输入文本 → 发送到活动窗口
4. 快捷键 → 预设按钮 (Alt+Tab, Win+R 等)
5. 启动应用 → 输入名称或点快捷按钮
```

## 注意事项
- 截图返回 base64，前端直接显示
- 文本输入使用剪贴板+Ctrl+V方案，支持中文
- 快捷键支持组合键 (ctrl+shift+esc)，首字母匹配
- 窗口激活使用 win32gui 的 SetForegroundWindow
- 所有操作异步执行，自动延迟300ms后截图更新
