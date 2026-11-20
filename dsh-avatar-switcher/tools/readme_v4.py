# -*- coding: utf-8 -*-
import io, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TARGETS = [
    r"D:\插件方向\dsh-avatar-plugin\README.md",
    r"D:\插件方向\dsh-avatar-skill\plugin\README.md",
    r"D:\编程（日常使用）\github插件\我的skill\plugin\README.md",
    r"C:\Users\38354\Desktop\源代码\README.md",
]

SECTION = """
## v4 图库存取 / 删除

上传不再覆盖旧图，每一张都留在 `~/.dsh-avatar-switcher/avatars/`，文件名是内容寻址的
`<side>-<sha256前12位>.<ext>` —— 同一张图重复上传不会产生第二份。

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/avatar-switcher/library` | 列出全部历史图 `{items:[{side,name,bytes,mtime,sha,active}], user, ai}` |
| POST | `/avatar-switcher/library/apply` | body `{"name":"user-xxxxxxxxxxxx.png"}` 切回历史图 |
| DELETE | `/avatar-switcher/library/item/<name>` | 删单张；删的正是当前选中的会回落到最新一张 |
| DELETE | `/avatar-switcher/library` | 清空整个图库并取消选中 |
| DELETE | `/avatar-switcher/<user\\|ai>` | 只取消选中，图留在库里 |
| POST | `/avatar-switcher/<user\\|ai>` | 存图并设为选中，返回 `deduped` 与 `count` |

```cmd
curl -s http://127.0.0.1:PORT/avatar-switcher/library
curl -s -X POST -H "content-type: application/json" -d "{\\"name\\":\\"user-423ecd8faaf9.png\\"}" http://127.0.0.1:PORT/avatar-switcher/library/apply
curl -s -X DELETE http://127.0.0.1:PORT/avatar-switcher/library/item/user-423ecd8faaf9.png
curl -s -X DELETE http://127.0.0.1:PORT/avatar-switcher/library
```

选中状态存在 `~/.dsh-avatar-switcher/state.json`（先写 `.tmp` 再 rename，断电不会半截）。
配额 64MB 打满时先淘汰最旧的非选中图；图库条目上限 60。

`GET /state` 的 `capabilities` 现在是 `{abi:2, layers:["css","dom"], contentAddressed:true, library:true}`。
浏览器发起的写请求（带 `origin` / `sec-fetch-site`）必须带 `x-avatar-token`，token 文件路径由 `/state` 的 `tokens.path` 给出。
"""

for p in TARGETS:
    if not os.path.exists(p):
        print("missing", p)
        continue
    s = io.open(p, encoding="utf-8").read()
    if "v4 图库存取" in s:
        print("already v4", p)
        continue
    io.open(p, "w", encoding="utf-8", newline="\n").write(s.rstrip() + "\n" + SECTION)
    print("appended", p, len(s) + len(SECTION))
