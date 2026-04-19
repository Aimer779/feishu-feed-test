# 配置管理与日志系统强化设计方案

## 背景

### 当前配置管理问题

1. 配置分散在多个模块：`sender/core.py`、`summarizer/core.py`、`fetcher/x.py`、`fetcher/reddit.py`
2. 每个模块都调用 `load_dotenv()`，重复加载
3. 校验逻辑不一致：fetcher 有 `RuntimeError`，sender 在使用处检查，summarizer 无检查
4. 错误提示质量参差不齐
5. 配置项：`FEISHU_WEBHOOK_URL`、`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`、`APIFY_API_TOKEN`

### 当前日志输出问题

1. 全部使用 `print()` 输出，无日志库
2. 无时间戳、无日志级别、无执行耗时
3. 无日志持久化（仅 stdout）
4. 关键链路节点：fetcher 开始/结束、summarizer 调用、card 构建、发送结果
5. `hourly_bot.py` 是主入口，协调整个流程

---

## 1. 新增文件清单

| 文件 | 职责 | 说明 |
|---|---|---|
| `config.py` | 统一配置管理 | 单点 `load_dotenv()`，提供 `load_config()` / `get_env()` / `require_env()` |
| `logger.py` | 结构化日志封装 | 基于 `loguru`，提供 `init_logging()` 和 `get_logger()` |

---

## 2. 需要修改的现有文件及修改要点

### P0 — 主链路（优先实施）

**`hourly_bot.py`**
- 顶部导入 `load_config` 和 `init_logging, get_logger`
- `main()` 开头：调用 `init_logging()` 和 `config = load_config()`
- 移除 `from sender import WEBHOOK_URL`，改用 `config.feishu_webhook_url`
- 所有 `print(...)` 替换为 `log.info/warning/error()`
- `run_platform()` 内增加平台级 `bind`：`plog = log.bind(platform=platform_key)`
- 在 fetcher / summarizer / sender 各阶段前后增加计时埋点
- 异常捕获后使用 `log.exception(...)` 输出完整堆栈和上下文

### P1 — 各子模块（配置去重 + 日志增强）

**`sender/core.py`**
- 移除 `load_dotenv()` 和 `from dotenv import load_dotenv`
- 保留模块级 `WEBHOOK_URL`，改为 `from config import get_env; WEBHOOK_URL = get_env("FEISHU_WEBHOOK_URL", "")`
- `send_card()` 内增加 logger 埋点：开始发送、响应状态、耗时、异常堆栈

**`summarizer/core.py`**
- 移除 `load_dotenv()`
- `os.getenv("LLM_*")` 改为 `from config import get_env`
- **保留参数覆盖机制**：`model or get_env("LLM_MODEL", "gpt-4o-mini")` 等
- `summarize()` 内增加：
  - 调用前：`log.info(f"LLM call start: model={resolved_model}, articles={len(articles)}")`
  - 调用后：解析 `resp.usage` 记录 token 消耗 + `time.time()` 耗时
  - 异常：`log.exception("LLM call failed")`

**`fetcher/x.py`**
- 移除 `load_dotenv()`
- `os.getenv("APIFY_API_TOKEN")` 改为 `get_env("APIFY_API_TOKEN")`
- `fetch_x()` 入口/出口增加 logger：`fetch start/end`、handles/search 数量、过滤前后数量、耗时
- 保留 `RuntimeError`（作为运行时错误，非启动校验）

**`fetcher/reddit.py`**
- 与 `fetcher/x.py` 一致，移除 `load_dotenv()`，增加 `get_logger("fetcher.reddit")` 埋点

**`sender/__main__.py`**
- 移除第 4 行 `import os` 和第 26 行 `os.getenv("FEISHU_WEBHOOK_URL", "")`
- 改为 `from config import get_env; default=get_env("FEISHU_WEBHOOK_URL", "")`
- print 保留或替换为 logger（该模块为 CLI 工具，print 到 stdout 可接受）

### P2 — 测试脚本（渐进式）

