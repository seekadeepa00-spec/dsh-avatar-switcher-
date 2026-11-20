# -*- coding: utf-8 -*-
import io, os, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SECTION = u"""

## 原装 DSH（无 wallpaper-engine 插件）

stock DSH 没有 `/wallpaper-engine/*` 路由，也没有 `~/.dsh-wallpaper-engine` 数据目录。
本仓库的 `plugin/` 是独立插件 `dsh-plugin-avatar-switcher`，它自带一套路由和存储：

| 接口 | 方法 | 作用 |
| --- | --- | --- |
| `/avatar-switcher/state` | GET | 返回 `{"user":名称或null,"ai":名称或null,"dir":头像目录}` |
| `/avatar-switcher/user` | GET/HEAD | 输出「我」的头像 |
| `/avatar-switcher/ai` | GET/HEAD | 输出「助手」的头像 |
| `/avatar-switcher/<side>` | POST | 原样 body 落盘，`content-type` 只收 `image/png`、`image/jpeg`、`image/webp`，上限 8MB |
| `/avatar-switcher/<side>` | DELETE | 删掉该侧头像 |

数据目录：`%USERPROFILE%\\.dsh-avatar-switcher\\avatars`（文件名 `user-<随机>.<ext>` / `ai-<随机>.<ext>`）。

装法（一次）：

```bash
python plugin/install.py
```

它把 `plugin/` 拷进 profile 的 `node_modules/dsh-plugin-avatar-switcher`，并在
`cordis.patch.yml` 追加一行 insert：

```yaml
- insert:
    - id: avatar-switcher
      name: 'dsh-plugin-avatar-switcher'
```

**装完必须重启 DSH**，路由在 boot 时注册，热加载无效（plugin_manager 只认注册表条目）。

换图（重启后）：

```bash
# 换「我」
curl -X POST "http://127.0.0.1:<GUI端口>/avatar-switcher/user" \
     -H "Content-Type: image/png" --data-binary @me.png

# 换「助手」
curl -X POST "http://127.0.0.1:<GUI端口>/avatar-switcher/ai" \
     -H "Content-Type: image/jpeg" --data-binary @bot.jpg

# 验活
python plugin/check.py
```

`check.py` 自己扫 `127.0.0.1` 的 LISTENING 端口，找到真的 GUI 就打印
`GUI port N avatar-switcher LIVE` 加 state 与两侧状态码。

浏览器半边 `lib/client.js` 按行注入头像：用户行（`data-chat-flow-kind="user"` /
`"steering"`）用 `user` 图，助手行（`"assistant-step"`）用 `ai` 图，插在行首
`div.das-avatar`，40px 圆角，配 `MutationObserver` + 4 秒轮询。
"""

targets = [
    r"D:\插件方向\dsh-avatar-skill\SKILL.md",
    r"C:\Users\38354\.dsh\skills\dsh-avatar-switcher\SKILL.md",
]
for p in targets:
    if not os.path.exists(p):
        print("missing", p)
        continue
    s = io.open(p, encoding="utf-8").read()
    if "原装 DSH（无 wallpaper-engine 插件）" in s:
        print("already", p)
        continue
    io.open(p, "w", encoding="utf-8").write(s.rstrip() + SECTION)
    print("appended", p, os.path.getsize(p))
