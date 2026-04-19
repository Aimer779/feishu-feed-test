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
    _ensure_dotenv()
    value = os.getenv(key, "")
    return value if value else default


def require_env(key: str, hint: str | None = None) -> str:
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
    return Config(
        feishu_webhook_url=cli_feishu_webhook_url
        or require_env("FEISHU_WEBHOOK_URL", hint="飞书机器人 Webhook 地址"),
        llm_base_url=cli_llm_base_url
        or get_env("LLM_BASE_URL", "https://api.openai.com/v1"),
        llm_api_key=cli_llm_api_key
        or require_env("LLM_API_KEY", hint="LLM API 密钥"),
        llm_model=cli_llm_model or get_env("LLM_MODEL", "gpt-4o-mini"),
        apify_api_token=cli_apify_api_token
        or require_env("APIFY_API_TOKEN", hint="Apify API Token（抓取 X / Reddit）"),
        log_level=cli_log_level or get_env("LOG_LEVEL", "INFO"),
        log_file=cli_log_file or get_env("LOG_FILE"),
    )
