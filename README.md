# 界 (Jie) v2.0.2 - AI 浏览器 (跨平台版)

**破了谁界：微信、抖音、小红书、知乎、本地电脑的界....**
**让 AI 像人一样「看」界面、「操作」界面、「理解」界面。**
**破界是破除企业级OA、APP和ERP的物理限制，在有界空间操作，在无界空间部署**

跨平台桌面自动化中枢 (Windows + Linux + macOS)

---

## 🎯 核心能力

- **界面感知**：截图 + UI 元素树提取
- **语义理解**：LLM 分析界面意图
- **自动操作**：点击/输入/滚动/拖拽
- **任务编排**：多步骤自动化流程
- **结果验证**：操作后截图确认
- **记忆学习**：记住常用操作路径
- **定时任务**：按计划自动执行
- **录制回放**：记录并重放操作
- **OCR识别**：识别屏幕文字
- **智能决策**：条件判断自动响应

---

## 📦 安装要求

### 系统要求
- Windows 10/11 | Linux  |  macOS
- QwenPaw >= 1.1.10

### Python依赖
```
Pillow>=10.0.0
httpx>=0.27.0
pytesseract>=0.3.10
```

### OCR引擎（可选）
- Tesseract-OCR >= 5.0
- 下载地址：https://github.com/UB-Mannheim/tesseract/wiki

---

## 🚀 快速开始

### 1. 安装插件
```bash
# 方式1: QwenPaw控制台安装
qwenpaw plugin install jie-browser.zip

# 方式2: 手动解压
解压 jie-browser.zip 到 ~/.copaw/plugins/jie-browser/
```

### 2. 重启QwenPaw
```bash
qwenpaw restart
```

### 3. 验证安装
```bash
curl http://localhost:8088/api/jie-browser/stats
```

---

## 📖 API文档

### 基础操作

#### 截图
```bash
curl http://localhost:8088/api/jie-browser/snapshot
```

#### 点击
```bash
curl -X POST http://localhost:8088/api/jie-browser/click \
  -d '{"x":100,"y":200}'
```

#### 输入文字
```bash
curl -X POST http://localhost:8088/api/jie-browser/type \
  -d '{"text":"Hello","clear":true,"press_enter":true}'
```

#### 快捷键
```bash
curl -X POST http://localhost:8088/api/jie-browser/shortcut \
  -d '{"keys":"ctrl+s"}'
```

#### 启动应用
```bash
curl -X POST http://localhost:8088/api/jie-browser/app \
  -d '{"name":"notepad"}'
```

### 多步骤执行
```bash
curl -X POST http://localhost:8088/api/jie-browser/execute \
  -d '{
    "steps":[
      {"action":"app","name":"notepad"},
      {"action":"click","x":800,"y":400},
      {"action":"type","text":"Hello World"},
      {"action":"shortcut","keys":"ctrl+s"}
    ]
  }'
```

### 定时任务
```bash
curl -X POST http://localhost:8088/api/jie-browser/schedule \
  -d '{
    "action":"screenshot",
    "interval":60,
    "count":10
  }'
```

### 录制回放

#### 开始录制
```bash
curl -X POST http://localhost:8088/api/jie-browser/record/start \
  -d '{"name":"登录流程"}'
```

#### 停止录制
```bash
curl -X POST http://localhost:8088/api/jie-browser/record/stop
```

#### 回放录制
```bash
curl -X POST http://localhost:8088/api/jie-browser/playback \
  -d '{"name":"登录流程","speed":1.0}'
```

#### 列出录制
```bash
curl http://localhost:8088/api/jie-browser/records
```

### OCR识别
```bash
# 全屏识别
curl -X POST http://localhost:8088/api/jie-browser/ocr

# 区域识别
curl -X POST http://localhost:8088/api/jie-browser/ocr \
  -d '{"x":100,"y":100,"width":500,"height":300}'
```

### 智能决策
```bash
curl -X POST http://localhost:8088/api/jie-browser/smart-action \
  -d '{
    "condition":"错误",
    "action_if_true":{"action":"click","x":800,"y":600},
    "check_interval":1,
    "timeout":30
  }'
```

---

## 🎬 使用示例

