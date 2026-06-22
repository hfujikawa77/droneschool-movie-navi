#!/usr/bin/env python3
"""catalog.json を埋め込んだ自己完結 index.html を生成する。

塾生はサーバ不要でダブルクリックして検索できる。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = HERE / "catalog.json"
OUT = HERE / "index.html"

TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ドローンエンジニア養成塾 過去チャレンジ検索</title>
<style>
  body{font-family:system-ui,"Hiragino Kaku Gothic ProN",Meiryo,sans-serif;margin:0;background:#f5f6f8;color:#222}
  header{background:#1a3a5c;color:#fff;padding:16px 20px}
  header h1{margin:0;font-size:18px}
  header .sub{font-size:12px;opacity:.8;margin-top:4px}
  .wrap{max-width:980px;margin:0 auto;padding:16px 20px}
  #q{width:100%;padding:12px 14px;font-size:16px;border:1px solid #ccc;border-radius:8px;box-sizing:border-box}
  .tags{margin:12px 0;display:flex;flex-wrap:wrap;gap:6px}
  .tag{font-size:12px;padding:5px 10px;border-radius:14px;border:1px solid #bcd;background:#fff;cursor:pointer;user-select:none}
  .tag.on{background:#1a3a5c;color:#fff;border-color:#1a3a5c}
  .count{font-size:13px;color:#666;margin:8px 0}
  .card{background:#fff;border:1px solid #e2e5ea;border-radius:8px;padding:12px 14px;margin-bottom:10px}
  .card a.t{font-weight:600;color:#13406b;text-decoration:none;font-size:15px}
  .card a.t:hover{text-decoration:underline}
  .meta{font-size:12px;color:#777;margin-top:4px}
  .ctags{margin-top:6px;display:flex;flex-wrap:wrap;gap:4px}
  .ctag{font-size:11px;padding:2px 8px;border-radius:10px;background:#eef3f8;color:#345}
  .preview{margin-top:8px;font-size:13px;line-height:1.55;color:#444}
  .preview .lbl{font-size:11px;color:#888;margin-right:6px}
  .preview .desc{white-space:pre-wrap}
  details.excerpt{margin-top:6px}
  details.excerpt summary{cursor:pointer;font-size:12px;color:#13406b}
  details.excerpt .body{margin-top:4px;color:#555;font-size:13px;line-height:1.6}
  .nosub{font-size:11px;color:#aaa;margin-top:6px}
</style>
</head>
<body>
<header>
  <h1>ドローンエンジニア養成塾 — 過去チャレンジ検索</h1>
  <div class="sub">動画 __N__ 件 / 生成日 __DATE__</div>
</header>
<div class="wrap">
  <input id="q" placeholder="キーワード検索 (例: 非GPS コプター, ローバー, ラズパイ ...)">
  <div class="tags" id="tags"></div>
  <div class="count" id="count"></div>
  <div id="results"></div>
</div>
<script>
const DATA = __DATA__;
const ALL_TAGS = [...new Set(DATA.flatMap(d=>d.tags))];
let active = new Set();
const qEl=document.getElementById('q'), tagsEl=document.getElementById('tags'),
      resEl=document.getElementById('results'), cntEl=document.getElementById('count');

function fmtDate(s){return s&&s.length===8 ? s.slice(0,4)+'-'+s.slice(4,6)+'-'+s.slice(6) : s;}
function render(){
  const terms=qEl.value.toLowerCase().split(/\\s+/).filter(Boolean);
  const rows=DATA.filter(d=>{
    const hay=(d.title+' '+d.description+' '+d.tags.join(' ')).toLowerCase();
    if(!terms.every(t=>hay.includes(t))) return false;
    for(const t of active) if(!d.tags.includes(t)) return false;
    return true;
  });
  cntEl.textContent=rows.length+' 件';
  resEl.innerHTML=rows.map(d=>`<div class="card">
    <a class="t" href="${d.url}" target="_blank" rel="noopener">${esc(d.title)}</a>
    <div class="meta">${fmtDate(d.upload_date)} ・ ${d.view_count} views${d.period?' ・ 第'+d.period+'期':''}${d.course?' コース'+d.course:''}</div>
    <div class="ctags">${d.tags.map(t=>'<span class="ctag">'+esc(t)+'</span>').join('')}</div>
    ${preview(d)}
  </div>`).join('');
}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function preview(d){
  let h='';
  // AI要約があれば最優先、無ければ説明文の冒頭
  if(d.summary) h+='<div class="preview"><span class="lbl">要約</span>'+esc(d.summary)+'</div>';
  else if(d.description) h+='<div class="preview"><span class="lbl">説明</span><span class="desc">'+esc(d.description.slice(0,180))+(d.description.length>180?'…':'')+'</span></div>';
  // 字幕の冒頭抜粋(リンクを開く前に中身を確認できる)
  if(d.transcript_excerpt)
    h+='<details class="excerpt"><summary>字幕プレビュー</summary><div class="body">'+esc(d.transcript_excerpt)+'</div></details>';
  else h+='<div class="nosub">字幕なし</div>';
  return h;
}
tagsEl.innerHTML=ALL_TAGS.map(t=>'<span class="tag" data-t="'+esc(t)+'">'+esc(t)+'</span>').join('');
tagsEl.querySelectorAll('.tag').forEach(el=>el.onclick=()=>{
  const t=el.dataset.t; el.classList.toggle('on');
  if(active.has(t))active.delete(t);else active.add(t); render();
});
qEl.oninput=render; render();
</script>
</body>
</html>
"""


def main() -> None:
    import datetime
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    # description は検索用に保持しつつ HTML 肥大化を抑えるため 400 字で切る
    for d in data:
        d["description"] = (d.get("description") or "")[:400]
    html = (TEMPLATE
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__N__", str(len(data)))
            .replace("__DATE__", datetime.date.today().isoformat()))
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size//1024} KB, {len(data)} videos)")


if __name__ == "__main__":
    main()
