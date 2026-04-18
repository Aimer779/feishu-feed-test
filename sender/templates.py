"""卡片模板加载与变量替换（纯工具函数，不触发 IO）。"""

import copy
import json
from pathlib import Path

CARDS_DIR = Path(__file__).parent.parent / "cards"


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


def load_card_from_file(path: str | Path) -> dict:
    """从 JSON 文件加载卡片配置。"""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"卡片配置文件不存在: {path}")
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def apply_vars(payload: dict, vars: list[str]) -> dict:
    """对 payload 进行简单的变量覆盖（仅支持顶层和第二层字符串替换）。

    返回新的 dict，不修改原对象。
    """
    payload = copy.deepcopy(payload)
    for var in vars:
        if "=" not in var:
            continue
        key, value = var.split("=", 1)
        if key in payload:
            payload[key] = value
        elif isinstance(payload.get("card"), dict) and key in payload["card"]:
            payload["card"][key] = value
        elif isinstance(payload.get("content"), dict) and key in payload["content"]:
            payload["content"][key] = value
    return payload
