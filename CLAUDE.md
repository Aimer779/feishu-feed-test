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

# 静态模板发送（CLI 入口）
.venv\Scripts\python.exe send_card.py --list
.venv\Scripts\python.exe send_card.py --template travel
.venv\Scripts\python.exe send_card.py --file my-card.json
.venv\Scripts\python.exe send_card.py --template text --var "text=自定义"

# 动态 AI Daily 卡片（会生成 preview_ai_daily_*.json 并向 webhook 发送示例）
.venv\Scripts\python.exe card_builder.py
```

项目目前没有测试框架或 lint 配置。

## 代码架构

两条并行的发送路径，共享同一个飞书 Webhook：

1. **静态模板路径 —— `send_card.py` + `cards/`**
   - `load_templates()` 在启动时扫描 `cards/*.json`，文件名（去掉后缀）即 `--template` 参数值。
   - 每个 JSON **必须是完整的 Webhook payload**（最外层含 `msg_type` 和 `card`），不能直接粘贴飞书卡片搭建工具导出的纯 `card` 定义。
   - `${variable}` 与 `repeat` 组件通过 Webhook 发送时**不会被渲染**，新增模板时需先静态化。
   - `--var key=value` 只做 payload 顶层 / `card` 层 / `content` 层的简单字符串替换，不是完整的模板引擎。

2. **动态构建路径 —— `card_builder.py`**
   - 核心是 `build_ai_daily_card(categories, platform, start_time, end_time)`，按平台（X / 即刻 / HackerNews…）与时间窗自适应生成标题，并为 `categories` 中每个主题生成一个 `collapsible_panel`。
   - 主题 emoji 通过模块内硬编码的 `CATEGORY_EMOJI_MAP` 映射（7 个预设主题：大厂&融资、模型&论文、产品&开源、编程&架构、增长&自媒体、独立开发、观点&争议）。**上游 AI 只输出主题名，不输出 emoji**；无内容的主题不应出现在列表中。
   - `format_time_range()` 自动识别同日/跨日，生成 `YYYY.MM.DD HH - HH` 或跨日格式。

### 数据流水线（预留接口）

```
fetcher.py  →  summarizer.py  →  card_builder.py
(按平台周期抓取) (AI 主题分类+摘要) (组装+发送卡片)
```

- `fetcher.py` 和 `summarizer.py` 目前**只有 docstring 规范**，没有实现体。新增功能时需遵守文件头中约定的输入/输出结构：
  - `fetcher` 输出带 `platform / title / url / content / author / published_at` 的原始文章列表。
  - `summarizer` 输出 `[{name, summary, items: [{title, summary, source, url}]}]`，即 `card_builder.build_ai_daily_card` 期望的 `categories` 参数。
- 平台抓取周期约定：X 1 小时、即刻 2 小时、HackerNews 24 小时。

## 新增内容的注意事项

- **新静态模板**：放入 `cards/`，保持完整 payload 格式；新增后用 `--list` 验证是否被正确加载（解析失败会直接使程序退出）。引用的 `img_key` 需上传到对应飞书租户。
- **扩展动态卡片的主题**：同时更新 `CATEGORY_EMOJI_MAP` 与 README 中的主题表，保持两处一致。
- **调试卡片视觉**：`card_builder.py` 运行会在项目根目录写出 `preview_ai_daily_*.json`，可用作不发送情况下的 payload 校对（历史预览文件已存在于 `test-file/`，`backup/` 保留 AI Daily 卡片的演进版本）。
