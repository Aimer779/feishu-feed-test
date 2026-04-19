# Feishu Card Sender

通过飞书 Webhook 发送多种类型的卡片消息。支持模板化管理和命令行快速发送，以及基于代码动态组装的 AI 资讯卡片推送。

## 已实现功能

- **多模板卡片发送**：内置文本、Markdown、模板卡片、旅游推荐、AI 资讯等多种卡片
- **动态模板加载**：所有静态卡片模板存放于 `cards/` 目录，程序启动时自动扫描加载，无需修改代码即可增删模板
- **动态卡片构建**：通过 `sender` 包按平台、时间范围、主题动态组装飞书卡片，主题数量和子信息数完全自适应
- **AI 资讯工作流**：`fetcher`（信息抓取器，HackerNews / X / Reddit 已接入，即刻待接入）、`summarizer`（信息总结器）、`sender`（消息发送器）三层已打通，可端到端自动生成并推送 AI 资讯卡片
- **统一配置管理**：`config.py` 集中管理所有环境变量，单点 `load_dotenv()`，启动时严格校验必需配置项
- **结构化日志**：基于 loguru 的日志系统，支持彩色终端输出、文件持久化、自动轮转，主链路各阶段带计时埋点
- **灵活的命令行参数**：支持选择模板、加载外部 JSON、自定义 Webhook、简单变量覆盖等
- **虚拟环境管理**：使用 `uv` 进行 Python 虚拟环境创建和依赖安装

## 环境准备

