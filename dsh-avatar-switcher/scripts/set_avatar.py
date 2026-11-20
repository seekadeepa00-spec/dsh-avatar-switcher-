#!/usr/bin/env python3
"""DSH 头像/立绘切换器 —— 把你给的一张图装成「我」或「助手」的头像，或大立绘。

用法：
  python set_avatar.py user   --image "C:\\path\\me.png"
  python set_avatar.py ai     --image "D:\\art.png" --size 64
  python set_avatar.py mascot --image "D:\\art.png"          # 立绘，自动算显示盒
  python set_avatar.py mascot --image "D:\\art.png" --box 96x102
  python set_avatar.py list                                  # 查当前状态
  python set_avatar.py probe                                 # 只找端口和数据目录

零依赖（标准库），Pillow 在位时用来读图尺寸、必要时转 PNG。
"""
import argparse
import io
import json
import os
import random
import re
import shutil
import socket
import string
import subprocess
import sys
import urllib.error
import urllib.request

BASE_PATH = "/wallpaper-engine"
USER_AGENT = "dsh-avatar-switcher/1.0"

AVATAR_RE = re.compile(r"^(user|ai)-[a-z0-9]{4,16}\.(png|jpg|jpeg|webp)$", re.I)
MASCOT_RE = re.compile(r"^mascot-[a-z0-9]{4,16}\.(png|jpg|jpeg|webp)$", re.I)
BOX_MAX_W, BOX_MAX_H = 96, 192


# ---------- 探测 ----------

def listening_ports():
    """本机处于 LISTENING 的 TCP 端口（Windows netstat / *nix ss）。"""
    ports = set()
    try:
        if os.name == "nt":
            out = subprocess.run(["netstat", "-ano"], capture_output=True, timeout=20).stdout
            for line in out.decode("mbcs", "replace").splitlines():
                if "LISTEN" not in line.upper():
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                for tok in parts:
                    if ":" in tok:
                        tail = tok.rsplit(":", 1)[-1]
                        if tail.isdigit():
                            ports.add(int(tail))
                        break
        else:
            out = subprocess.run(["ss", "-ltnH"], capture_output=True, timeout=20).stdout
            for line in out.decode("utf-8", "replace").splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    tail = parts[3].rsplit(":", 1)[-1]
                    if tail.isdigit():
                        ports.add(int(tail))
    except Exception:
        pass
    return sorted(ports)


def http_json(url, timeout=0.6):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def find_gui_port(explicit=None, extra=None):
    """返回提供 wallpaper-engine 路由的端口。"""
    candidates = []
    if explicit:
        candidates.append(int(explicit))
    if extra:
        candidates.extend(int(p) for p in extra)
    candidates.extend([61130, 62615, 54629, 54951])
    candidates.extend(p for p in listening_ports() if p not in candidates)

    seen = set()
    for port in candidates:
        if port in seen:
            continue
        seen.add(port)
        try:
            data = http_json(f"http://127.0.0.1:{port}{BASE_PATH}/settings", 0.5)
        except Exception:
            continue
        if data is None or not isinstance(data, dict):
            continue
        return port
    return None


def find_data_dir(explicit=None):
    """wallpaper-engine 插件数据目录：优先显式，其次 %USERPROFILE%\\.dsh-wallpaper-engine。"""
    if explicit:
        if os.path.isdir(os.path.join(explicit, "avatars")) or os.path.isdir(os.path.join(explicit, "mascot")):
            return explicit
        raise SystemExit(f"--data-dir 里没找到 avatars/mascot 子目录: {explicit}")

    home = os.path.expanduser("~")
    guesses = [
        os.path.join(home, ".dsh-wallpaper-engine"),
        os.path.join(os.environ.get("APPDATA", ""), "dsh-wallpaper-engine"),
        os.path.join(home, ".config", "dsh-wallpaper-engine"),
    ]
    for g in guesses:
        if g and os.path.isdir(g) and (
            os.path.isdir(os.path.join(g, "avatars")) or os.path.isdir(os.path.join(g, "mascot"))
        ):
            return g

    # 兜底：家目录下一层里找带 avatars 或 mascot 的目录
    try:
        for name in os.listdir(home):
            p = os.path.join(home, name)
            if not os.path.isdir(p):
                continue
            if os.path.isdir(os.path.join(p, "avatars")) or os.path.isdir(os.path.join(p, "mascot")):
                return p
    except Exception:
        pass
    raise SystemExit("找不到 wallpaper-engine 数据目录，用 --data-dir 指定（内含 avatars/ 和 mascot/）")


# ---------- 图片处理 ----------

def image_size(path):
    try:
        from PIL import Image
    except Exception:
        return None
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def normalize_image(src, dst_png):
    """有 Pillow 就统一转成 RGBA PNG，顺手把超大的缩到 2048 边长内。"""
    try:
        from PIL import Image
    except Exception:
        shutil.copyfile(src, dst_png)
        return dst_png
    with Image.open(src) as im:
        im = im.convert("RGBA")
        if max(im.size) > 2048:
            f = 2048 / max(im.size)
            im = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))), Image.LANCZOS)
        im.save(dst_png, "PNG", optimize=True)
    return dst_png


def new_stamp():
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))


