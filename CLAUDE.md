# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 会话约定

- 启动会话时先阅读 `README.md`。
- 遇到飞书卡片相关报错时，优先查阅 `lesson.md`，其中记录了 schema 2.0 的兼容性坑点（如不支持 `background_style`、`action` 包装层等）。
- **运行端到端测试时，Shell timeout 必须设为至少 300 秒（5 分钟）**。`tests/test_x_e2e.py`、`tests/test_reddit_e2e.py`、`tests/test_hn_e2e.py` 和 `hourly_bot.py` 都涉及 Apify 抓取 + LLM summarization，其中 summarizer 处理 60+ 篇文章在 `qwen3.6-plus` 模型下耗时约 150~160 秒，120 秒超时必断。

## 环境与常用命令

项目使用 [uv](https://github.com/astral-sh/uv) 管理虚拟环境。配置统一由 `config.py` 管理（单点 `load_dotenv()`），日志由 `logger.py` 封装（基于 loguru）。

```bash
# 初始化
uv venv
uv pip install -r requirements.txt

# 静态模板发送（CLI 入口 = sender 包）
# Windows: .venv\Scripts\python.exe -m sender ...
# Linux/macOS: .venv/bin/python -m sender ...
.venv/bin/python -m sender --list
.venv/bin/python -m sender --template travel
.venv/bin/python -m sender --file my-card.json
.venv/bin/python -m sender --template text --var "text=自定义"
.venv/bin/python -m sender --mock          # 使用内置 mock payload 调试

# summarizer 独立调试（读 mock 文章，打印 categories JSON）
.venv/bin/python -m summarizer

# HackerNews 抓取调试（打印前 3 条结构化文章）
.venv/bin/python -m fetcher.hn

# X / Reddit 抓取调试（走 Apify，需 APIFY_API_TOKEN）
.venv/bin/python -m fetcher.x
.venv/bin/python -m fetcher.reddit

# 按平台节奏运行定时推送（不发飞书）
.venv/bin/python hourly_bot.py --dry-run
.venv/bin/python hourly_bot.py --only x --dry-run
.venv/bin/python hourly_bot.py --only reddit --dry-run
.venv/bin/python hourly_bot.py --only hn --dry-run
.venv/bin/python hourly_bot.py --force --dry-run

# 端到端：mock 文章 → summarizer → builder → 发送
.venv/bin/python tests/test_e2e.py

# 端到端：真实抓取 → summarizer → builder → 发送
.venv/bin/python tests/test_hn_e2e.py --dry-run
.venv/bin/python tests/test_x_e2e.py --dry-run
.venv/bin/python tests/test_reddit_e2e.py --dry-run

# 最小契约测试（验证 fetcher / summarizer / builder 的边界）
.venv/bin/python tests/test_contracts.py
```

环境变量（见 `.env.example`）：`FEISHU_WEBHOOK_URL` 给发送用，`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` 给 summarizer 用，`APIFY_API_TOKEN` 给 `fetcher/x.py` 和 `fetcher/reddit.py` 用，`LOG_LEVEL` / `LOG_FILE` 控制日志级别和文件持久化（可选）。所有环境变量统一通过 `config.py` 的 `get_env()` / `require_env()` 读取，各子模块不再自行调用 `load_dotenv()`。

项目目前没有 pytest 等测试框架或 lint 配置。`tests/` 下多数脚本仍是手动运行的端到端脚本；其中 `test_e2e.py` 用 mock 文章，`test_hn_e2e.py` / `test_x_e2e.py` / `test_reddit_e2e.py` 走真实抓取。新增的 `test_contracts.py` 是最小离线测试，用于验证 `fetcher -> summarizer -> builder` 的共享契约层。

## 代码架构

两条并行的发送路径，共享同一个飞书 Webhook。核心代码按职责拆分到三个包：`fetcher/`（各平台抓取）、`summarizer/`（原始文章 → categories）、`sender/`（卡片构建 + 发送 + 静态模板）。主链路之间新增了 `contracts.py` 作为轻量统一契约层。配置统一由 `config.py` 管理，日志由 `logger.py`（基于 loguru）提供结构化输出。

4. **配置与日志 —— `config.py` + `logger.py`**
   - `config.py` 是全局唯一的 `load_dotenv()` 调用点。提供三层 API：`load_config()` 启动时严格校验所有必需项；`require_env(key, hint)` 缺失时友好退出；`get_env(key, default)` 静默回退。
   - `logger.py` 封装 loguru，`init_logging(level, log_file)` 在 `hourly_bot.py` 启动时调用一次；`get_logger(name)` 返回带 bind 的 logger 实例。主链路各阶段有计时和上下文埋点。
   - 子模块（`sender/core.py`、`summarizer/core.py`、`fetcher/x.py`、`fetcher/reddit.py`）均通过 `config.get_env()` 读取配置，不再自行调用 `load_dotenv()` 或 `os.getenv()`。

1. **静态模板路径 —— `sender` 包 + `cards/`**
   - 入口：`python -m sender`（见 `sender/__main__.py`），复用 `sender/templates.py` 的 `load_templates()` 扫描 `cards/*.json`，文件名（去掉后缀）即 `--template` 参数值。
   - 每个 JSON **必须是完整的 Webhook payload**（最外层含 `msg_type` 和 `card`），不能直接粘贴飞书卡片搭建工具导出的纯 `card` 定义。
   - `${variable}` 与 `repeat` 组件通过 Webhook 发送时**不会被渲染**，新增模板时需先静态化。
   - `apply_vars` 只做 payload 顶层 / `card` 层 / `content` 层的简单字符串替换，不是完整的模板引擎。
   - `--mock` 走 `sender/fixtures.py::mock_payload()`，内部直接调 `build_ai_daily_card`，用来在不依赖真实模板的情况下验证发送链路。

2. **动态构建路径 —— `sender/builder.py` + `sender/core.py` + `categories.py`**
   - `sender.build_ai_daily_card(categories, platform, start_time, end_time)`（在 `sender/builder.py`，从包顶层 re-export）为纯函数：按平台（X / 即刻 / HackerNews…）与时间窗自适应生成标题，并为 `categories` 中每个主题生成一个 `collapsible_panel`。
   - `sender.send_card(webhook_url, payload)`（在 `sender/core.py`）负责实际 HTTP 发送；`FEISHU_WEBHOOK_URL` 通过 `config.get_env()` 读取，同时作为模块级 `WEBHOOK_URL` 导出。
   - `categories.CATEGORY_EMOJI_MAP` 集中维护 7 个预设主题的 emoji（大厂&融资、模型&论文、产品&开源、编程&架构、增长&自媒体、独立开发、观点&争议）；`summarizer/schema.py` 通过 `CATEGORIES_ENUM = list(CATEGORY_EMOJI_MAP.keys())` 从这里派生主题白名单并注入 JSON Schema 的 `enum`。**上游 AI 只输出主题名，不输出 emoji**；无内容的主题不应出现在列表中。
   - `format_time_range()` 自动识别同日/跨日，生成 `YYYY.MM.DD HH - HH` 或跨日格式。
   - `sender.builder` 入口会调用 `contracts.validate_category_groups()` 做运行时校验，避免上游分类结构漂移时静默带错。
   - 生产发送入口：`hourly_bot.py` 按平台分别抓取、总结、构卡和发送。
   - 当前标题展示规则未做平台特化：统一显示**总结后的信息条数**和**抓取时间窗**。

3. **调度路径 —— `delivery.py` + `hourly_bot.py`**
   - `delivery.py` 维护平台调度配置：抓取窗口、执行节奏、最小文章数、发送历史去重窗口。
   - `hourly_bot.py` 按平台分别执行抓取、总结、构卡和发送，不再把多个平台合并成一张卡。
   - `tmp/delivery_state.json` 记录最近已发送 URL，用于跨窗口抓取时避免重复发送。
   - 当前节奏约定：`X` 每 1 小时检查一次但抓取近 24 小时；`Reddit` 每 2 小时检查一次并抓取近 2 小时；`HackerNews` 每天中国时区 `13` 点这一轮检查一次并抓取近 24 小时。

### 数据流水线

```
fetcher/   →  summarizer/  →  sender/builder.py  →  sender/core.py
(按平台周期抓取) (AI 主题分类+摘要)   (组装 payload)       (发送到 webhook)
```

- `fetcher/` 按平台拆文件，统一输出带 `platform / title / url / content / author / published_at` 的原始文章列表，喂给 `summarizer.summarize()`。
  - 主链路共享契约放在 `contracts.py`：`RawArticle`、`CategoryItem`、`CategoryGroup`，以及 `validate_raw_articles()` / `validate_category_groups()` 两个运行时校验函数。
  - `fetcher/hn.py::fetch_hn(hours=24, min_score=50, limit=30)` 已实现：走 Algolia HN Search API（`hn.algolia.com/api/v1/search`），一次请求按 `points` 和 `created_at_i` 过滤，不抓外链正文，`content` 字段直接填 `title`（先跑通链路，后续摘要质量不够再升级到 `trafilatura` 抽原文）。Ask/Show HN 帖子 url 为 null 时会 fallback 到 `news.ycombinator.com/item?id={id}`。
  - `fetcher/x.py::fetch_x(hours=24, since=None, until=None, min_favorites=5, search_min_favorites=25, handle_limit=50, search_limit=200, handles=None, search_terms=None)` 走 Apify `apidojo/tweet-scraper`，同时抓核心账号时间线和关键词搜索；本地再按 `since/until` 精确过滤，解决 actor 的日期级 `start/end` 不够细的问题。字段映射：`text`→`content`（前 60 字 + "..." 作 `title`）、`author.userName`→`@handle`。
  - `fetcher/reddit.py::fetch_reddit(hours=2, min_score=30, limit=40, subreddits=None)` 走 Apify `trudax/reddit-scraper-lite`，按模块级 `_DEFAULT_SUBREDDITS`（AI 相关 sub）拉最新 post，只过滤 `dataType=="post"`；`body` 可能为空（链接帖），fallback 到 `title`。
  - 即刻尚未接入，需要自行逆向 `api.ruguoapp.com` 签名。
- `summarizer/` 已是完整实现：`core.summarize(articles, platform)` 走 OpenAI 兼容 API（`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`），以 `summarizer/prompt.py` 的 system prompt + `summarizer/schema.py` 的 `response_format={"type": "json_schema"}` 约束结构，返回 `[{name, summary, items: [{title, summary}]}]`，即 `build_ai_daily_card` 期望的 `categories` 参数。`summarize()` 会先校验输入文章结构，再校验模型输出结构；空 items 的主题会被过滤掉。
- `summarizer/fixtures.py::mock_articles()` 提供可直接喂给 `summarize` 的样例文章，`python -m summarizer` 会用它跑一遍并打印 JSON。
- 平台节奏约定：`X` 每 1 小时检查一次但抓取近 24 小时；`Reddit` 每 2 小时检查一次并抓取近 2 小时；`HackerNews` 每天中国时区 `13` 点这一轮检查一次并抓取近 24 小时。

### 共享契约的使用方式

- `contracts.py` 是 `fetcher -> summarizer -> builder` 的共享边界定义。
- 新增平台时，目标不是“返回一个差不多能用的 dict 列表”，而是返回满足 `RawArticle` 的数据，并在模块出口调用 `validate_raw_articles()`。
- 调整 prompt 或 schema 时，目标不是“只要模型能返回 JSON 就行”，而是让返回值同时满足 `CategoryGroup` 结构；`summarizer/core.py` 会在返回前调用 `validate_category_groups()`。
- 调整卡片 UI 时，优先修改 `sender/builder.py`，不要要求 `summarizer` 为展示逻辑硬编码额外字段。

## 新增内容的注意事项

- **新静态模板**：放入 `cards/`，保持完整 payload 格式；新增后用 `python -m sender --list` 验证是否被正确加载（解析失败会直接使程序退出）。引用的 `img_key` 需上传到对应飞书租户。
- **扩展动态卡片的主题**：同时更新 `categories.py` 的 `CATEGORY_EMOJI_MAP` 与 README 中的主题表，保持两处一致；`summarizer/schema.py` 的枚举和 `summarizer/prompt.py` 里的主题说明由前者派生/同步，新增主题时记得在 prompt 里补上对应的说明。
- **新增平台 fetcher**：在 `fetcher/` 下新建 `<platform>.py`，暴露一个返回 `list[RawArticle]` 的抓取函数，字段严格对齐 `platform / title / url / content / author / published_at`；返回前调用 `contracts.validate_raw_articles()`；在 `fetcher/__init__.py` 里 re-export，并加一个 `if __name__ == "__main__":` 的独立调试入口（参考 `fetcher/hn.py`）。平台依赖按需加入 `requirements.txt`；目前 Apify 系（X / Reddit）统一复用 `apify-client`。
- **调整平台节奏**：优先修改 `delivery.py`，不要把抓取窗口、发送节奏和标题展示逻辑散落到 `hourly_bot.py` 或各个 `tests/*_e2e.py` 里。