项目使用 [uv](https://github.com/astral-sh/uv) 管理虚拟环境和依赖。

```bash
# 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt
```

## 配置

1. 复制环境变量模板：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入真实的飞书 Webhook 地址：
   ```text
   FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx
   ```

3. 可选：配置日志级别和日志文件持久化：
   ```text
   LOG_LEVEL=INFO          # DEBUG / INFO / WARNING / ERROR，默认 INFO
   LOG_FILE=logs/app.log   # 不设置则仅输出到 stdout
   ```

4. 也可以通过环境变量直接覆盖：

**Windows (PowerShell)**
```powershell
$env:FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
.venv\Scripts\python.exe -m sender
```

**Linux / macOS**
```bash
export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
.venv/bin/python -m sender
```

## 使用方法

### 发送静态模板卡片

**Windows (PowerShell)**
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

**Linux / macOS**
```bash
# 使用默认模板（从 .env 读取 webhook）
.venv/bin/python -m sender

# 使用指定模板
.venv/bin/python -m sender --template travel

# 从外部 JSON 文件加载
.venv/bin/python -m sender --file my-card.json

# 临时覆盖 webhook 地址
.venv/bin/python -m sender --template text --webhook https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx

# 使用 mock payload 发送（用于测试）
.venv/bin/python -m sender --mock
```

### 查看所有可用静态模板

**Windows (PowerShell)**
```powershell
.venv\Scripts\python.exe -m sender --list
```

**Linux / macOS**
```bash
.venv/bin/python -m sender --list
```

### 覆盖模板变量

**Windows (PowerShell)**
```powershell
.venv\Scripts\python.exe -m sender --template text --var "text=自定义消息内容"
```

**Linux / macOS**
```bash
.venv/bin/python -m sender --template text --var "text=自定义消息内容"
```

> 注：`--var` 目前仅支持对 `payload` 顶层、`card` 层或 `content` 层的字符串值进行简单替换。

### 测试 summarizer（调用 LLM 并输出 JSON）

**Windows (PowerShell)**
```powershell
.venv\Scripts\python.exe -m summarizer
```

**Linux / macOS**
```bash
.venv/bin/python -m summarizer
```

### 调试 HackerNews 抓取

**Windows (PowerShell)**
```powershell
# 抓取 24h 内分数 >= 50 的热门 story,打印前 3 条
.venv\Scripts\python.exe -m fetcher.hn
```

**Linux / macOS**
```bash
# 抓取 24h 内分数 >= 50 的热门 story,打印前 3 条
.venv/bin/python -m fetcher.hn
```

### 调试 X / Reddit 抓取

**Windows (PowerShell)**
```powershell
# X：默认抓取近 24h，打印前 5 条
.venv\Scripts\python.exe -m fetcher.x

# Reddit：默认抓取近 2h，打印前 3 条
.venv\Scripts\python.exe -m fetcher.reddit
```

**Linux / macOS**
```bash
# X：默认抓取近 24h，打印前 5 条
.venv/bin/python -m fetcher.x

# Reddit：默认抓取近 2h，打印前 3 条
.venv/bin/python -m fetcher.reddit
```

### 按平台节奏运行定时推送

**Windows (PowerShell)**
```powershell
# 按当前中国时区时间判断哪些平台应该执行
.venv\Scripts\python.exe hourly_bot.py --dry-run

# 只调试某个平台，不发飞书
.venv\Scripts\python.exe hourly_bot.py --only x --dry-run
.venv\Scripts\python.exe hourly_bot.py --only reddit --dry-run
.venv\Scripts\python.exe hourly_bot.py --only hn --dry-run

# 忽略节奏限制，强制检查所有平台
.venv\Scripts\python.exe hourly_bot.py --force --dry-run
```

**Linux / macOS**
```bash
# 按当前中国时区时间判断哪些平台应该执行
.venv/bin/python hourly_bot.py --dry-run

# 只调试某个平台，不发飞书
.venv/bin/python hourly_bot.py --only x --dry-run
.venv/bin/python hourly_bot.py --only reddit --dry-run
.venv/bin/python hourly_bot.py --only hn --dry-run

# 忽略节奏限制，强制检查所有平台
.venv/bin/python hourly_bot.py --force --dry-run
```

当前平台节奏：
- `X`：每 1 小时检查一次，抓取近 24 小时内容，并按发送历史去重
- `Reddit`：每 2 小时检查一次，抓取近 2 小时内容
- `HackerNews`：每天中国时区 `13` 点这一轮检查一次，抓取近 24 小时内容

### 端到端链路测试（summarizer → card_builder → 发送）

**Windows (PowerShell)**
```powershell
# mock 文章版
.venv\Scripts\python.exe tests\test_e2e.py

# 真实 HN 抓取版（fetch_hn → summarize → build → send）
.venv\Scripts\python.exe tests\test_hn_e2e.py

# 真实 X / Reddit 抓取版
.venv\Scripts\python.exe tests\test_x_e2e.py --dry-run
.venv\Scripts\python.exe tests\test_reddit_e2e.py --dry-run
```

**Linux / macOS**
```bash
# mock 文章版
.venv/bin/python tests/test_e2e.py

# 真实 HN 抓取版（fetch_hn → summarize → build → send）
.venv/bin/python tests/test_hn_e2e.py

# 真实 X / Reddit 抓取版
.venv/bin/python tests/test_x_e2e.py --dry-run
.venv/bin/python tests/test_reddit_e2e.py --dry-run
```

### 最小契约测试（fetcher → summarizer → builder）

**Windows (PowerShell)**
```powershell
.venv\Scripts\python.exe tests\test_contracts.py
```

**Linux / macOS**
```bash
.venv/bin/python tests/test_contracts.py
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
fetcher/ (抓取) → summarizer (AI 总结分类) → sender (组装+发送)
```

### 最小统一契约

当前主链路已补上一层轻量契约：`contracts.py`。

- `RawArticle`：约束 `fetcher/` 输出的原始文章结构
- `CategoryItem` / `CategoryGroup`：约束 `summarizer` 输出、`sender.builder` 输入的分类结构
- `validate_raw_articles()`：在各平台 `fetcher` 返回前校验字段是否完整且为字符串
- `validate_category_groups()`：在 `summarizer` 输出和 `sender.builder` 输入处校验分类结构

这层契约的目标不是做重型模型层，而是让后续扩平台、改 prompt、改 schema 时，问题尽量在模块边界就暴露，而不是拖到链路后半段才出错。

### 契约链路图

```text
第三方平台原始响应
        ↓
fetcher/<platform>.py
  - 负责抓取、过滤、字段映射
  - 输出 list[RawArticle]
  - 返回前调用 validate_raw_articles()
        ↓
summarizer/core.py
  - 输入必须是 list[RawArticle]
  - 调 LLM + JSON Schema 约束输出
  - 输出 list[CategoryGroup]
  - 返回前调用 validate_category_groups()
        ↓
sender/builder.py
  - 输入必须是 list[CategoryGroup]
  - 入口再次调用 validate_category_groups()
  - 输出 Feishu webhook payload
        ↓
sender/core.py
  - 发送到 Feishu webhook
```

### 后续接手最常改的入口

#### 1. 新增平台

优先改这些文件：

- `fetcher/<platform>.py`
- `fetcher/__init__.py`
- `delivery.py`
- `README.md`
- `CLAUDE.md`

最小实现步骤：

1. 在 `fetcher/` 下新增 `<platform>.py`
2. 将第三方原始数据映射为 `RawArticle`
3. 在返回前调用 `validate_raw_articles()`
4. 在 `fetcher/__init__.py` 里导出新函数
5. 在 `delivery.py` 配置抓取窗口、节奏、去重窗口
6. 用 `hourly_bot.py --only <platform> --dry-run` 做联调

#### 2. 调整 prompt 或 schema

优先改这些文件：

- `summarizer/prompt.py`
- `summarizer/schema.py`
- `categories.py`

注意点：

- 如果新增主题，必须同时更新 `categories.py` 和 `summarizer/schema.py`
- `summarizer` 输出要继续满足 `CategoryGroup` 契约
- 即使 LLM 返回 JSON 可解析，运行时校验不过也会直接报错

#### 3. 调整卡片结构

优先改这些文件：

- `sender/builder.py`
- `categories.py`

注意点：

- `builder` 只假设输入是合法的 `CategoryGroup`
- 如果卡片要增加平台特化展示，优先在 `builder` 内做，不要反向污染 `summarizer`

### `sender.builder` 核心能力

- **平台差异化**：支持 `X`、`即刻`、`HackerNews` 等不同平台，标题自动显示平台名
- **时间范围自适应**：支持 1 小时、2 小时、24 小时等任意间隔，自动处理跨天场景
  - 同一天：`2026.04.17 16 - 17`
  - 跨天：`2026.04.17 23 - 2026.04.18 01`
- **主题数量自适应**：上游返回几个主题，卡片就生成几个 `collapsible_panel`（0~N 个）
- **子信息数自适应**：每个主题下 1~M 条信息均可正常渲染
- **emoji 硬编码映射**：`categories.py` 维护 `CATEGORY_EMOJI_MAP`，上游 AI 只需输出主题名，无需关心 emoji

### `hourly_bot.py` 调度约定

- 调度配置集中在 `delivery.py`
- `hourly_bot.py` 不再把多个平台合并成一张卡，而是按平台分别抓取、总结、构建、发送
- `tmp/delivery_state.json` 记录最近已发送过的 URL，用于小时级/跨窗口抓取时去重
- 卡片标题仍显示**总结后的信息条数**和**实际抓取时间窗**

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

`fetcher/` 各平台模块输出原始文章列表，字段统一对齐为 `platform / title / url / content / author / published_at`，并在返回前经过 `contracts.validate_raw_articles()` 校验；`summarizer` 调用 AI 后输出如下结构：

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

> 注意：若某主题无文章，则**不应出现在列表中**；AI 输出也**不需要包含 emoji**。`summarizer` 输出和 `sender.builder` 输入会经过 `contracts.validate_category_groups()` 校验。

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
├── fetcher/                    # 信息抓取器（包，按平台拆文件）
│   ├── __init__.py             # 导出 fetch_hn / fetch_x / fetch_reddit()
│   ├── hn.py                   # HackerNews 抓取（Algolia Search API）
│   ├── reddit.py               # Reddit 抓取（Apify）
│   └── x.py                    # X 抓取（Apify）
├── contracts.py                # 主链路最小统一契约与运行时校验
├── config.py                   # 统一配置管理（单点 load_dotenv + 分层校验）
├── logger.py                   # 结构化日志封装（基于 loguru）
├── tests/
│   ├── test_contracts.py       # 最小契约测试
│   ├── test_e2e.py             # mock 文章端到端
│   ├── test_hn_e2e.py          # 真实 HN 抓取端到端
│   ├── test_reddit_e2e.py      # 真实 Reddit 抓取端到端
│   └── test_x_e2e.py           # 真实 X 抓取端到端
├── .venv/                      # Python 虚拟环境（由 uv 创建）
├── requirements.txt            # 项目依赖
├── delivery.py                 # 平台调度配置与发送历史去重
├── categories.py               # 主题与 emoji 映射
├── tmp/                        # 临时输出目录（预览文件、测试产物，已加入 .gitignore）
├── lesson.md                   # 飞书卡片实战经验总结
└── README.md                   # 本文件
```

## 经验参考

项目开发过程中积累的飞书卡片兼容性经验（如 schema 2.0 不支持 `background_style`、`action` 包装层等）已整理在 `lesson.md` 中，可供后续开发参考。