### 示例1: 自动化记事本操作
```bash
# 1. 开始录制
curl -X POST /api/jie-browser/record/start -d '{"name":"记事本演示"}'

# 2. 执行操作
curl -X POST /api/jie-browser/app -d '{"name":"notepad"}'
curl -X POST /api/jie-browser/click -d '{"x":800,"y":400}'
curl -X POST /api/jie-browser/type -d '{"text":"Hello World"}'
curl -X POST /api/jie-browser/shortcut -d '{"keys":"ctrl+s"}'

# 3. 停止录制
curl -X POST /api/jie-browser/record/stop

# 4. 回放
curl -X POST /api/jie-browser/playback -d '{"name":"记事本演示"}'
```

### 示例2: 定时监控
```bash
# 每5分钟截图一次
curl -X POST /api/jie-browser/schedule \
  -d '{"action":"screenshot","interval":300,"count":-1}'
```

### 示例3: 智能错误处理
```bash
# 如果出现"错误"弹窗则点击确定
curl -X POST /api/jie-browser/smart-action \
  -d '{
    "condition":"确定",
    "action_if_true":{"action":"click","x":900,"y":600},
    "action_if_false":{"action":"wait"},
    "check_interval":2,
    "timeout":60
  }'
```

---

## 📁 文件结构

```
jie-browser/
├── plugin.json          # 插件配置
├── plugin.py            # 后端代码
├── README.md            # 说明文档
├── requirements.txt     # Python依赖
├── frontend/
│   └── dist/
│       └── index.js     # 前端界面
├── skills/
│   └── SKILL.md         # 技能文档
└── backend/
    └── __init__.py
```

---

## 🔧 故障排除

### OCR识别失败
1. 检查Tesseract-OCR是否安装
2. 检查pytesseract是否安装：`pip install pytesseract`
3. 检查Tesseract是否在PATH中

### 录制文件为空
1. 确认已开始录制：`/record/start`
2. 执行操作时会自动记录
3. 停止录制：`/record/stop`

### 点击无响应
1. 检查坐标是否正确
2. 确认目标窗口在前台
3. 使用Snapshot查看当前界面

---

## 👨‍💻 作者

**0+1+2≠3 Team 115886**

---

## 📄 版本历史

### v2.0.2 (2026-07-01)
- ✅ 跨平台支持 ### v2.0.2 (2026-07-01)
- ✅ 新增: OCR识图、UI元素识别(Accessibility)、录制回放持久化、扩展键码(含多媒体键)

### v2.0.0 (2026-06-29)
- ✅ 跨平台支持 (Windows + Linux)
- ✅ Windows: 使用 ctypes + pywin32
- ✅ Linux: 使用 xdotool + scrot + xclip
- ✅ 统一 API，自动适配平台
- ✅ 前端显示当前平台标识

### v1.1.5 (2026-06-29)
- ✅ 完全重写前端代码，与 eradicate 插件结构一致
- ✅ 使用立即执行函数包裹 (function(){...})()
- ✅ 修复菜单不显示问题

### v1.1.4 (2026-06-29)
- ✅ 修复菜单显示问题（参考 eradicate 插件注册方式）
- ✅ 使用 `location: 'primary.settings'` 注册到左侧菜单

### v1.1.3 (2026-06-29)
- ✅ 增强路径自动检测（支持.copaw/.qwenpaw/自定义位置）
- ✅ 5种路径检测方法，确保跨平台兼容

### v1.1.2 (2026-06-29)
- ✅ 支持自动检测QwenPaw安装路径
- ✅ 跨平台兼容（不同用户、不同安装位置）

### v1.1.1 (2026-06-29)
- ✅ 录制自动记录功能完善
- ✅ 所有API操作自动记录到录制文件

### v1.1.0 (2026-06-29)
- ✅ 新增定时任务功能
- ✅ 新增录制回放功能
- ✅ 新增OCR识别功能
- ✅ 新增智能决策功能

### v1.0.0 (2026-06-28)
- ✅ 基础桌面自动化功能
- ✅ 截图/点击/输入/滚动/快捷键
- ✅ 多步骤任务编排

---

## 📞 支持

如有问题，请通过邮件联系：115886@qq.com