**`tests/test_e2e.py`、`tests/test_*_e2e.py`**
- 可暂不修改，保持原有 print
- 如需增强：在 `main()` 开头加 `init_logging()`，print 替换为 `get_logger("tests").info()`
- `from sender import WEBHOOK_URL` 继续兼容（因为 `sender/core.py` 保留了该导出）

---

## 3. 配置校验的时机和策略

### 策略分层

| 层级 | 函数 | 用途 | 校验强度 |
|---|---|---|---|
| 启动校验 | `load_config()` | `hourly_bot.py` 主入口调用 | **严格**：所有必需项存在且非空，否则 `SystemExit` |
| 按需读取 | `require_env(key, hint)` | 独立运行脚本（如 `python -m fetcher.x`） | **运行时失败**：缺失时抛异常并给出 `.env.example` 引导 |
| 安全读取 | `get_env(key, default)` | 有默认值或可选配置 | **静默回退**：如 `LLM_MODEL` 默认 `gpt-4o-mini` |

### 启动时（`hourly_bot.py`）完整校验逻辑

```python
# config.py 中
def load_config(...) -> Config:
    return Config(
        feishu_webhook_url=... or require_env("FEISHU_WEBHOOK_URL", hint="飞书机器人 Webhook..."),
        llm_base_url=... or get_env("LLM_BASE_URL", "https://api.openai.com/v1"),
        llm_api_key=... or require_env("LLM_API_KEY", hint="LLM API 密钥..."),
        llm_model=... or get_env("LLM_MODEL", "gpt-4o-mini"),
        apify_api_token=... or require_env("APIFY_API_TOKEN", hint="Apify Token..."),
        log_level=... or get_env("LOG_LEVEL", "INFO"),
        log_file=... or get_env("LOG_FILE"),
    )
```

### 友好错误提示示例

```
❌ 缺失必需配置项: FEISHU_WEBHOOK_URL
   说明: 飞书机器人 Webhook 地址，用于发送卡片消息
   请在 .env 文件中设置该变量，或导出为环境变量。
   参考: D:\code\self-project\feishu-feed-test\.env.example
```

### 避免重复 `load_dotenv()`

`config.py` 模块内使用一个 `_ENV_LOADED` 标记，确保 `.env` 只被加载一次。其余模块移除自己的 `load_dotenv()`。

---

## 4. 日志埋点的具体位置

### 日志格式（`logger.py`）

```text
# stdout（彩色）
2026-04-19 17:52:13 | INFO     | hourly_bot:run_platform:51 - [platform=x] Fetching X: hours=24, handles=12, search_terms=2

# 文件（如果启用 LOG_FILE）
2026-04-19 17:52:13 | INFO     | hourly_bot:run_platform:51 - [platform=x] Fetching X: hours=24, handles=12, search_terms=2
```

### 埋点清单

