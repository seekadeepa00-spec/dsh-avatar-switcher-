# -*- coding: utf-8 -*-
import io, os, shutil, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")

SRC = r"D:\插件方向\dsh-avatar-plugin"
PROFILE = r"C:\Users\38354\.dsh\profiles\desktop\node_modules\dsh-plugin-avatar-switcher"
REPO = r"D:\插件方向\dsh-avatar-skill"
GH = r"D:\编程（日常使用）\github插件\我的skill"
IGN = {".git", "__pycache__", "node_modules", ".pytest_cache"}


def sync(src, dst):
    if not os.path.isdir(dst):
        os.makedirs(dst)
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in IGN]
        rel = os.path.relpath(root, src)
        out = dst if rel == "." else os.path.join(dst, rel)
        if not os.path.isdir(out):
            os.makedirs(out)
        for f in files:
            if f.endswith(".pyc"):
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(out, f))
    return dst


SECTION = u"""

## 最可能被喷的五点，和已经改掉的实现

社区里同类插件已有 30 个（`ANM-Yukang/dsh-avatar`、`BlackRasion/dsh-chat-avatars`、`lhjlol/dsh-whale-avatar` 等），被挑刺的方向非常集中。下面五条是 v2 的实测状态，不是口号。

| 会被喷的点 | 为什么会喷 | v2 的实际做法 |
|---|---|---|
| 写接口没有鉴权 | 浏览器里任何一个恶意网页都能 `POST /avatar-switcher/user` 覆盖你的头像，纯 CSRF | `browserWriteBlocked()`：带 `origin` 或 `sec-fetch-site` 的请求必须携带 `x-avatar-token`，token 落在 `~/.dsh-avatar-switcher/token`（`randomBytes(16)`，mode 0600）；无浏览器头部的本机客户端（curl、桌面 exe）放行。实测 `POST /ai (origin, no tok) -> 401 token-required` |
| 只认 `content-type` | 上传个 `.svg` 或 HTML 谎报 `image/png`，浏览器直出就是 XSS | `sniff()` 读魔数判 png/jpeg/webp，不信头部；响应统一 `x-content-type-options: nosniff`，图片再叠 `content-security-policy: default-src 'none'; style-src 'unsafe-inline'`。实测 `POST /user (svg as png) -> 415 not a real png/jpeg/webp` |
| 硬改宿主布局 | 插 DOM + 改 padding 会被骂"侵入式"，和别的头像插件同装会双头像重叠 | 默认纯 overlay（绝对定位在行外，不动宿主 `padding`）；`[data-das-shift="1"]` 缩进只有用户 `localStorage['das-shift']='1'` 才开；检测到行内已有 `.we-avatar` / `[data-we-avatar-node]` 就撤自己的节点跳过，和 wallpaper-engine 并存不叠图 |
| 轮询把 CPU 吃满 | 4s 定时 + 每次全量 sweep 在长会话里必卡 | 去掉定时轮询，只在 boot / `visibilitychange` / `das:refresh` 事件 / `storage` 变化时拉一次 state；DOM 变更用 `requestIdleCallback`（300ms 超时）去抖；跳过 `data-turn-process-hidden` 折叠行 |
| 无配额无清理 | 反复上传 8MB 图会把 `.dsh-avatar-switcher` 撑爆，用户还找不到垃圾在哪 | 单张 ≤ 8MB，总配额 64MB（超了 `507 quota exceeded`）；每次写入先删同侧旧文件，`GET /state` 直接回 `limits.usedBytes`；`DELETE /avatar-switcher/all` 一键清空两侧 |
| 移动端/暗色不管 | 40px 头像在窄屏上挤掉正文 | `@media (max-width: 640px)` 缩到 32px；头像 `border-radius` 走 `--das-radius` 变量，跟主题走；`alt=""` + `aria-hidden` 不污染读屏 |

自检命令（三秒出结果，不依赖 GUI 是否加载）：

```cmd
"C:\\Users\\38354\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\node\\bin\\node.exe" test-host.mjs
```
"""


def append_section(path):
    txt = ""
    if os.path.isfile(path):
        txt = io.open(path, encoding="utf-8").read()
    if "最可能被喷的五点" in txt:
        return "already %s" % path
    with io.open(path, "a", encoding="utf-8") as f:
        f.write(SECTION)
    return "appended %s %d" % (path, os.path.getsize(path))


def git(cwd, *args):
    p = subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.returncode, (p.stdout or "") + (p.stderr or ""))


print(sync(SRC, PROFILE))
print(sync(SRC, os.path.join(REPO, "plugin")))
print(sync(SRC, os.path.join(GH, "plugin")))
for p in (os.path.join(REPO, "README.md"), os.path.join(REPO, "plugin", "README.md"),
          os.path.join(GH, "README.md"), os.path.join(GH, "plugin", "README.md")):
    print(append_section(p))
for cwd in (REPO, GH):
    git(cwd, "config", "user.name", "maodie")
    git(cwd, "config", "user.email", "maodie@local")
    git(cwd, "add", "-A")
    rc, out = git(cwd, "commit", "-m", "feat(plugin): v2 hardening - csrf token, magic-byte sniff, non-overlay default, no polling, quota")
    print(cwd, "commit rc=%s" % rc, out.strip().splitlines()[0] if out.strip() else "")
    rc, out = git(cwd, "log", "--oneline", "-1")
    print("  head:", out.strip())
