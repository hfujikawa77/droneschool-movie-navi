#!/usr/bin/env python3
"""塾生向け 過去チャレンジ検索 (CLI)。

使い方:
  python3 search.py 非GPS               # キーワード or タグで全文検索
  python3 search.py コプター カメラ       # 複数語は AND
  python3 search.py --tag 非GPS          # タグ完全一致で絞り込み
  python3 search.py --list-tags          # 使えるタグ一覧と件数
  python3 search.py --period 20          # 第20期
"""
import argparse
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = HERE / "catalog.json"


def load() -> list[dict]:
    if not CATALOG.exists():
        raise SystemExit("catalog.json がありません。先に categorize.py を実行してください。")
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def haystack(r: dict) -> str:
    return " ".join([r["title"], r["description"], " ".join(r["tags"])]).lower()


def main() -> None:
    ap = argparse.ArgumentParser(description="過去チャレンジ検索")
    ap.add_argument("terms", nargs="*", help="キーワード(複数=AND)")
    ap.add_argument("--tag", action="append", default=[], help="タグ完全一致(複数=AND)")
    ap.add_argument("--period", help="期(例: 20)")
    ap.add_argument("--course", help="コース(例: 3)")
    ap.add_argument("--list-tags", action="store_true")
    ap.add_argument("--include-talk", action="store_true",
                    help="ウェビナー/インタビュー/座談会/MVP/メッセージ も含める(既定は除外)")
    args = ap.parse_args()

    rows = load()
    if not args.include_talk:
        rows = [r for r in rows if not r.get("talk")]

    if args.list_tags:
        c = Counter(t for r in rows for t in r["tags"])
        for name, n in c.most_common():
            print(f"{n:4}  {name}")
        return

    res = rows
    for kw in args.terms:
        res = [r for r in res if kw.lower() in haystack(r)]
    for t in args.tag:
        res = [r for r in res if t in r["tags"]]
    if args.period:
        res = [r for r in res if r["period"] == args.period.lstrip("第").rstrip("期")]
    if args.course:
        res = [r for r in res if r["course"] == args.course]

    print(f"=== {len(res)} 件 ===")
    for r in res:
        date = r["upload_date"]
        date = f"{date[:4]}-{date[4:6]}-{date[6:]}" if len(date) == 8 else date
        tags = ",".join(r["tags"])
        print(f"[{date}] {r['title']}")
        print(f"    {r['url']}  tags={tags}")
        prev = r.get("summary") or r.get("transcript_excerpt") or (r.get("description") or "")[:160]
        if prev:
            print(f"    概要: {prev}")


if __name__ == "__main__":
    main()