| 模块 | 位置 | 日志内容 | 级别 |
|---|---|---|---|
| **hourly_bot** | `main()` 入口 | `AI hourly bot started, platforms: [x, reddit]` | INFO |
| | `main()` 调度前 | `Current CN hour: ..., due platforms: ...` | INFO |
| | `run_platform()` fetch 前 | `[platform=x] Step: fetcher start, window=24h` | INFO |
| | `run_platform()` fetch 后 | `[platform=x] Fetched N articles in 8.2s (raw=150, kept=45)` | INFO |
| | `run_platform()` dedupe 后 | `[platform=x] After dedupe filter: M articles` | INFO |
| | `run_platform()` 文章不足 | `[platform=x] Too few articles (3 < 5), skipping` | WARNING |
| | `run_platform()` summarizer 前 | `[platform=x] Step: summarizer start` | INFO |
| | `run_platform()` summarizer 后 | `[platform=x] Generated 4 categories, 12 items in 4.1s` | INFO |
| | `run_platform()` builder 后 | `[platform=x] Card payload built` | INFO |
| | `run_platform()` send 前 | `[platform=x] Step: sender start` | INFO |
| | `run_platform()` send 后 | `[platform=x] Card sent, msg_id=...` | INFO |
| | `run_platform()` 异常 | `[platform=x] Platform run failed` + 堆栈 | ERROR |
| | `main()` 出口 | `AI hourly bot finished, saved state` | INFO |
| **fetcher/x** | `fetch_x()` 入口 | `Fetching X: hours=24...` | INFO |
| | handles 抓取后 | `[handles] fetched 80 raw, kept 25 after filter` | INFO |
| | search 抓取后 | `[search] fetched 200 raw, kept 30 after filter` | INFO |
| | `fetch_x()` 出口 | `Fetched 55 articles from X in 12.3s` | INFO |
| | `_run_actor()` 异常 | `Apify actor call failed: ...` | ERROR |
| **fetcher/reddit** | `fetch_reddit()` 入口/出口 | 类似 x | INFO |
| **summarizer** | `summarize()` 入口 | `LLM call start: model=gpt-4o-mini, articles=12` | INFO |
| | `summarize()` 出口 | `LLM call completed in 3.8s, tokens: prompt=2042, completion=890, total=2932` | INFO |
| | `summarize()` 异常 | `LLM call failed after 5.2s: ...` | ERROR |
| **sender** | `send_card()` 入口 | `Sending card to Feishu webhook...` | INFO |
| | `send_card()` 成功 | `Card sent successfully, status=200` | INFO |
| | `send_card()` 异常 | `Failed to send card: ...` | ERROR |

### Token 消耗埋点

```python
# summarizer/core.py
usage = resp.usage
if usage:
    log.info(
        f"LLM call completed in {elapsed:.2f}s, "
        f"tokens: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}"
    )
```

---

## 5. 向后兼容性考虑

| 现有行为 | 兼容策略 |
|---|---|
| `summarizer.summarize(articles, platform, model=..., base_url=..., api_key=...)` | **保留**。参数优先级仍最高，内部改为 `api_key or get_env("LLM_API_KEY")` |
| `sender.send_card(webhook_url, payload)` | **保留**。签名不变，增加内部 logger |
| `from sender import WEBHOOK_URL` | **保留**。`sender/core.py` 仍导出该变量，改为 `get_env("FEISHU_WEBHOOK_URL", "")` |
| `python -m sender --webhook ...` | **保留**。CLI 参数优先逻辑不变 |
| `python -m fetcher.x` 独立运行 | **保留**。运行时若 `APIFY_API_TOKEN` 缺失仍抛 `RuntimeError` |
| 各测试脚本 `tests/*.py` | **零改动仍可运行**。`.env` 仍会被 `config.py` 自动加载 |
| 现有 `print` 输出 | **主链路替换，子模块渐进**。测试脚本的 print 暂时保留 |

---

## 6. 依赖变更（`requirements.txt`）

```text
lark-oapi>=1.4.8
requests>=2.31.0
python-dotenv>=1.0.0
openai>=1.50.0
apify-client>=1.8.0
loguru>=0.7.0          # 新增：结构化日志
```

无需其他变更。`loguru` 是单文件纯 Python，零配置即可彩色输出，支持自动文件轮转。

---

## 7. 实现优先级

| 优先级 | 内容 | 预计影响面 |
|---|---|---|
| **P0** | 1. 新增 `config.py`（统一配置读取 + 校验）<br>2. 新增 `logger.py`（loguru 封装）<br>3. 修改 `hourly_bot.py`（完整配置校验 + 全链路日志） | 主入口文件 1 个，新增 2 个模块 |
| **P1** | 4. 修改 `sender/core.py`（移除 `load_dotenv`，保留 `WEBHOOK_URL`，增加 send 日志）<br>5. 修改 `summarizer/core.py`（移除 `load_dotenv`，保留参数覆盖，增加 LLM 耗时/token 日志）<br>6. 修改 `fetcher/x.py` 和 `fetcher/reddit.py`（移除 `load_dotenv`，增加抓取耗时日志）<br>7. 修改 `sender/__main__.py`（移除独立 `os.getenv`，改为 `get_env`） | 4 个核心模块 |
| **P2** | 8. 修改 `tests/test_e2e.py`、`test_*_e2e.py`（可选，替换 print 为 logger）<br>9. 添加 `LOG_FILE` 环境变量支持并验证文件持久化<br>10. 更新 `CLAUDE.md` 记录新的配置/日志约定 | 测试脚本 + 文档 |

