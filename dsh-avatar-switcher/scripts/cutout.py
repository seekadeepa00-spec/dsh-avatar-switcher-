#!/usr/bin/env python3
"""可选：把带背景的头像图抠成透明 PNG。需要 numpy + Pillow。

两种模式：
  --mode detail  背景是虚化的（室内虚焦、渐变、星空散景）→ 靠高频细节能量分离主体
  --mode warm    背景偏暖/偏亮（沙地、木墙、阳光、米色桌布）→ 靠 r-b 暖度分离主体

用法：
  python cutout.py --image in.jpg --out out.png --mode detail
  python cutout.py --image in.jpg --out out.png --mode warm --pad 0.06 --size 1024
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

SOFT = (0.40, 0.30)  # (起点, 过渡宽度)


def to_img(mask):
    return Image.fromarray((mask * 255).astype(np.uint8), "L")


def to_msk(img):
    return np.asarray(img) > 128


def comps(mask, min_area=200):
    """8 邻域连通域，返回 [(area, ys, xs)]，只留面积达标的。"""
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
    out = []
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        stack = [(y0, x0)]
        seen[y0, x0] = True
        cy, cx = [], []
        while stack:
            y, x = stack.pop()
            cy.append(y)
            cx.append(x)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        if len(cy) >= min_area:
            out.append((len(cy), np.array(cy), np.array(cx)))
    return sorted(out, key=lambda t: -t[0])


def largest(mask):
    cl = comps(mask, 1)
    res = np.zeros_like(mask)
    if cl:
        res[cl[0][1], cl[0][2]] = True
    return res


def hole_fill(mask):
    """从边界灌水，灌不到的封闭区域算主体内部，填上。"""
    inv = ~mask
    h, w = inv.shape
    seed = np.zeros_like(inv)
    seed[0, :] = inv[0, :]
    seed[-1, :] = inv[-1, :]
    seed[:, 0] = inv[:, 0]
    seed[:, -1] = inv[:, -1]
    seen = seed.copy()
    stack = list(zip(*np.nonzero(seed)))
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and inv[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                stack.append((ny, nx))
    return mask | (inv & ~seen)


def mode_detail(rgb):
    hp = np.abs(rgb - np.asarray(Image.fromarray(rgb.astype(np.uint8)).filter(ImageFilter.GaussianBlur(3.0)), float)).mean(-1)
    energy = np.asarray(Image.fromarray(hp.astype(np.uint8)).filter(ImageFilter.GaussianBlur(6.0)), float)
    t = max(np.percentile(energy, 55), 3.0)
    fg = energy > t
    fg = to_msk(to_img(fg).filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.MinFilter(13)))
    fg = largest(fg)
    fg = hole_fill(fg)
    fg = to_msk(to_img(fg).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(9)))
    fg = largest(fg)
    return fg


def mode_warm(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1)
    warm = ((r - b >= 22) & (r >= 70)) | ((r - b >= 18) & (mx < 170))
    fg = (~warm) & (mx > 40)
    fg = to_msk(to_img(fg).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(7)))

    # 行内跨度填充，闭合主体内部空洞（抠掉的脸、衣服缝隙）
    h, w = fg.shape
    span = fg.sum(1)
    rows = np.nonzero(span)[0]
    for y in rows:
        xs = np.nonzero(fg[y])[0]
        if len(xs) < 2:
            continue
        if xs[-1] - xs[0] <= 0.72 * w:
            fg[y, xs[0]:xs[-1] + 1] = True

    fg = hole_fill(fg)
    fg = largest(fg)
    fg = to_msk(to_img(fg).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3)))
    return fg


def main(argv=None):
    ap = argparse.ArgumentParser(description="抠图（numpy + Pillow）")
    ap.add_argument("--image", "-i", required=True)
    ap.add_argument("--out", "-o", required=True)
    ap.add_argument("--mode", choices=["detail", "warm"], default="detail")
    ap.add_argument("--pad", type=float, default=0.04, help="方形留白比例")
    ap.add_argument("--size", type=int, default=1024, help="输出边长")
    args = ap.parse_args(argv)

    im = Image.open(args.image).convert("RGB")
    rgb = np.asarray(im, float)

    fg = mode_detail(rgb) if args.mode == "detail" else mode_warm(rgb)
    if fg.mean() < 0.02:
        raise SystemExit("分割结果几乎是空的，换 --mode 再试")

    alpha = to_msk(to_img(fg).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.2)))
    a = np.asarray(to_img(fg).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.2)), float) / 255.0
    a = np.clip((a - SOFT[0]) / SOFT[1], 0, 1)

    rgba = np.dstack([np.asarray(im), (a * 255).astype(np.uint8)])
    cut = Image.fromarray(rgba, "RGBA")
    bbox = cut.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox:
        cut = cut.crop(bbox)

    side = int(max(cut.size) * (1 + args.pad * 2))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(cut, ((side - cut.width) // 2, (side - cut.height) // 2), cut)
    canvas = canvas.resize((args.size, args.size), Image.LANCZOS)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    canvas.save(args.out, "PNG", optimize=True)
    print(f"cut {cut.size} -> {canvas.size} -> {args.out} ({os.path.getsize(args.out)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
