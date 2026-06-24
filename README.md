# ドローンエンジニア養成塾 過去チャレンジ検索

チャンネル「ドローンジャパンチャンネル」の動画を、塾生がキーワード/カテゴリで
検索できるようにしたツール一式。公開サイト: https://hfujikawa77.github.io/droneschool-movie-navi/

- 収録: 約415動画(ドローンワイン/ドローン米プロジェクトは対象外。`exclude.txt`)
- 字幕: 約358件取得済み(本編内容もタグ判定・プレビューに利用)

## すぐ使う

- **ブラウザ**: `index.html` をダブルクリック → 検索ボックス。「絞り込み ▾」で期・タグ等を開閉
  - ウェビナー/インタビュー/座談会/MVP/めざせ 等のトーク系は既定で非表示(チェックで表示)
  - 各カードに説明の冒頭と「字幕プレビュー」を表示(リンクを開く前に中身を確認)
- **コマンドライン**:
  ```bash
  python3 search.py 非GPS コプター      # キーワード(複数=AND)
  python3 search.py --tag ローバー       # タグで絞り込み
  python3 search.py --period 20         # 第20期
  python3 search.py --include-talk      # トーク系も含める(既定は除外)
  python3 search.py --list-tags         # タグ一覧と件数
  ```

## カテゴリ(タグ)

| 軸 | タグ |
|----|------|
| 機体種類 | コプター / ローバー / ボート / プレーン / ヘリ / 水中機 |
| 機体サイズ | マイクロ機(sub-100g級) / 小型機(4インチ等) / 大型・産業機 |
| チャレンジ種別 | 機体製作(ハード) / プログラムチャレンジ |
| テーマ・用途 | カメラ系 / Web系 / 非GPS / コンパニオン / 自律・ミッション / 障害物回避 / シミュレータ / RTK・高精度測位 / 農業 / 測量・点検 / AI・機械学習 |
| プロジェクト | TAP-J(JIC災害救助コンペのTAP-Jチーム) |

タグは `categorize.py` の `TAG_RULES`(キーワード辞書)で自動付与。語を足せば精度を調整できる。
期(第N期)・コース(コースN)はタイトル/説明から自動抽出し、UIのドロップダウンで絞り込み。

### 判定スコープ(過剰タグ対策)
- **機体種類・TAP-J**(`TITLE_SCOPED`)は タイトル+説明文 のみで判定。
  字幕まで見ると講師の雑談的言及(「コプターでもボートでも…」)を拾い過剰タグになるため。
- **サイズ・テーマ・用途**は 字幕込みの全文 で判定(本編内容で初めて分かるため)。
- **既定コプター**: 実機(製作/飛行)動画で他の機体種類が特定できない場合はコプターを既定付与。
  飛行/フライトはプレーン・ヘリの可能性もあるため、それらが付く場合は付与せず、
  インタビュー/ウェビナーも対象外。

### トーク系の省略 (`talk`)
ウェビナー/インタビュー/座談会/MVP/メッセージ/めざせ/APDC/決意発表/成果発表 等の
非チャレンジ動画は `talk` フラグを付け、検索から既定で除外(`TALK_MARKERS`)。

### 手動補正 (`overrides.json`)
キーワードでは拾えない誤タグ(字幕内の願望・雑談的言及など)を動画ID単位で修正する。
自動判定の後に適用される。修正後は `categorize.py` → `build_html.py` を再実行。
```json
{ "<videoId>": { "remove": ["非GPS"], "add": ["コプター"], "talk": true } }
```

### AI要約 (`summaries.json`)
タイトル・説明文・字幕(将来的には画像特徴も)を踏まえたAI要約を動画ID単位で保持する。
`categorize.py` がここから読み込み `catalog.json` の `summary` 欄に反映する(直接編集すると
再生成で消えるため、要約はこのファイルに書く)。`index.html`/`search.py` は `summary` があれば
説明文より優先して表示する。
```json
{ "<videoId>": "AI要約テキスト" }
```
現状は字幕取得・ネットアクセス可能な環境でのみ手動/半自動生成(一部動画のみ試行中)。
サムネイル等の画像特徴を使った要約は、YouTubeへのネットアクセスが必要なため別環境で行う想定。

### 対象外 (`exclude.txt`)
ドローンワイン/ドローン米プロジェクト等の対象外動画ID(1行1ID、`#`コメント可)。
`fetch_metadata.py` / `fetch_subtitles.py` / `categorize.py` が無視する。

## データ生成パイプライン(再構築・更新する場合)

```bash
# 1. チャンネルのURL一覧 (既存: yt_video_urls.txt / yt_videos.tsv)
# 2. 各動画のメタデータ取得 (再開可能・数分)
python3 fetch_metadata.py        # -> metadata.jsonl
# 3. (任意) 日本語字幕の取得 (重い・再開可能) → 検索精度UP
python3 fetch_subtitles.py       # -> transcripts/<id>.txt
# 4. 分類してカタログ生成
python3 categorize.py            # -> catalog.json / catalog.tsv
# 5. 自己完結HTMLを再生成
python3 build_html.py            # -> index.html
# 6. git push すると GitHub Pages が自動で再ビルド
```

## ファイル

| ファイル | 内容 |
|----------|------|
| `yt_video_urls.txt` / `yt_videos.tsv` | 動画URL一覧 / id・title・url |
| `metadata.jsonl` | 各動画メタデータ |
| `exclude.txt` | 対象外動画ID(31件) |
| `overrides.json` | 手動タグ補正・talk上書き |
| `summaries.json` | 動画IDごとのAI要約(字幕+説明+将来は画像特徴) |
| `catalog.json` / `catalog.tsv` | タグ付きカタログ(検索の元データ) |
| `index.html` | 塾生向け検索ページ(自己完結) |
| `assets/` | ロゴ等 |
| `transcripts/` | 字幕テキスト |
