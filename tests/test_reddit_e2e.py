import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from delivery import get_delivery_config
from fetcher import fetch_reddit
from sender import WEBHOOK_URL, build_ai_daily_card, send_card
from summarizer import summarize


def main():
    config = get_delivery_config("reddit")
    parser = argparse.ArgumentParser(description="Reddit 端到端测试")
    parser.add_argument(
        "--hours",
        type=int,
        default=config.fetch_hours,
        help="抓取窗口（小时），默认 2",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只生成预览，不发 Feishu",
    )
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    hours = args.hours

    print(f"Step 1: fetcher -> Reddit posts (last {hours}h)")
    articles = fetch_reddit(hours=hours)
    print(f"Fetched {len(articles)} articles")

    print("\nStep 2: summarizer -> categories")
    categories = summarize(articles, platform="Reddit")
    item_total = sum(len(c.get("items", [])) for c in categories)
    print(f"Generated {len(categories)} categories, {item_total} items total")

    print("\nStep 3: card_builder -> payload")
    utc_now = datetime.now(timezone.utc)
    cn_tz = timezone(timedelta(hours=8))
    start_time_utc = utc_now - timedelta(hours=hours)
    payload = build_ai_daily_card(
        categories,
        platform="Reddit",
        start_time=start_time_utc.astimezone(cn_tz),
        end_time=utc_now.astimezone(cn_tz),
    )

    preview_path = "tmp/test_reddit_preview.json"
    with open(preview_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Preview saved to: {preview_path}")

    if args.dry_run:
        print("\nDry run mode — card NOT sent.")
        return

    print(f"\nStep 4: send_card -> {WEBHOOK_URL[:50]}...")
    result = send_card(WEBHOOK_URL, payload)
    print(f"Success: {result}")


if __name__ == "__main__":
    main()
