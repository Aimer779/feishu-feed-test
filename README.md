# Feishu Card Sender

通过飞书 Webhook 发送多种类型的卡片消息。支持模板化管理和命令行快速发送，以及基于代码动态组装的 AI 资讯卡片推送。

## 已实现功能

- **多模板卡片发送**：内置文本、Markdown、模板卡片、旅游推荐、AI 资讯等多种卡片
- **动态模板加载**：所有静态卡片模板存放于 `cards/` 目录，程序启动时自动扫描加载，无需修改代码即可增删模板
- **动态卡片构建**：通过 `sender` 包按平台、时间范围、主题动态组装飞书卡片，主题数量和子信息数完全自适应
- **AI 资讯工作流**：已预留 `fetcher.py`（信息抓取器）、`summarizer`（信息总结器）和 `sender`（消息发送器）的标准接口，未来可直接接入 AI 自动化流程
- **灵活的命令行参数**：支持选择模板、加载外部 JSON、自定义 Webhook、简单变量覆盖等
- **虚拟环境管理**：使用 `uv` 进行 Python 虚拟环境创建和依赖安装

## 环境准备

项目使用 [uv](https://github.com/astral-sh/uv) 管理虚拟环境和依赖。

```powershell
# 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt
```

## 配置

1. 复制环境变量模板：
   ```powershell
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入真实的飞书 Webhook 地址：
   ```text
   FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx
   ```

3. 也可以通过环境变量直接覆盖：

```powershell
$env:FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
.venv\Scripts\python.exe -m sender
```

## 使用方法

### 发送静态模板卡片

```powershell
# 使用默认模板（从 .env 读取 webhook）
.venv\Scripts\python.exe -m sender

# 使用指定模板
.venv\Scripts\python.exe -m sender --template travel

# 从外部 JSON 文件加载
.venv\Scripts\python.exe -m sender --file my-card.json

# 临时覆盖 webhook 地址
.venv\Scripts\python.exe -m sender --template text --webhook https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx

# 使用 mock payload 发送（用于测试）
.venv\Scripts\python.exe -m sender --mock
```

### 查看所有可用静态模板

```powershell
.venv\Scripts\python.exe -m sender --list
```

### 覆盖模板变量

```powershell
.venv\Scripts\python.exe -m sender --template text --var "text=自定义消息内容"
```

> 注：`--var` 目前仅支持对 `payload` 顶层、`card` 层或 `content` 层的字符串值进行简单替换。

### 运行动态 AI Daily 卡片构建器

```powershell
# 运行示例（会发送示例数据到配置的 webhook）
.venv\Scripts\python.exe examples\preview_ai_daily.py
```

### 测试 summarizer（调用 LLM 并输出 JSON）

```powershell
.venv\Scripts\python.exe -m summarizer
```

`examples/preview_ai_daily.py` 会生成四个预览文件用于调试：
- `preview_ai_daily_x.json`
- `preview_ai_daily_jike.json`
- `preview_ai_daily_hn.json`
- `preview_ai_daily_cross.json`

### 从外部数据文件发送卡片

如果你有预处理好的 categories 数据（如 `out.json`），可直接发送：

```powershell
.venv\Scripts\python.exe send_out.py
```

### 端到端链路测试（summarizer → card_builder → 发送）

```powershell
.venv\Scripts\python.exe tests\test_e2e.py
```

## 内置静态模板

| 模板名 | 说明 |
|--------|------|
| `default` | 原始模板卡片（`template_id: <你的模板ID>`） |
| `text` | 纯文本消息 |
| `markdown` | Markdown 富文本卡片 |
| `travel` | 西湖旅游推荐卡片 |
| `feishu-card` | 五条 AI Daily 资讯卡片（静态内容版） |
| `task-report` | 任务详情报告卡片（带 collapsible_panel） |
| `ai-daily` | AI 资讯动态卡片（视觉结构参考，实际由 `sender` 动态组装） |

## 新增静态模板注意事项

1. **必须是完整的 Webhook Payload**
   - `cards/` 目录中的 JSON 文件最外层必须包含 `msg_type` 和 `card`，例如：
     ```json
     {
       "msg_type": "interactive",
       "card": {
         "schema": "2.0",
         ...
       }
     }
     ```
   - 不能直接将飞书卡片搭建工具导出的纯 `card` 定义放入该目录，否则会导致发送失败或内容解析异常。

2. **模板变量需提前静态化**
   - 如果卡片中使用了 `${variable}` 或 `repeat` 组件，直接通过 Webhook 发送时变量区域会显示**空白**或原始占位符。
   - 建议先在 JSON 中填充为静态内容，再注册到 `cards/` 目录。

3. **文件名即模板名**
   - 文件名将直接作为 `--template` 的参数名（不含 `.json` 后缀）。
   - 建议使用英文小写、短横线连接，如 `daily-report.json`。

4. **确保 JSON 格式合法**
   - 启动时若某个 `.json` 解析失败，程序会直接报错退出。
   - 新增后建议先用 `--list` 检查是否能正常加载。

5. **图片资源需有效**
   - 若模板中引用了 `img_key`，请确保图片已上传到该机器人/应用所在的飞书租户，否则图片区域会显示裂图。

## 动态卡片架构（推荐用于 AI 资讯推送）

对于需要按不同平台、不同时间间隔、不同主题数量动态生成的卡片，建议使用 `sender.builder` 动态组装，而非修改静态 JSON 文件。

### 数据流

```
fetcher.py (抓取) → summarizer (AI 总结分类) → sender (组装+发送)
```

### `sender.builder` 核心能力

- **平台差异化**：支持 `X`、`即刻`、`HackerNews` 等不同平台，标题自动显示平台名
- **时间范围自适应**：支持 1 小时、2 小时、24 小时等任意间隔，自动处理跨天场景
  - 同一天：`2026.04.17 16 - 17`
  - 跨天：`2026.04.17 23 - 2026.04.18 01`
- **主题数量自适应**：上游返回几个主题，卡片就生成几个 `collapsible_panel`（0~N 个）
- **子信息数自适应**：每个主题下 1~M 条信息均可正常渲染
- **emoji 硬编码映射**：`categories.py` 维护 `CATEGORY_EMOJI_MAP`，上游 AI 只需输出主题名，无需关心 emoji

### 7 大预设主题

| 主题 | emoji |
|:---|:---|
| 大厂&融资 | 🏢 |
| 模型&论文 | 🧠 |
| 产品&开源 | 🛠️ |
| 编程&架构 | 💻 |
| 增长&自媒体 | 📈 |
| 独立开发 | 🚀 |
| 观点&争议 | 💬 |

### 上游约定

`fetcher.py` 输出原始文章列表，`summarizer` 调用 AI 后输出如下结构：

```python
[
    {
        "name": "大厂&融资",
        "summary": "科技巨头新一轮融资潮涌动...",
        "items": [
            {
                "title": "某 AI 独角兽完成 10 亿美元融资",
                "summary": "据 [Bloomberg](https://...) 报道，估值突破 300 亿美元。"
            }
        ]
    }
]
```

> 注意：若某主题无文章，则**不应出现在列表中**；AI 输出也**不需要包含 emoji**。

## 项目结构

```text
.
├── cards/                      # 静态卡片模板目录
│   ├── ai-daily.json           # AI 资讯卡片（视觉参考，供静态加载测试）
│   ├── default.json
│   ├── feishu-card.json
│   ├── markdown.json
│   ├── task-report.json
│   ├── text.json
│   └── travel.json
├── sender/                     # 消息发送器（包）
│   ├── __init__.py             # 导出 build_ai_daily_card / send_card / load_templates 等
│   ├── __main__.py             # CLI 入口 (python -m sender)
│   ├── core.py                 # 传输层：send_card() + WEBHOOK_URL
│   ├── builder.py              # 动态卡片构建器（纯函数）
│   ├── templates.py            # 模板加载、变量替换、文件读取
│   ├── fixtures.py             # mock payload
│   └── schema.py               # 卡片数据类型定义
├── summarizer/                 # 信息总结器（包）
│   ├── __init__.py             # 导出 summarize()
│   ├── __main__.py             # CLI 入口 (python -m summarizer)
│   ├── core.py                 # summarize() + _render_user_prompt()
│   ├── prompt.py               # SYSTEM_PROMPT
│   ├── schema.py               # RESPONSE_SCHEMA + CATEGORIES_ENUM
│   └── fixtures.py             # mock_articles()
├── tests/
│   └── test_e2e.py             # 端到端链路测试
├── examples/
│   └── preview_ai_daily.py     # AI Daily 卡片示例与预览入口
├── .venv/                      # Python 虚拟环境（由 uv 创建）
├── requirements.txt            # 项目依赖
├── send_out.py                 # 从外部数据文件直接发送卡片
├── categories.py               # 主题与 emoji 映射
├── fetcher.py                  # 信息抓取器（接口预留，待接入各平台爬虫）
├── tmp/                        # 临时输出目录（预览文件、测试产物，已加入 .gitignore）
├── lesson.md                   # 飞书卡片实战经验总结
└── README.md                   # 本文件
```

## 经验参考

项目开发过程中积累的飞书卡片兼容性经验（如 schema 2.0 不支持 `background_style`、`action` 包装层等）已整理在 `lesson.md` 中，可供后续开发参考。
