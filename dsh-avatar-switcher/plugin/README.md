# dsh-plugin-avatar-switcher

给 **原装 DeepSeek Harness**（不装 wallpaper-engine 那套插件）也能换「我」/「助手」对话头像的独立插件。

宿主半边注册 `/avatar-switcher/*` 路由并把图片存在 `~/.dsh-avatar-switcher/avatars/`，浏览器半边往聊天行首插一个圆形头像节点，页面每 4 秒拉一次 state 自动刷新。

## 装

```bash
python install.py
```

`install.py` 做两件事：

1. 把本目录拷到 `<profile>/node_modules/dsh-plugin-avatar-switcher`（profile 默认 `~/.dsh/profiles/desktop`）
2. 在 `<profile>/cordis.patch.yml` 里追加一条 insert 行（已有就跳过）

装完**重启 DSH**（关掉窗口再打开），路由才会生效。

## 用

```bash
# 换「我」
curl -X POST --data-binary @"me.png" -H "Content-Type: image/png" http://127.0.0.1:<端口>/avatar-switcher/user

# 换「助手」
curl -X POST --data-binary @"ai.webp" -H "Content-Type: image/webp" http://127.0.0.1:<端口>/avatar-switcher/ai

# 看当前状态 / 删掉头像
curl http://127.0.0.1:<端口>/avatar-switcher/state
curl -X DELETE http://127.0.0.1:<端口>/avatar-switcher/ai
```

端口每次重启都变，用 `check.py` 自己找：

```bash
python check.py
```

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/avatar-switcher/state` | `{"user":"user-xxxx.png","ai":null,"dir":"..."}` |
| GET/HEAD | `/avatar-switcher/user` \| `/ai` | 出图，未设置 404 |
| POST | `/avatar-switcher/user` \| `/ai` | 裸 body，`image/png|jpeg|webp`，≤8MB |
| DELETE | `/avatar-switcher/user` \| `/ai` | 删除该侧 |

## 目录

```
~/.dsh-avatar-switcher/avatars/user-<stamp>.png
~/.dsh-avatar-switcher/avatars/ai-<stamp>.png
```

同名旧文件在写入前会被清掉，`.tmp` + rename 原子落盘。

## 兼容

装了两套插件也不冲突：wallpaper-engine 用 `/wallpaper-engine/avatar/<side>`，本插件用 `/avatar-switcher/<side>`，两边各有自己的样式类。先加载的那套先插节点，后加载的会再插一个，切到其中一套就够用。

## v3 架构：四层适配器 + 失败可见

渲染层不写死。启动时按能力探测降级，探测到哪层就用到哪层：

| 层 | 做法 | 触发条件 |
|---|---|---|
| `css` | 只注入一个 `<style>` + `:root[data-das="on"] .row::before{background-image:url(...)}`，**零 DOM 节点** | `getComputedStyle(row,'::before').backgroundImage` 能读到我们的 URL |
| `dom` | MutationObserver + 空闲去抖，行首插 `div.das-avatar[data-das-node]` | css 探测失败（行被 `overflow:hidden` / `contain:paint` 裁掉时自动跳过该行） |
| `none` | 什么都不做，只在 `/health` 留回执 | 宿主结构完全不认识 |

其它硬规则：

- **内容寻址文件名**：`<side>-<sha256[:12]>.<ext>`，同图重复安装零写入，URL 天然长效缓存。
- **失败可见**：`POST /avatar-switcher/health` 落 `~/.dsh-avatar-switcher/health.json`，`GET /avatar-switcher/state` 回带 `capabilities` / `limits` / `health`；不用 DevTools 也能查当前用的哪层、盯了几行。
- **能力协商**：`GET /state` 里 `capabilities.abi = 1`，客户端按 abi + 层列表选路，不按版本号硬判。
- **绝不拖垮宿主**：`apply()` 整体 try/catch，路由 handler 外层包 Promise catch 回 500 JSON；插件抛错只留日志，不阻断 bootstrap。
- **完整 teardown**：`apply()` 返回 dispose，逆序执行所有清理（样式标签、节点、属性、observer、监听器）。

### 接口表（v3）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/avatar-switcher/state` | `{user, ai, dir, capabilities, limits, health, tokens}` |
| GET | `/avatar-switcher/<user\|ai>` | 出图，`immutable` 缓存 |
| POST | `/avatar-switcher/<user\|ai>` | raw body，需魔数校验；浏览器来源必须带 `x-avatar-token` |
| GET/POST | `/avatar-switcher/health` | 客户端上报渲染层与行数 |
| DELETE | `/avatar-switcher/<side>` | 清单侧 |
| DELETE | `/avatar-switcher/all` | 清两侧 |

## v4 图库存取 / 删除

上传不再覆盖旧图，每一张都留在 `~/.dsh-avatar-switcher/avatars/`，文件名是内容寻址的
`<side>-<sha256前12位>.<ext>` —— 同一张图重复上传不会产生第二份。

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/avatar-switcher/library` | 列出全部历史图 `{items:[{side,name,bytes,mtime,sha,active}], user, ai}` |
| POST | `/avatar-switcher/library/apply` | body `{"name":"user-xxxxxxxxxxxx.png"}` 切回历史图 |
| DELETE | `/avatar-switcher/library/item/<name>` | 删单张；删的正是当前选中的会回落到最新一张 |
| DELETE | `/avatar-switcher/library` | 清空整个图库并取消选中 |
| DELETE | `/avatar-switcher/<user\|ai>` | 只取消选中，图留在库里 |
| POST | `/avatar-switcher/<user\|ai>` | 存图并设为选中，返回 `deduped` 与 `count` |

```cmd
curl -s http://127.0.0.1:PORT/avatar-switcher/library
curl -s -X POST -H "content-type: application/json" -d "{\"name\":\"user-423ecd8faaf9.png\"}" http://127.0.0.1:PORT/avatar-switcher/library/apply
curl -s -X DELETE http://127.0.0.1:PORT/avatar-switcher/library/item/user-423ecd8faaf9.png
curl -s -X DELETE http://127.0.0.1:PORT/avatar-switcher/library
```

选中状态存在 `~/.dsh-avatar-switcher/state.json`（先写 `.tmp` 再 rename，断电不会半截）。
配额 64MB 打满时先淘汰最旧的非选中图；图库条目上限 60。

`GET /state` 的 `capabilities` 现在是 `{abi:2, layers:["css","dom"], contentAddressed:true, library:true}`。
浏览器发起的写请求（带 `origin` / `sec-fetch-site`）必须带 `x-avatar-token`，token 文件路径由 `/state` 的 `tokens.path` 给出。