---

## 附：`config.py` 与 `logger.py` 核心草案

### `config.py`

```python
"""Unified configuration management.

Priority: CLI args > environment variables > defaults
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_ENV_LOADED = False


def _ensure_dotenv() -> None:
    global _ENV_LOADED
    if not _ENV_LOADED:
        load_dotenv()
        _ENV_LOADED = True


def get_env(key: str, default: str | None = None) -> str | None:
    """安全读取环境变量，空字符串视为未设置。"""
    _ensure_dotenv()
    value = os.getenv(key, "")
    return value if value else default


def require_env(key: str, hint: str | None = None) -> str:
    """强制读取环境变量，缺失时友好退出。"""
    value = get_env(key)
    if value:
        return value
    lines = [f"❌ 缺失必需配置项: {key}"]
    if hint:
        lines.append(f"   说明: {hint}")
    lines.append("   请在 .env 文件中设置该变量，或导出为环境变量。")
    example = Path(".env.example")
    if example.exists():
        lines.append(f"   参考: {example.resolve()}")
    raise SystemExit("\n".join(lines))


@dataclass(frozen=True)
class Config:
    feishu_webhook_url: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    apify_api_token: str
    log_level: str = "INFO"
    log_file: str | None = None


def load_config(
    cli_feishu_webhook_url: str | None = None,
    cli_llm_base_url: str | None = None,
    cli_llm_api_key: str | None = None,
    cli_llm_model: str | None = None,
    cli_apify_api_token: str | None = None,
    cli_log_level: str | None = None,
    cli_log_file: str | None = None,
) -> Config:
    """主入口启动时调用：一次性校验所有必需配置，快速失败。"""
    return Config(
        feishu_webhook_url=cli_feishu_webhook_url or require_env(
            "FEISHU_WEBHOOK_URL", hint="飞书机器人 Webhook 地址"
        ),
        llm_base_url=cli_llm_base_url or get_env("LLM_BASE_URL", "https://api.openai.com/v1"),
        llm_api_key=cli_llm_api_key or require_env("LLM_API_KEY", hint="LLM API 密钥"),
        llm_model=cli_llm_model or get_env("LLM_MODEL", "gpt-4o-mini"),
        apify_api_token=cli_apify_api_token or require_env(
            "APIFY_API_TOKEN", hint="Apify API Token（抓取 X / Reddit）"
        ),
        log_level=cli_log_level or get_env("LOG_LEVEL", "INFO"),
        log_file=cli_log_file or get_env("LOG_FILE"),
    )
```

### `logger.py`

```python
"""Structured logging based on loguru."""

import sys

from loguru import logger

__all__ = ["init_logging", "get_logger"]


def init_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """应用启动时调用一次。默认 stdout，可选文件持久化。"""
    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )
    if log_file:
        logger.add(
            log_file,
            level=level,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} - {message}"
            ),
            rotation="1 day",
            retention="7 days",
            encoding="utf-8",
        )


def get_logger(name: str | None = None):
    """获取带名称的 logger，支持 bind 上下文。"""
    if name:
        return logger.bind(logger_name=name)
    return logger
```

---

## 设计原则

- **最小侵入性**：不破坏任何现有函数签名，保留 `summarizer.summarize` 的参数覆盖和 `sender.WEBHOOK_URL` 导出，测试脚本零改动即可继续运行。
- **渐进式迁移**：先改主链路（`hourly_bot.py`），再改子模块，最后改测试脚本。
- **快速失败**：启动时一次性校验所有必需配置，缺失时给出 `.env.example` 引导。
- **清晰可追踪**：通过 `log.bind(platform=...)` 和耗时埋点，使单次推送的完整链路可追踪。
