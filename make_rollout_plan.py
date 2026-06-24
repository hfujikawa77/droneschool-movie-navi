#!/usr/bin/env python3
"""画像入り AI要約の展開計画(20本/バッチ)を作成・更新する。

対象 : catalog.json のうち talk(=UIで既定省略)でない動画 = 287本想定
除外 : talk:true(ウェビナー/インタビュー等) は対象外
真実 : 実施済み判定は summaries.json に要約があるか(= 単一の真実)

- rollout_plan.json : バッチ割り当て(動画ID→バッチ番号)。一度作ったら固定し、
                      新規動画は既存バッチを崩さず末尾に追加する。
- rollout_plan.md   : 人間用の進捗表(チェックボックス)。summaries.json から
                      毎回再生成するので手動編集しない。

使い方: python3 make_rollout_plan.py   (生成 / 進捗更新)
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = HERE / "catalog.json"
SUMMARIES = HERE / "summaries.json"
PLAN_JSON = HERE / "rollout_plan.json"
PLAN_MD = HERE / "rollout_plan.md"
BATCH_SIZE = 20


def load_json(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def main() -> None:
    catalog = load_json(CATALOG, [])
    summaries = load_json(SUMMARIES, {})

    # 対象 = talk でない動画(catalog.json の並び=投稿日の新しい順 を踏襲)
    targets = [r for r in catalog if not r.get("talk")]
    target_ids = [r["id"] for r in targets]
    meta = {r["id"]: r for r in targets}

    # バッチ割り当て: 既存 rollout_plan.json を尊重し、未割当の動画だけ末尾に追加
    plan = load_json(PLAN_JSON, {"batch_size": BATCH_SIZE, "assignments": {}})
    assign = plan.get("assignments", {})  # id -> batch number(1始まり)
    # 既存割当のうち、もう対象でない(talk化した等)IDは除去
    assign = {vid: b for vid, b in assign.items() if vid in meta}

    assigned_ids = set(assign)
    next_seq = len(assigned_ids)
    for vid in target_ids:  # catalog順で安定
        if vid not in assigned_ids:
            assign[vid] = next_seq // BATCH_SIZE + 1
            assigned_ids.add(vid)
            next_seq += 1

    plan = {"batch_size": BATCH_SIZE, "assignments": assign}
    PLAN_JSON.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    # バッチ番号 -> [id...](catalog順を保つ)
    batches: dict[int, list[str]] = {}
    for vid in target_ids:
        batches.setdefault(assign[vid], []).append(vid)

    done = lambda vid: bool(summaries.get(vid))
    total = len(target_ids)
    total_done = sum(1 for vid in target_ids if done(vid))

    lines = []
    lines.append("# 画像入りAI要約 展開計画(20本/バッチ)\n")
    lines.append(f"- 対象: talk(UI既定で省略)を除く **{total}本**")
    lines.append(f"- 実施済み: **{total_done} / {total}**(`summaries.json` に要約があるもの)")
    lines.append(f"- バッチ数: {len(batches)}(1バッチ={BATCH_SIZE}本)")
    lines.append("- 進捗は `python3 make_rollout_plan.py` で再生成。手動編集しない。")
    lines.append("- 関連: Issue #2\n")
    for b in sorted(batches):
        ids = batches[b]
        bdone = sum(1 for vid in ids if done(vid))
        status = "実施済み" if bdone == len(ids) else ("一部" if bdone else "未済")
        lines.append(f"## バッチ{b:02d}  [{bdone}/{len(ids)}] {status}")
        for vid in ids:
            box = "x" if done(vid) else " "
            title = (meta[vid].get("title") or "").replace("\n", " ")
            date = meta[vid].get("upload_date", "")
            lines.append(f"- [{box}] `{vid}` {date} {title}")
        lines.append("")
    PLAN_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"targets={total} done={total_done} batches={len(batches)} -> {PLAN_MD.name}")


if __name__ == "__main__":
    main()
