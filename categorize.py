#!/usr/bin/env python3
"""metadata.jsonl (+ あれば字幕) を対象に、塾の検索軸でタグ付けする。

検索対象テキスト = タイトル + 説明文 + (transcripts/<id>.txt があれば字幕)
出力:
  catalog.tsv  … 1行1動画。タグ列付きの一覧 (表計算/grep 用)
  catalog.json … 検索ツール (search.py / search.html) が読む構造化データ
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
META = HERE / "metadata.jsonl"
TRANSCRIPTS = HERE / "transcripts"
TSV = HERE / "catalog.tsv"
JSON_OUT = HERE / "catalog.json"
OVERRIDES = HERE / "overrides.json"  # 動画IDごとの手動タグ補正

# タグ名 -> 検索キーワード(小文字・部分一致)。日本語/英語/略称を混在で登録。
TAG_RULES: dict[str, list[str]] = {
    # --- 機体種類 ---
    # 「ドローン/drone」は全動画に出るほど汎用なので除外し、機体固有語のみ
    "コプター": ["コプター", "マルチコプター", "クアッド", "quad", "hexa", "ヘキサ",
              "octo", "オクト", "copter", "arducopter", "クアッドコプター",
              "4発", "6発", "8発", "プロペラ機",
              # 代表的なマルチコプター用フレーム名
              "f550", "f450", "s500", "x500", "tarot"],
    "ローバー": ["ローバー", "rover", "ardurover", "走行", "クローラ", "無人車",
              "草刈", "自動草刈"],
    "ボート": ["ボート", "boat", "水上", "船", "asv", "usv"],
    "プレーン": ["プレーン", "plane", "固定翼", "arduplane", "vtol", "テールシッター"],
    "ヘリ": ["ヘリ", "helicopter", "traditional heli"],
    "水中機": ["ardusub", "水中", "rov", "submarine", "潜水"],
    # --- チャレンジ種別 ---
    "機体製作(ハード)": ["機体製作", "自作", "製作", "組み立て", "組立", "組み上げ",
                   "組み上", "初組み", "フレーム", "モーター", "esc", "はんだ",
                   "半田", "配線", "hardware", "ハード", "3dプリント", "基板",
                   # DIYビルド・フレーム名は明確な機体製作シグナル
                   "diy", "ビルド", "機体完成", "完成機", "自作機",
                   "f550", "f450", "s500", "x500", "tarot"],
    "プログラムチャレンジ": ["プログラム", "program", "コード", "code", "スクリプト",
                     "script", "python", "lua", "スクリプティング", "mavlink",
                     "pymavlink", "dronekit", "mavproxy", "アルゴリズム",
                     # フライトモード(自作・新規)はプログラムチャレンジ
                     "フライトモード", "flight mode", "flightmode", "飛行モード",
                     "カスタムモード", "custom mode"],
    # --- テーマ ---
    "カメラ系": ["カメラ", "camera", "映像", "gimbal", "ジンバル", "画像", "vision",
             "opencv", "物体検出", "detection", "認識", "ストリーミング",
             "fpv", "yolo", "セグメンテーション"],
    "Web系": ["web", "ウェブ", "サーバ", "server", "ブラウザ", "html", "api",
            "クラウド", "cloud", "ダッシュボード", "node", "javascript",
            "django", "flask"],
    # マーカー(ArUco/AprilTag)追従はGPS下でも行うため非GPSの判定語にしない
    "非GPS": ["非gps", "non-gps", "nongps", "gpsなし", "gps無し", "gpsレス",
            "屋内", "indoor", "slam", "optical flow", "オプティカルフロー",
            "visual odometry", "vio", "t265", "ビーコン", "uwb"],
    "コンパニオン": ["コンパニオン", "companion", "raspberry", "ラズパイ", "ラズベリー",
              "jetson", "ジェットソン", "rpi", "nvidia", "ros", "ros2",
              "オンボード", "linux"],
    # --- 機体サイズ ---
    # マイクロ機は sub-100g/whoop 級のみ。「ミニコプター(4インチ等)」は小型機へ。
    "マイクロ機": ["マイクロドローン", "マイクロ機", "whoop", "tiny whoop", "27g",
              "100g未満", "100g以下", "sub100g", "sub 100g", "100グラム未満",
              "100グラム以下"],
    "小型機": ["小型機", "小型ドローン", "ミニドローン", "手のひら", "3インチ", "4インチ",
            "5インチ", "コンパクト機", "ミニコプター", "minicopter", "mini copter"],
    "大型/産業機": ["大型機", "産業用", "ペイロード", "重量物", "運搬", "物流", "散布", "農薬"],
    # --- 用途・テーマ(本編から判定) ---
    "自律/ミッション": ["自律", "ミッション", "waypoint", "ウェイポイント", "自動航行", "オートミッション"],
    "障害物回避": ["障害物", "回避", "avoidance", "obstacle", "lidar", "ライダー", "深度カメラ"],
    "シミュレータ": ["sitl", "シミュレーション", "シミュレータ", "gazebo"],
    "RTK/高精度測位": ["rtk", "gnss"],
    "農業": ["農薬", "圃場", "水田", "作物", "農業ドローン", "営農"],
    "測量/点検": ["測量", "点検", "インフラ点検", "オルソ", "マッピング", "3次元計測"],
    "AI/機械学習": ["機械学習", "ディープラーニング", "ニューラル", "物体検出", "yolo", "生成ai", "学習モデル"],
    # --- プロジェクト/チーム ---
    "TAP-J": ["tap-j", "tapj", "tap j"],  # 災害救助コンペ(JIC)等に取り組むTAP-Jチーム
    # 「養成塾」はほぼ全動画に付きフィルタとして機能しないため廃止(期は別途ドロップダウンで絞り込み)
}

# 機体種類・サイズは「この動画の主題」なので タイトル+説明文 のみで判定する。
# (字幕まで見ると講師の雑談的言及を拾い過剰タグになるため)
TITLE_SCOPED = {
    "コプター", "ローバー", "ボート", "プレーン", "ヘリ", "水中機",
    "TAP-J",  # 字幕の雑談的言及は拾わず、タイトル・説明のみで判定
}
# サイズ(マイクロ/小型/大型)はタイトルに出にくいが、識別語が固有で誤検出しにくいので
# 全文(字幕込み)で判定する。
# それ以外(テーマ・用途・塾文脈)は字幕込みの全文で判定する。

# 「第N期」「コースN」抽出用
RE_PERIOD = re.compile(r"第?\s*([０-９0-9]{1,2})\s*期")
RE_COURse = re.compile(r"コース\s*([０-９0-9])")
Z2H = str.maketrans("０１２３４５６７８９", "0123456789")


def load_excluded() -> set[str]:
    """exclude.txt の対象外動画ID(ドローンワイン/ドローン米プロジェクト等)。"""
    ids = set()
    p = HERE / "exclude.txt"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            vid = line.split("#", 1)[0].strip()
            if vid:
                ids.add(vid)
    return ids


def load_meta() -> list[dict]:
    rows = []
    if not META.exists():
        return rows
    excluded = load_excluded()
    for line in META.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("id") not in excluded:
                rows.append(d)
    return rows


def transcript_for(vid: str) -> str:
    p = TRANSCRIPTS / f"{vid}.txt"
    return p.read_text(encoding="utf-8") if p.exists() else ""


RE_URL = re.compile(r"https?://\S+")

# 実機チャレンジではない「トーク系」動画(既定で検索から除外)
TALK_MARKERS = ["ウェビナー", "webinar", "zoom", "インタビュー", "interview", "座談会",
                "mvp", "メッセージ", "めざせ",
                "apdc", "conference",
                "決意発表", "成果発表", "周年", "カリキュラム"]  # 発表・告知系も省略


def is_talk(title: str) -> bool:
    low = title.lower()
    return any(m in low for m in TALK_MARKERS)


def clean_description(desc: str) -> str:
    """表示・検索用に説明文の定型(URL行・ハッシュタグのみの行)を除去する。
    多くの動画で同一の #ドローンエンジニア 等の定型文は情報量が無いため。"""
    out = []
    for line in desc.splitlines():
        s = RE_URL.sub("", line).strip()
        if not s:
            continue
        # ハッシュタグだけの行(# / ＃ で始まるトークンのみ)を除去
        toks = s.split()
        if toks and all(t.startswith("#") or t.startswith("＃") for t in toks):
            continue
        out.append(s)
    return "\n".join(out)


