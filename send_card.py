import argparse
import copy
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")
CARDS_DIR = Path(__file__).parent / "cards"


def load_templates(directory: Path = CARDS_DIR) -> dict:
    """从指定目录加载所有 .json 卡片模板。"""
    templates = {}
    if not directory.exists():
        return templates
    for file in sorted(directory.glob("*.json")):
        try:
            templates[file.stem] = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"解析模板失败 {file.name}: {e}") from e
    return templates


def send_card(webhook_url: str, payload: dict) -> dict:
    """发送卡片消息到飞书 webhook。"""
    response = requests.post(
        webhook_url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def load_card_from_file(path: str) -> dict:
    """从 JSON 文件加载卡片配置。"""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"卡片配置文件不存在: {path}")
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_templates(templates: dict):
    """列出所有可用的预定义模板。"""
    print("可用的卡片模板:")
    for name in templates:
        print(f"  - {name}")


def main():
    templates = load_templates()
    template_names = list(templates.keys())

    parser = argparse.ArgumentParser(description="发送飞书卡片消息")
    parser.add_argument(
        "--webhook",
        default=WEBHOOK_URL,
        help="飞书 webhook 地址（默认从 FEISHU_WEBHOOK_URL 环境变量或 .env 文件读取）",
    )
    parser.add_argument(
        "--template",
        "-t",
        choices=template_names if template_names else None,
        default=template_names[0] if template_names else None,
        help="选择预定义的卡片模板",
    )
    parser.add_argument(
        "--file",
        "-f",
        help="从 JSON 文件加载卡片配置（优先级高于 --template）",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="列出所有可用的预定义模板",
    )
    parser.add_argument(
        "--var",
        "-v",
        action="append",
        default=[],
        help="覆盖模板变量，格式为 key=value。可多次使用。",
    )

    args = parser.parse_args()

    if args.list:
        list_templates(templates)
        sys.exit(0)

    # 确定要发送的 payload
    if args.file:
        payload = load_card_from_file(args.file)
    else:
        if not templates:
            print("错误: 未找到任何卡片模板，请检查 cards/ 目录。")
            sys.exit(1)
        payload = copy.deepcopy(templates[args.template])

    # 处理简单的变量覆盖（仅支持顶层和第二层字符串替换）
    for var in args.var:
        if "=" not in var:
            continue
        key, value = var.split("=", 1)
        if key in payload:
            payload[key] = value
        elif isinstance(payload.get("card"), dict) and key in payload["card"]:
            payload["card"][key] = value
        elif isinstance(payload.get("content"), dict) and key in payload["content"]:
            payload["content"][key] = value

    print(f"Sending card to: {args.webhook}")
    try:
        result = send_card(args.webhook, payload)
        print(f"Success: {result}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
