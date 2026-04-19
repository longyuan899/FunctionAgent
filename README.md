# 🤖 FunctionAgent

> 基于大语言模型与 Function Calling 技术的智能任务代理系统。
> 支持自然语言调用日历、搜索、会议室、数据库等多种工具，让 AI 成为真正的智能助手。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🔌 **Function Calling** | 深度集成大模型工具调用协议，支持多轮工具推理与执行 |
| 🧠 **ReAct 架构** | 采用 ReAct（Reasoning + Acting）范式，思考→行动→观察闭环 |
| 🛠️ **10+ 工具支持** | 内置日历、搜索、天气、单位换算、数据库、会议室等工具 |
| 💬 **流式对话** | 支持流式输出，实时展示 AI 回复过程 |
| 📜 **会话管理** | 多会话并行管理，支持历史记录查询与清空 |
| 🎨 **精美 UI** | GitHub 风格深色主题，无需登录，开箱即用 |
| 🔒 **本地优先** | 所有数据本地存储，无需第三方服务 |

---

## 🚀 快速开始

### 环境要求

- **Python** 3.10 或更高版本
- ** DashScope API Key**（阿里云通义千问，用于 LLM 调用）

### 安装

```bash
# 克隆项目
git clone https://github.com/longyuan899/FunctionAgent.git
cd FunctionAgent

# 创建虚拟环境（推荐）
python -m venv .venv
.\.venv\Scripts\activate     # Windows
# source .venv/bin/activate   # macOS / Linux

# 安装依赖
pip install -r requirements.txt
```

### 配置

在项目根目录创建 `.env` 文件：

```env
# DashScope API Key（必填）
# 获取地址：https://dashscope.console.aliyun.com/
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 应用配置（可选）
APP_NAME=FunctionAgent
APP_VERSION=1.0.0
LOG_LEVEL=INFO
```

### 启动

```bash
# Windows
.\run.bat

# 或手动启动
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

打开浏览器访问：**http://localhost:8001**

---

## 🗂️ 工具一览

本系统内置以下工具，开箱即用：

### 📅 日历工具

| 工具 | 功能 |
|------|------|
| `calendar_query` | 查询指定日期范围内的所有日程 |
| `calendar_create` | 创建新日程（标题、时间、参与者） |
| `calendar_check_conflict` | 检查时间冲突，避免重复预约 |

### 🔍 搜索工具

| 工具 | 功能 |
|------|------|
| `web_search` | 搜索互联网，返回标题、URL 和摘要 |
| `weather_query` | 查询城市天气预报，支持多日预报 |
| `unit_convert` | 单位换算（长度、温度、重量等） |

### 🏢 会议室工具

| 工具 | 功能 |
|------|------|
| `room_search` | 查询可用会议室（按容量、位置筛选） |
| `room_book` | 预约会议室（自动冲突检测） |

### 🗄️ 数据库工具

| 工具 | 功能 |
|------|------|
| `db_schema` | 查看数据库表结构（字段、类型、说明） |
| `db_query` | 执行 SQL 查询（只读，支持多表关联） |

---

## 🏗️ 项目架构

```
FunctionAgent/
├── main.py                          # 应用入口
├── app/
│   ├── __init__.py                  # 应用工厂 create_app()
│   ├── config.py                    # 配置管理（Pydantic Settings）
│   ├── api/
│   │   └── chat.py                  # 对话 API 路由
│   ├── core/
│   │   └── agent.py                 # ReAct Agent 核心引擎
│   ├── models/
│   │   └── schemas.py              # Pydantic 数据模型
│   ├── services/
│   │   ├── llm_service.py         # LLM 服务（DashScope）
│   │   └── session_manager.py      # 会话存储管理
│   └── tools/
│       ├── base.py                  # 工具基类与注册中心
│       ├── search_tool.py           # 搜索/天气/单位工具
│       ├── calendar_tool.py         # 日历工具
│       ├── meeting_room_tool.py     # 会议室工具
│       └── database_tool.py         # 数据库工具
└── frontend/
    └── templates/                   # Jinja2 前端模板
        ├── index.html               # 首页
        ├── chat.html                # 对话页面
        ├── tools.html               # 工具列表
        └── history.html             # 历史记录
```

### 核心流程

```
用户输入
  ↓
Agent 接收消息
  ↓
LLM 推理（携带工具 schema）
  ↓
