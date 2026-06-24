#!/usr/bin/env python3
"""動画(.videos/<id>.mp4)から一定間隔でフレームを抽出し、
タイムスタンプ付きのコンタクトシート(グリッド画像)を1枚にまとめる。

機体が映ったフレームを目視/vision で素早く特定するための一覧用。
ffmpeg 不要(cv2 で読み込み)。

使い方: python3 make_contact_sheet.py <videoId> [interval_sec]
出力  : frames/<id>_sheet.jpg  と 抽出フレーム frames/<id>_t<sec>s.jpg
"""
import sys
import cv2
from PIL import Image, ImageDraw

vid = sys.argv[1]
interval = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
COLS = 5
CELL_W = 200  # セル幅(px)

cap = cv2.VideoCapture(f".videos/{vid}.mp4")
fps = cap.get(cv2.CAP_PROP_FPS) or 30
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
dur = total / fps

times = []
t = interval / 2
while t < dur:
    times.append(t)
    t += interval

cells = []
for ts in times:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(ts * fps))
    ok, frame = cap.read()
    if not ok:
        continue
    out = f"frames/{vid}_t{int(ts):03d}s.jpg"
    cv2.imwrite(out, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    # BGR->RGB for PIL
    img = Image.fromarray(frame[:, :, ::-1])
    h = int(img.height * CELL_W / img.width)
    img = img.resize((CELL_W, h))
    d = ImageDraw.Draw(img)
    label = f"{int(ts)}s"
    d.rectangle([0, 0, 46, 16], fill=(0, 0, 0))
    d.text((3, 3), label, fill=(255, 255, 0))
    cells.append(img)
cap.release()

if not cells:
    print("no frames")
    sys.exit(1)

cw, ch = cells[0].size
rows = (len(cells) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * cw, rows * ch), (30, 30, 30))
for i, c in enumerate(cells):
    r, col = divmod(i, COLS)
    sheet.paste(c, (col * cw, r * ch))
sheet_path = f"frames/{vid}_sheet.jpg"
sheet.save(sheet_path, quality=85)
print(f"{vid}: {len(cells)} frames @ {interval}s -> {sheet_path} ({sheet.size[0]}x{sheet.size[1]})")
