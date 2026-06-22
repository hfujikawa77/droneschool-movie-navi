# ドローンエンジニア養成塾 過去チャレンジ検索

チャンネル「ドローンジャパンチャンネル」の全動画(446件)を、塾生がキーワード/カテゴリで
検索できるようにしたツール一式。

## すぐ使う

- **ブラウザ**: `index.html` をダブルクリック → 検索ボックス + タグで絞り込み(サーバ不要)
- **コマンドライン**:
  ```bash
  python3 search.py 非GPS コプター      # キーワード(複数=AND)
  python3 search.py --tag ローバー       # タグで絞り込み
  python3 search.py --period 20         # 第20期
  python3 search.py --list-tags         # タグ一覧と件数
  ```

## カテゴリ(タグ)

| 軸 | タグ |
|----|------|
| 機体種類 | コプター / ローバー / ボート / プレーン / ヘリ / 水中機 |
| 機体サイズ | マイクロ機 / 小型機 / 大型・産業機 |
| チャレンジ種別 | 機体製作(ハード) / プログラムチャレンジ |
| テーマ・用途 | カメラ系 / Web系 / 非GPS / コンパニオン / 自律・ミッション / 障害物回避 / シミュレータ / RTK・高精度測位 / 農業 / 測量・点検 / AI・機械学習 |
| 塾の文脈 | 養成塾(+ 第N期・コースN を自動抽出) |

タグは `categorize.py` の `TAG_RULES`(キーワード辞書)で自動付与。語を足せば精度を調整できる。

### 判定スコープ(過剰タグ対策)
- **機体種類**(`TITLE_SCOPED`)は タイトル+説明文 のみで判定。
  字幕まで見ると講師の雑談的言及(「コプターでもボートでも…」)を拾い過剰タグになるため。
- **サイズ・テーマ・用途**は 字幕込みの全文 で判定(本編内容で初めて分かるため)。

### 手動補正 (`overrides.json`)
キーワードでは拾えない誤タグ(字幕内の願望・雑談的言及など)を動画ID単位で修正する。
自動判定の後に適用される。修正後は `categorize.py` → `build_html.py` を再実行。
```json
{ "<videoId>": { "remove": ["非GPS"], "add": ["カメラ系"] } }
```

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
```

## ファイル

| ファイル | 内容 |
|----------|------|
| `yt_video_urls.txt` | 動画URL一覧(451) |
| `yt_videos.tsv` | id / title / url |
| `metadata.jsonl` | 各動画メタデータ(446、取得不可5件=限定公開/削除) |
| `catalog.json` / `catalog.tsv` | タグ付きカタログ(検索の元データ) |
| `index.html` | 塾生向け検索ページ(自己完結) |
| `transcripts/` | 字幕テキスト(取得した場合) |
