---
name: dsh-avatar-switcher
description: 换 DSH 桌面端「我」/「助手」的对话头像和大立绘。用户说"改用户头像""换个头像""换成这张图当图标/立绘""把这张设成我的头像"时用；脚本自己找 GUI 端口和插件数据目录，一条命令装上，F5 生效。
---

# DSH 头像切换

一头像一条命令，不用点设置面板。脚本在 `scripts/set_avatar.py`，零依赖（标准库）。

## 先问清楚要改哪个位置

只有三种，问一句话就够，别啰嗦：

1. `user` —— 对话里「我」那侧的头像
2. `ai` —— 对话里「助手」（我）那侧的头像
3. `mascot` —— 大立绘（侧栏/主视觉那张立绘，带显示盒尺寸）

用户只说"换成这张图"，没讲哪个位置 → 问："改你的（助手）还是你的（用户）那侧的头像？还是要做成大立绘？"

## 用户给图之后怎么拿图

- 对话里贴的图：附件实体在 `C:\Users\<你>\.dsh\attachments\v1\objects\<前2位>\<sha256>`，直接把该路径传给 `--image`
- 给了磁盘路径：原样传
- 只有画在画布上的：先用画布截图落到磁盘，再传

图片格式 png/jpg/webp 都吃，带背景整图也直接塞（头像本身就是方的，不抠也行）。

## 执行

```bash
python scripts/set_avatar.py user   --image "<图片路径>"
python scripts/set_avatar.py ai     --image "<图片路径>" --size 64
python scripts/set_avatar.py mascot --image "<图片路径>"
python scripts/set_avatar.py list
```

Windows 上如果 `python` 不在 PATH，用 DSH 自带运行时：
`C:\Users\<你>\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`

脚本自动做四件事：扫本机 LISTENING 端口找到 `/wallpaper-engine/settings` 那个、
定位插件数据目录（默认 `~/.dsh-wallpaper-engine`）、把图规整成 PNG 落到 `avatars/` 或 `mascot/`、
PUT 设置把对应键指过去。最后打印 `GET /avatar/<side>` 的返回码做验证。

## 参数

| 参数 | 用途 |
| --- | --- |
| `--size` | 头像显示 px，默认沿用现有值，常见 56，要更清楚给 64/72 |
| `--box` | 立绘显示盒 `宽x高`，硬上限 96x192；不给按图片比例自动算 |
| `--port` | 手动指定 GUI 端口（自动扫失败时用） |
| `--data-dir` | 手动指定插件数据目录（含 `avatars/`、`mascot/`） |

## 报错怎么处理

- `没找到 GUI 端口` → 桌面端没开；先开 DSH，或让用户看窗口地址栏 `http://127.0.0.1:xxxxx` 传 `--port`
- `找不到 wallpaper-engine 数据目录` → 插件没装；让用户装有 mascot/avatar 的那个壁纸插件，或 `--data-dir` 指过去
- `写入被拒` → 回显里有插件返回的错误，照它改参数（例如立绘盒超了 96x192 会被清成默认）
- 装完头像没变 → 让用户 F5；还不变就 Ctrl+Shift+R 强刷

## 想顺便抠背景

```bash
python scripts/cutout.py --image in.jpg --out out.png --mode detail
python scripts/set_avatar.py user --image out.png
```

`--mode detail` 用于虚焦/渐变/星空类背景，`--mode warm` 用于沙地/木墙/阳光类暖色背景。
`cutout.py` 需要 numpy + Pillow；抠完是 1024 方图，直接给 `set_avatar.py`。

## 交付话术

三行以内：装了什么名字、落在哪个路径、验证返回码。加一句"F5 生效"。

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

数据目录：`%USERPROFILE%\.dsh-avatar-switcher\avatars`（文件名 `user-<随机>.<ext>` / `ai-<随机>.<ext>`）。

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
curl -X POST "http://127.0.0.1:<GUI端口>/avatar-switcher/user"      -H "Content-Type: image/png" --data-binary @me.png

# 换「助手」
curl -X POST "http://127.0.0.1:<GUI端口>/avatar-switcher/ai"      -H "Content-Type: image/jpeg" --data-binary @bot.jpg

# 验活
python plugin/check.py
```

`check.py` 自己扫 `127.0.0.1` 的 LISTENING 端口，找到真的 GUI 就打印
`GUI port N avatar-switcher LIVE` 加 state 与两侧状态码。

浏览器半边 `lib/client.js` 按行注入头像：用户行（`data-chat-flow-kind="user"` /
`"steering"`）用 `user` 图，助手行（`"assistant-step"`）用 `ai` 图，插在行首
`div.das-avatar`，40px 圆角，配 `MutationObserver` + 4 秒轮询。
