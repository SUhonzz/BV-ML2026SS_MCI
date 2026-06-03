"""Create quick contact sheets for calibration images."""

from __future__ import annotations

import glob
import math
import os

from PIL import Image, ImageDraw


def make_sheet(side: str) -> str:
    files = sorted(glob.glob(f"calib_images/*_{side}.png"))
    thumb_w, thumb_h = 256, 205
    label_h = 24
    thumbs = []

    for path in files:
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h))
        canvas = Image.new("RGB", (thumb_w, thumb_h + label_h), "white")
        canvas.paste(image, ((thumb_w - image.width) // 2, 0))
        label = os.path.basename(path).replace("_20260601_", "_")
        ImageDraw.Draw(canvas).text((4, thumb_h + 4), label, fill=(0, 0, 0))
        thumbs.append(canvas)

    cols = 4
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (240, 240, 240))
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % cols) * thumb_w, (index // cols) * (thumb_h + label_h)))

    out_path = f"_calib_{side.lower()}_contact.jpg"
    sheet.save(out_path, quality=92)
    return out_path


if __name__ == "__main__":
    print(make_sheet("L"))
    print(make_sheet("R"))
