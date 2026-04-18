# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 会话约定

- 启动会话时先阅读 `README.md`（来自 `AGENTS.md` 的约定）。
- 遇到飞书卡片相关报错时，优先查阅 `lesson.md`，其中记录了 schema 2.0 的兼容性坑点（如不支持 `background_style`、`action` 包装层等）。

## 环境与常用命令

项目使用 [uv](https://github.com/astral-sh/uv) 管理虚拟环境。Webhook 地址从 `.env` 的 `FEISHU_WEBHOOK_URL` 读取。

```powershell
# 初始化
uv venv
uv pip install -r requirements.txt

# 静态模板发送（CLI 入口 = sender 包）
.venv\Scripts\python.exe -m sender --list
.venv\Scripts\python.exe -m sender --template travel
.venv\Scripts\python.exe -m sender --file my-card.json
.venv\Scripts\python.exe -m sender --template text --var "text=自定义"
.venv\Scripts\python.exe -m sender --mock          # 使用内置 mock payload 调试

# 动态 AI Daily 卡片预览（在 tmp/ 下写出 preview_ai_daily_*.json 并发送其中一份示例）
.venv\Scripts\python.exe examples\preview_ai_daily.py

# 从已生成的 out.json 直接发送一条 AI Daily
.venv\Scripts\python.exe send_out.py

# summarizer 独立调试（读 mock 文章，打印 categories JSON）
.venv\Scripts\python.exe -m summarizer

# 端到端：mock 文章 → summarizer → builder → 发送
.venv\Scripts\python.exe tests\test_e2e.py
```

环境变量（见 `.env.example`）：`FEISHU_WEBHOOK_URL` 给发送用，`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` 给 summarizer 用。

项目目前没有 pytest 等测试框架或 lint 配置，`tests/test_e2e.py` 是手动运行的端到端脚本。

## 代码架构

两条并行的发送路径，共享同一个飞书 Webhook。核心代码按职责拆分到两个包：`sender/`（卡片构建 + 发送 + 静态模板）和 `summarizer/`（原始文章 → categories）。

1. **静态模板路径 —— `sender` 包 + `cards/`**
   - 入口：`python -m sender`（见 `sender/__main__.py`），复用 `sender/templates.py` 的 `load_templates()` 扫描 `cards/*.json`，文件名（去掉后缀）即 `--template` 参数值。
   - 每个 JSON **必须是完整的 Webhook payload**（最外层含 `msg_type` 和 `card`），不能直接粘贴飞书卡片搭建工具导出的纯 `card` 定义。
   - `${variable}` 与 `repeat` 组件通过 Webhook 发送时**不会被渲染**，新增模板时需先静态化。
   - `apply_vars` 只做 payload 顶层 / `card` 层 / `content` 层的简单字符串替换，不是完整的模板引擎。
   - `--mock` 走 `sender/fixtures.py::mock_payload()`，内部直接调 `build_ai_daily_card`，用来在不依赖真实模板的情况下验证发送链路。

2. **动态构建路径 —— `sender/builder.py` + `sender/core.py` + `categories.py`**
   - `sender.build_ai_daily_card(categories, platform, start_time, end_time)`（在 `sender/builder.py`，从包顶层 re-export）为纯函数：按平台（X / 即刻 / HackerNews…）与时间窗自适应生成标题，并为 `categories` 中每个主题生成一个 `collapsible_panel`。
   - `sender.send_card(webhook_url, payload)`（在 `sender/core.py`）负责实际 HTTP 发送；`FEISHU_WEBHOOK_URL` 只在这里 `load_dotenv`，同时作为模块级 `WEBHOOK_URL` 导出。
   - `categories.CATEGORY_EMOJI_MAP` 集中维护 7 个预设主题的 emoji（大厂&融资、模型&论文、产品&开源、编程&架构、增长&自媒体、独立开发、观点&争议）；`summarizer/schema.py` 通过 `CATEGORIES_ENUM = list(CATEGORY_EMOJI_MAP.keys())` 从这里派生主题白名单并注入 JSON Schema 的 `enum`。**上游 AI 只输出主题名，不输出 emoji**；无内容的主题不应出现在列表中。
   - `format_time_range()` 自动识别同日/跨日，生成 `YYYY.MM.DD HH - HH` 或跨日格式。
   - 预览入口：`examples/preview_ai_daily.py`（内置 `SAMPLE_CATEGORIES`，写到 `tmp/preview_ai_daily_*.json`）。
   - 生产发送入口：根目录的 `send_out.py`，从项目根的 `out.json`（summarizer 输出的 categories）读取数据并发送。

### 数据流水线

```
fetcher.py  →  summarizer/  →  sender/builder.py  →  sender/core.py
(按平台周期抓取) (AI 主题分类+摘要)   (组装 payload)       (发送到 webhook)
```

- `fetcher.py` 目前**仅有 docstring 规范**，没有实现体。新增实现需遵守文件头约定：输出带 `platform / title / url / content / author / published_at` 的原始文章列表。
- `summarizer/` 已是完整实现：`core.summarize(articles, platform)` 走 OpenAI 兼容 API（`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`），以 `summarizer/prompt.py` 的 system prompt + `summarizer/schema.py` 的 `response_format={"type": "json_schema"}` 约束结构，返回 `[{name, summary, items: [{title, summary}]}]`，即 `build_ai_daily_card` 期望的 `categories` 参数。空 items 的主题会被过滤掉。
- `summarizer/fixtures.py::mock_articles()` 提供可直接喂给 `summarize` 的样例文章，`python -m summarizer` 会用它跑一遍并打印 JSON。
- 平台抓取周期约定：X 1 小时、即刻 2 小时、HackerNews 24 小时。

## 新增内容的注意事项

- **新静态模板**：放入 `cards/`，保持完整 payload 格式；新增后用 `python -m sender --list` 验证是否被正确加载（解析失败会直接使程序退出）。引用的 `img_key` 需上传到对应飞书租户。
- **扩展动态卡片的主题**：同时更新 `categories.py` 的 `CATEGORY_EMOJI_MAP` 与 README 中的主题表，保持两处一致；`summarizer/schema.py` 的枚举和 `summarizer/prompt.py` 里的主题说明由前者派生/同步，新增主题时记得在 prompt 里补上对应的说明。
- **调试卡片视觉**：`examples/preview_ai_daily.py` 运行会在 `tmp/` 下写出 `preview_ai_daily_*.json`，可用作不发送情况下的 payload 校对（历史预览文件保留在 `test-file/`，`backup/` 保留 AI Daily 卡片的演进版本）。
