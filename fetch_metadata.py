#!/usr/bin/env python3
"""各動画のメタデータ(description等)を取得して metadata.jsonl に追記する。

再開可能: 既に metadata.jsonl にある id はスキップする。
入力 : yt_video_urls.txt (1行1URL)
出力 : metadata.jsonl (1行1動画のJSON)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
URLS = HERE / "yt_video_urls.txt"
OUT = HERE / "metadata.jsonl"

# yt-dlp に取得させるフィールド (JSON dict で1行出力)
FIELDS = "%(.{id,title,description,upload_date,duration,view_count,like_count,tags,categories,webpage_url})j"


def video_id(url: str) -> str:
    m = re.search(r"v=([\w-]+)", url)
    return m.group(1) if m else url


def done_ids() -> set[str]:
    ids = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ids.add(json.loads(line)["id"])
            except (json.JSONDecodeError, KeyError):
                pass
    return ids


def excluded_ids() -> set[str]:
    """exclude.txt の対象外動画ID(ドローンワイン/ドローン米プロジェクト等)。"""
    ids = set()
    p = HERE / "exclude.txt"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            vid = line.split("#", 1)[0].strip()
            if vid:
                ids.add(vid)
    return ids


def main() -> int:
    urls = [u.strip() for u in URLS.read_text(encoding="utf-8").splitlines() if u.strip()]
    have = done_ids()
    skip = excluded_ids()
    todo = [u for u in urls if video_id(u) not in have and video_id(u) not in skip]
    print(f"total={len(urls)} done={len(have)} excluded={len(skip)} todo={len(todo)}", flush=True)

    ok = fail = 0
    with OUT.open("a", encoding="utf-8") as fh:
        for i, url in enumerate(todo, 1):
            vid = video_id(url)
            try:
                res = subprocess.run(
                    ["python3", "-m", "yt_dlp", "--skip-download",
                     "--no-warnings", "--print", FIELDS, url],
                    capture_output=True, text=True, timeout=120,
                )
            except subprocess.TimeoutExpired:
                print(f"[{i}/{len(todo)}] {vid} TIMEOUT", flush=True)
                fail += 1
                continue
            out = res.stdout.strip()
            if res.returncode != 0 or not out:
                print(f"[{i}/{len(todo)}] {vid} ERR rc={res.returncode} {res.stderr.strip()[:120]}", flush=True)
                fail += 1
                continue
            # --print は複数行出る可能性があるので最初のJSON行を採用
            for ln in out.splitlines():
                ln = ln.strip()
                if ln.startswith("{"):
                    fh.write(ln + "\n")
                    fh.flush()
                    ok += 1
                    break
            if i % 25 == 0:
                print(f"[{i}/{len(todo)}] ok={ok} fail={fail}", flush=True)

    print(f"DONE ok={ok} fail={fail} total_in_file={len(done_ids())}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
