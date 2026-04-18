import json
import sys
from datetime import datetime

from card_builder import build_ai_daily_card
from feishu_client import WEBHOOK_URL, send_card
from summarizer.core import summarize
from summarizer.fixtures import mock_articles

def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print("Step 1: summarizer -> categories")
    articles = mock_articles()
    categories = summarize(articles, platform="X")
    print(f"Generated {len(categories)} categories, {sum(len(c.get('items', [])) for c in categories)} items total")

    print("\nStep 2: card_builder -> payload")
    now = datetime.now()
    payload = build_ai_daily_card(
        categories,
        platform="X",
        start_time=now,
        end_time=now,
    )

    preview_path = "test_send_preview.json"
    with open(preview_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Preview saved to: {preview_path}")

    print(f"\nStep 3: send_card -> {WEBHOOK_URL[:50]}...")
    try:
        result = send_card(WEBHOOK_URL, payload)
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
