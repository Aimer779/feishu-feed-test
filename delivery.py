"""平台推送配置与简单发送历史去重。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class DeliveryConfig:
    key: str
    platform: str
    fetch_hours: int
    cadence_hours: int
    min_articles: int = 5
    dedupe_hours: int | None = None
    trigger_hour_cn: int | None = None
    trigger_minute_cn: int | None = None


PLATFORM_DELIVERY_CONFIGS: dict[str, DeliveryConfig] = {
    "x": DeliveryConfig(
        key="x",
        platform="X",
        fetch_hours=24,
        cadence_hours=1,
        min_articles=5,
        dedupe_hours=24,
    ),
    "reddit": DeliveryConfig(
        key="reddit",
        platform="Reddit",
        fetch_hours=2,
        cadence_hours=2,
        min_articles=5,
        dedupe_hours=6,
    ),
    "hn": DeliveryConfig(
        key="hn",
        platform="HackerNews",
        fetch_hours=24,
        cadence_hours=24,
        min_articles=5,
        dedupe_hours=24,
        trigger_hour_cn=13,
        trigger_minute_cn=10,
    ),
}

_STATE_FILE = Path("tmp/delivery_state.json")


def get_delivery_config(key: str) -> DeliveryConfig:
    return PLATFORM_DELIVERY_CONFIGS[key]


def due_platform_keys(now_cn: datetime) -> list[str]:
    return [
        key
        for key, config in PLATFORM_DELIVERY_CONFIGS.items()
        if _is_due(config, now_cn)
    ]


def _is_due(config: DeliveryConfig, now_cn: datetime) -> bool:
    if config.trigger_hour_cn is not None and now_cn.hour != config.trigger_hour_cn:
        return False
    if config.trigger_minute_cn is not None and now_cn.minute != config.trigger_minute_cn:
        return False
    return now_cn.hour % config.cadence_hours == 0


def load_delivery_state() -> dict[str, dict[str, str]]:
    if not _STATE_FILE.exists():
        return {}
    with _STATE_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def save_delivery_state(state: dict[str, dict[str, str]]) -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def filter_recent_articles(
    state: dict[str, dict[str, str]],
    platform_key: str,
    articles: list[dict],
    now: datetime,
    dedupe_hours: int | None,
) -> list[dict]:
    if dedupe_hours is None:
        return articles

    platform_state = state.get(platform_key, {})
    cutoff = now - timedelta(hours=dedupe_hours)
    pruned_state = {
        url: sent_at
        for url, sent_at in platform_state.items()
        if _parse_timestamp(sent_at) >= cutoff
    }
    state[platform_key] = pruned_state

    filtered = []
    for article in articles:
        url = (article.get("url") or "").strip()
        if url and url in pruned_state:
            continue
        filtered.append(article)
    return filtered


def mark_sent_articles(
    state: dict[str, dict[str, str]],
    platform_key: str,
    articles: list[dict],
    now: datetime,
) -> None:
    platform_state = state.setdefault(platform_key, {})
    sent_at = now.astimezone(timezone.utc).isoformat()
    for article in articles:
        url = (article.get("url") or "").strip()
        if url:
            platform_state[url] = sent_at


def _parse_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