def excerpt(tr: str, n: int = 220) -> str:
    """字幕の冒頭を1行プレビュー用に整形(改行→空白、先頭n文字)。"""
    s = " ".join(tr.split())
    return s[:n] + ("…" if len(s) > n else "")


def tag(title_desc: str, fulltext: str) -> list[str]:
    """TITLE_SCOPED のタグは title+desc のみ、他は全文(字幕込み)で判定。"""
    td = title_desc.lower()
    ft = fulltext.lower()
    hits = []
    for name, kws in TAG_RULES.items():
        hay = td if name in TITLE_SCOPED else ft
        if any(kw.lower() in hay for kw in kws):
            hits.append(name)
    return hits


# --- 既定コプター判定 ---
# 飛行/フライトはコプター・プレーン・ヘリのいずれもあり得るため、飛行=即コプターにはしない。
# 実機(製作/飛行)動画で他の機体種類が特定できない場合のみ、コプターを既定付与する。
OTHER_VEHICLES = {"ローバー", "ボート", "プレーン", "ヘリ", "水中機"}
FLIGHT_WORDS = ["フライト", "飛行", "ホバリング", "ホバ", "離陸", "空撮", "飛ばし", "飛ばす",
                "飛ん", "飛ぶ", "旋回",
                # 飛行モード/デモを表す語(=実機コプターの飛行)
                "loiter", "ロイター", "着陸", "landing", "ドローンショー", "drone show",
                "descent", "降下", "fast decent", "フリップ", "flip", "throw mode",
                "crash recovery", "precision land"]