┌─ 无需工具？ → 直接回复用户
│
└─ 需要工具？ → 执行工具 → 注入结果 → LLM 继续推理
                  ↑                    ↓
                  └────── 循环 ≤ 8 轮 ──┘
  ↓
最终回答
```

---

## 📡 API 文档

启动服务后访问 **http://localhost:8001/docs** 查看完整 Swagger 文档。

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/tools` | 获取所有可用工具列表 |
| `POST` | `/api/chat` | 发送对话消息 |
| `GET` | `/api/history/{session_id}` | 获取指定会话历史 |
| `GET` | `/api/sessions` | 获取所有会话列表 |
| `DELETE` | `/api/session/{session_id}` | 删除指定会话 |
| `DELETE` | `/api/sessions` | 清空所有历史会话 |

### 对话请求示例

```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我查一下北京明天的天气",
    "session_id": null
  }'
```

### 响应示例

```json
{
  "session_id": "a1b2c3d4",
  "reply": "北京明天天气晴，最高气温28°C，最低气温18°C，适合出行。",
  "tool_calls": [
    {
      "id": "call_001",
      "name": "weather_query",
      "arguments": "{\"city\": \"北京\", \"days\": 1}",
      "result": "{\"success\": true, \"city\": \"北京\", \"forecast\": [...]}",
      "success": true
    }
  ],
  "turns": 2,
  "elapsed_ms": 1243.5
}
```

---

## 🧩 技术栈

| 层级 | 技术 |
|------|------|
| **框架** | FastAPI + Uvicorn |
| **LLM** | DashScope（通义千问 Qwen） |
| **前端** | 原生 HTML/CSS/JS + Jinja2 |
| **数据模型** | Pydantic v2 |
| **配置管理** | Pydantic Settings + python-dotenv |
| **日志** | Loguru |
| **会话存储** | 本地 JSON 文件（`data/` 目录） |
| **工具调用** | DashScope Function Calling API |

---

## 🎯 使用示例

### 对话示例

```
👤 用户：查一下下周三下午2点到4点有哪些会议室可用

🤖 Agent：
   → 调用 room_search 工具
   → 发现 3 个可用会议室：1001（8人）、1002（12人）、1003（20人）
   
   返回给用户：
   "下周三下午2-4点可用的会议室有：
   • 1001 会议室（8人，10楼南）
   • 1002 会议室（12人，10楼北）
   • 1003 会议室（20人，12楼）
   
   需要我帮你预约吗？"

👤 用户：帮我预约1002

🤖 Agent：
   → 调用 room_book 工具预约 1002
   → 预约成功！

   "已成功预约 1002 会议室（12人），时间是下周三14:00-16:00。"
```

---

## 🔧 高级配置

### 更换 LLM 模型

修改 `app/services/llm_service.py` 中的模型配置：

```python
# 当前默认使用 qwen-plus
MODEL_NAME = "qwen-plus"   # 或 "qwen-max", "qwen-long" 等
```

### 添加新工具

1. 在 `app/tools/` 目录下创建新工具文件
2. 继承 `BaseTool` 基类
3. 在工具文件中调用 `registry.register(YourTool())`
4. 工具自动注册，无需修改其他代码

```python
from app.tools.base import BaseTool, ToolParameter, registry

class MyCustomTool(BaseTool):
    name = "my_custom_tool"
    description = "我的自定义工具"
    category = "custom"
    parameters = [
        ToolParameter(name="param1", type="string", description="参数说明", required=True),
    ]

    def execute(self, param1, **kwargs) -> dict:
        return {"success": True, "result": f"处理了: {param1}"}

registry.register(MyCustomTool())
```

---

## 📝 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| `v1.0.0` | 2026-04 | 初始版本，支持 10 个内置工具，ReAct 推理引擎 |

---

## ❓ 常见问题

**Q: 工具调用返回的数据是模拟的吗？**
> A: 目前部分工具（搜索、天气、会议室）返回模拟数据用于演示。接入真实 API（如 SERP、Google Weather）后可获得真实数据。

**Q: 会话数据存储在哪里？**
> A: 默认存储在 `data/` 目录下（JSON 文件），可修改 `app/config.py` 中的 `DATA_DIR` 配置更改存储路径。

**Q: 如何修改工具调用最大轮次？**
> A: 修改 `app/core/agent.py` 中的 `MAX_TURNS = 8`（默认 8 轮）。

**Q: 支持流式输出吗？**
> A: 当前版本已实现流式响应，前端实时展示回复；后端 API 支持流式和非流式两种模式。

---

## 📄 License