def auto_box(size):
    """按原图比例算立绘显示盒，夹在 96x192 内。"""
    if not size:
        return f"{BOX_MAX_W}x{int(round(BOX_MAX_W * 1.05))}"
    w, h = size
    bw = BOX_MAX_W
    bh = int(round(bw * h / w))
    if bh > BOX_MAX_H:
        bh = BOX_MAX_H
        bw = int(round(bh * w / h))
    return f"{max(1, min(bw, BOX_MAX_W))}x{max(1, min(bh, BOX_MAX_H))}"


def install_avatar(port, data_dir, side, image, size):
    adir = os.path.join(data_dir, "avatars")
    os.makedirs(adir, exist_ok=True)
    name = f"{side}-{new_stamp()}.png"
    dst = os.path.join(adir, name)
    normalize_image(image, dst)
    if not AVATAR_RE.match(name):
        raise SystemExit("生成的文件名不合规，改 stamp 逻辑")

    patch = {f"avatar{side.capitalize()}Image": name, "avatarEnabled": True}
    if size:
        patch["avatarSize"] = int(size)
    put_settings(port, patch)
    return name, dst


def install_mascot(port, data_dir, image, box):
    mdir = os.path.join(data_dir, "mascot")
    os.makedirs(mdir, exist_ok=True)
    name = f"mascot-{new_stamp()}.png"
    dst = os.path.join(mdir, name)
    normalize_image(image, dst)
    if not MASCOT_RE.match(name):
        raise SystemExit("生成的文件名不合规，改 stamp 逻辑")

    patch = {"mascotImage": name, "mascotImageBox": box or auto_box(image_size(image))}
    put_settings(port, patch)
    return name, dst


# ---------- 设置写入 ----------

def put_settings(port, patch):
    body = json.dumps(patch).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{BASE_PATH}/settings",
        data=body, method="PUT",
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read().decode("utf-8", "replace")
    try:
        res = json.loads(raw)
    except Exception:
        return raw
    if isinstance(res, dict) and res.get("ok") is False:
        raise SystemExit(f"写入被拒: {raw}")
    return res


def get_settings(port):
    try:
        return http_json(f"http://127.0.0.1:{port}{BASE_PATH}/settings", 5) or {}
    except Exception as exc:
        return {"error": str(exc)}


def verify(port, side):
    url = f"http://127.0.0.1:{port}{BASE_PATH}/avatar/{side}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, len(r.read()), r.headers.get("Content-Type")
    except urllib.error.HTTPError as exc:
        return exc.code, 0, exc.headers.get("Content-Type") if exc.headers else None
    except Exception as exc:
        return type(exc).__name__, 0, None


def show(port, data_dir):
    s = get_settings(port)
    if s and "settings" in s:
        s = s["settings"]
    keys = ("avatarEnabled", "avatarSize", "avatarUserImage", "avatarAiImage",
            "mascotImage", "mascotImageBox")
    print(f"port={port}  data_dir={data_dir}")
    for k in keys:
        print(f"  {k:16} = {s.get(k)!r}")
    for side in ("user", "ai"):
        print(f"  GET /avatar/{side:<4} -> {verify(port, side)}")
    for d, pat in (("avatars", AVATAR_RE), ("mascot", MASCOT_RE)):
        full = os.path.join(data_dir, d)
        if os.path.isdir(full):
            files = sorted(f for f in os.listdir(full) if pat.match(f))
            print(f"  {d}/: {files}")


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="DSH 头像 / 立绘切换器")
    ap.add_argument("action", choices=["user", "ai", "mascot", "list", "probe"])
    ap.add_argument("--image", "-i", help="图片路径（png/jpg/webp 都行，也支持带背景的整图）")
    ap.add_argument("--size", type=int, help="头像显示尺寸 px（默认沿用现有，常见 56）")
    ap.add_argument("--box", help="立绘显示盒 宽x高，最大 96x192；不给就按图片比例自动算")
    ap.add_argument("--port", type=int, help="GUI 端口；不给就自动扫")
    ap.add_argument("--data-dir", help="插件数据目录；不给就自动找")
    args = ap.parse_args(argv)

    port = find_gui_port(args.port)
    data_dir = None
    try:
        data_dir = find_data_dir(args.data_dir)
    except SystemExit:
        if args.action not in ("probe",):
            raise
    if not port:
        raise SystemExit("没找到 GUI 端口。先把 DSH 桌面端跑起来，或用 --port 指定。")

    if args.action == "probe":
        print(f"port={port}  data_dir={data_dir}")
        return 0

    if args.action == "list":
        show(port, data_dir)
        return 0

    if not args.image:
        raise SystemExit("缺 --image：给出想要的那张图")
    if not os.path.isfile(args.image):
        raise SystemExit(f"图片不存在: {args.image}")

    if args.action in ("user", "ai"):
        name, dst = install_avatar(port, data_dir, args.action, args.image, args.size)
    else:
        name, dst = install_mascot(port, data_dir, args.image, args.box)

    print(f"installed {name} -> {dst} ({os.path.getsize(dst)} B)")
    show(port, data_dir)
    print("\nGUI 里按 F5 刷新；图标级缓存顽固时用 Ctrl+Shift+R。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
