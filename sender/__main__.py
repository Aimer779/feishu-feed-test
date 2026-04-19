import argparse
import copy
import json
import sys

from config import get_env

from .core import send_card
from .fixtures import mock_payload
from .templates import apply_vars, load_card_from_file, load_templates


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
        default=get_env("FEISHU_WEBHOOK_URL", ""),
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
    parser.add_argument(
        "--mock",
        action="store_true",
        help="使用 mock payload 发送（用于测试）",
    )

    args = parser.parse_args()

    if args.list:
        list_templates(templates)
        sys.exit(0)

    # 确定要发送的 payload
    if args.mock:
        payload = mock_payload()
    elif args.file:
        payload = load_card_from_file(args.file)
    else:
        if not templates:
            print("错误: 未找到任何卡片模板，请检查 cards/ 目录。")
            sys.exit(1)
        payload = copy.deepcopy(templates[args.template])

    payload = apply_vars(payload, args.var)

    if not args.webhook:
        print("错误: 未指定 webhook 地址，请通过 --webhook 或 FEISHU_WEBHOOK_URL 环境变量设置。")
        sys.exit(1)

    print(f"Sending card to: {args.webhook}")
    try:
        result = send_card(args.webhook, payload)
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
