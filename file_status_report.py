import argparse
import json
import os
from datetime import datetime
from typing import Any, Dict, List

DEFAULT_FILES = [
    "pending_approvals.json",
    "slack_reactions.json",
    "ad_copy_history.json",
]


def format_ts(ts: float) -> str:
    try:
        return datetime.fromtimestamp(ts).isoformat()
    except Exception:
        return "unknown"


def summarize_statuses(entries: List[Dict[str, Any]]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for entry in entries:
        status = entry.get("status", "(missing)")
        summary[status] = summary.get(status, 0) + 1
    return summary


def inspect_file(path: str) -> None:
    print(f"\n=== {path} ===")

    if not os.path.exists(path):
        print("[警告] ファイルが存在しません")
        return

    size = os.path.getsize(path)
    mtime = format_ts(os.path.getmtime(path))
    print(f"パス: {os.path.abspath(path)}")
    print(f"サイズ: {size} bytes")
    print(f"最終更新: {mtime}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"[エラー] JSON読み込みに失敗しました: {exc}")
        return

    if isinstance(data, list):
        print(f"レコード数: {len(data)}")
        status_summary = summarize_statuses(data)
        if status_summary:
            print("ステータス内訳:")
            for status, count in sorted(status_summary.items()):
                print(f"  - {status}: {count}")
        preview = data[:3]
        if preview:
            print("サンプル(最大3件):")
            for idx, row in enumerate(preview, start=1):
                print(f"  [{idx}] {json.dumps(row, ensure_ascii=False)}")
    else:
        print(f"トップレベルの型: {type(data).__name__}")
        print("内容:")
        print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="approval/slackリアクションファイルの状態を確認する簡易ツール"
    )
    parser.add_argument(
        "files",
        nargs="*",
        default=DEFAULT_FILES,
        help="確認するファイルのパス (未指定なら主要ファイルを確認)",
    )
    args = parser.parse_args()

    for path in args.files:
        inspect_file(path)


if __name__ == "__main__":
    main()