INTERVIEW_MARKERS = ["インタビュー", "ウェビナー", "webinar", "zoom"]  # 実機動画でないので除外


def default_copter(title: str, tags: list[str], fulltext: str) -> list[str]:
    if "コプター" in tags or any(v in tags for v in OTHER_VEHICLES):
        return tags
    if any(m in title.lower() for m in INTERVIEW_MARKERS):
        return tags  # インタビュー/ウェビナーは対象外
    ft = fulltext.lower()
    if "機体製作(ハード)" in tags or any(w in ft for w in FLIGHT_WORDS):
        return ["コプター"] + tags  # 機体種類なので先頭に
    return tags


def load_overrides() -> dict:
    """手動補正。{ "<videoId>": {"remove": [...], "add": [...], "talk": true|false} } 形式。

    キーワード判定では拾えない誤タグ(字幕内の願望・雑談的言及など)を
    動画単位で除去/追加する。自動判定の後に適用される。
    "talk" を指定すると省略対象フラグを手動で上書きできる。
    """
    if OVERRIDES.exists():
        return json.loads(OVERRIDES.read_text(encoding="utf-8"))
    return {}


def apply_overrides(vid: str, tags: list[str], ov: dict) -> list[str]:
    rule = ov.get(vid)
    if not rule:
        return tags
    out = [t for t in tags if t not in set(rule.get("remove", []))]
    for t in rule.get("add", []):
        if t not in out:
            out.append(t)
    return out


def main() -> None:
    rows = load_meta()
    overrides = load_overrides()
    catalog = []
    for d in rows:
        vid = d.get("id", "")
        title = d.get("title") or ""
        desc = d.get("description") or ""
        tr = transcript_for(vid)
        # 全角スペースを半角化し連続空白を畳んで一致漏れ(例: "Crash　 Recovery")を防ぐ
        norm = lambda s: re.sub(r"[ 　]+", " ", s)
        fulltext = norm("\n".join([title, desc, tr]))
        tags = tag(norm("\n".join([title, desc])), fulltext)
        tags = default_copter(title, tags, fulltext)
        tags = apply_overrides(vid, tags, overrides)

        period = RE_PERIOD.search(title) or RE_PERIOD.search(desc)
        course = RE_COURse.search(title) or RE_COURse.search(desc)

        catalog.append({
            "id": vid,
            "title": title,
            "url": d.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}",
            "upload_date": d.get("upload_date") or "",
            "duration": d.get("duration") or 0,
            "view_count": d.get("view_count") or 0,
            "period": period.group(1).translate(Z2H) if period else "",
            "course": course.group(1).translate(Z2H) if course else "",
            "tags": tags,
            "has_transcript": bool(tr),
            "description": clean_description(desc),
            "transcript_excerpt": excerpt(tr),
            # トーク系(ウェビナー/インタビュー等)= 既定で検索除外。overridesで手動上書き可
            "talk": overrides.get(vid, {}).get("talk", is_talk(title)),
            "summary": "",  # 後でAI要約を入れる枠
        })

    catalog.sort(key=lambda r: r["upload_date"], reverse=True)
    JSON_OUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")

    with TSV.open("w", encoding="utf-8") as fh:
        fh.write("upload_date\tperiod\tcourse\ttags\ttitle\turl\tviews\n")
        for r in catalog:
            fh.write("\t".join([
                r["upload_date"], r["period"], r["course"],
                "|".join(r["tags"]), r["title"], r["url"], str(r["view_count"]),
            ]) + "\n")

    # 集計
    from collections import Counter
    c = Counter(t for r in catalog for t in r["tags"])
    print(f"videos={len(catalog)}  with_transcript={sum(r['has_transcript'] for r in catalog)}")
    print("tag counts:")
    for name in TAG_RULES:
        print(f"  {name:18} {c.get(name,0)}")


if __name__ == "__main__":
    main()
