import json
import sys
from datetime import datetime, timedelta, timezone

from fetcher import fetch_hn
from sender import WEBHOOK_URL, build_ai_daily_card, send_card
from summarizer import summarize


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    hours = 24

    print(f"Step 1: fetcher -> HN articles (last {hours}h)")
    articles = fetch_hn(hours=hours)
    print(f"Fetched {len(articles)} articles")

    print("\nStep 2: summarizer -> categories")
    categories = summarize(articles, platform="HackerNews")
    item_total = sum(len(c.get("items", [])) for c in categories)
    print(f"Generated {len(categories)} categories, {item_total} items total")

    print("\nStep 3: card_builder -> payload")
    utc_now = datetime.now(timezone.utc)
    cn_tz = timezone(timedelta(hours=8))
    start_time_utc = utc_now - timedelta(hours=hours)
    payload = build_ai_daily_card(
        categories,
        platform="HackerNews",
        start_time=start_time_utc.astimezone(cn_tz),
        end_time=utc_now.astimezone(cn_tz),
    )

    preview_path = "tmp/test_hn_preview.json"
    with open(preview_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Preview saved to: {preview_path}")

    print(f"\nStep 4: send_card -> {WEBHOOK_URL[:50]}...")
    result = send_card(WEBHOOK_URL, payload)
    print(f"Success: {result}")


if __name__ == "__main__":
    main()
