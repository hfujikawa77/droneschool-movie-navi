#!/usr/bin/env python3
"""各動画の日本語字幕(手動優先・無ければ自動字幕)を取得し整形して保存する。

再開可能: transcripts/<id>.txt が既にあればスキップ。
自動字幕の VTT はタイムスタンプ・タグ・ローリング重複行を除去して平文化する。
出力: transcripts/<id>.txt   (取得不可なら transcripts/<id>.none を作りスキップ対象に)
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
URLS = HERE / "yt_video_urls.txt"
OUT = HERE / "transcripts"
OUT.mkdir(exist_ok=True)

RE_VID = re.compile(r"v=([\w-]+)")
RE_TS = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3} -->")
RE_TAG = re.compile(r"<[^>]+>")


def vtt_to_text(vtt: str) -> str:
    lines = []
    prev = None
    for raw in vtt.splitlines():
        s = raw.strip()
        if not s or s == "WEBVTT" or RE_TS.match(s):
            continue
        if s.startswith(("Kind:", "Language:", "NOTE")) or s.isdigit():
            continue
        s = RE_TAG.sub("", s).strip()
        if not s or s == prev:
            continue
        # 自動字幕は前行の続きが重複しがちなので包含チェック
        if prev and (s in prev or prev in s):
            if len(s) > len(prev):
                lines[-1] = s
                prev = s
            continue
        lines.append(s)
        prev = s
    return "\n".join(lines)


def main() -> int:
    urls = [u.strip() for u in URLS.read_text(encoding="utf-8").splitlines() if u.strip()]
    ok = none = skip = 0
    for i, url in enumerate(urls, 1):
        m = RE_VID.search(url)
        vid = m.group(1) if m else url
        if (OUT / f"{vid}.txt").exists() or (OUT / f"{vid}.none").exists():
            skip += 1
            continue
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(
                ["python3", "-m", "yt_dlp", "--skip-download",
                 "--write-subs", "--write-auto-subs",
                 "--sub-langs", "ja,ja-orig,ja-JP,a.ja",
                 "--sub-format", "vtt", "--no-warnings",
                 "-o", f"{td}/%(id)s.%(ext)s", url],
                capture_output=True, text=True, timeout=180,
            )
            vtts = list(Path(td).glob("*.vtt"))
            if not vtts:
                (OUT / f"{vid}.none").write_text("", encoding="utf-8")
                none += 1
            else:
                text = vtt_to_text(vtts[0].read_text(encoding="utf-8"))
                (OUT / f"{vid}.txt").write_text(text, encoding="utf-8")
                ok += 1
        if i % 25 == 0:
            print(f"[{i}/{len(urls)}] ok={ok} none={none} skip={skip}", flush=True)
    print(f"DONE ok={ok} none={none} skip={skip}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
