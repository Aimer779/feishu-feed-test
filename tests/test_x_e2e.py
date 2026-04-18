import json
import sys
from datetime import datetime, timedelta

from fetcher import fetch_x
from sender import WEBHOOK_URL, build_ai_daily_card, send_card
from summarizer import summarize


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    hours = 1

    print(f"Step 1: fetcher -> X tweets (last {hours}h)")
    articles = fetch_x(hours=hours)
    print(f"Fetched {len(articles)} articles")

    print("\nStep 2: summarizer -> categories")
    categories = summarize(articles, platform="X")
    item_total = sum(len(c.get("items", [])) for c in categories)
    print(f"Generated {len(categories)} categories, {item_total} items total")

    print("\nStep 3: card_builder -> payload")
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    payload = build_ai_daily_card(
        categories,
        platform="X",
        start_time=start_time,
        end_time=end_time,
    )

    preview_path = "tmp/test_x_preview.json"
    with open(preview_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Preview saved to: {preview_path}")

    print(f"\nStep 4: send_card -> {WEBHOOK_URL[:50]}...")
    result = send_card(WEBHOOK_URL, payload)
    print(f"Success: {result}")


if __name__ == "__main__":
    main()
