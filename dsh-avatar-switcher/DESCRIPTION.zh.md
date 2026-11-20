# dsh-avatar-switcher — 中文

**给 DeepSeek Harness 换上你自己的头像和助手的头像，随便什么本地图片都行，不依赖 wallpaper-engine 插件。**

原版 DSH 只有账号级的个人资料图。聊天窗口里的头像都是插件渲染的，没装插件就只有占位图形。这个插件补的就是这块：自建图片仓库、自建路由、自建渲染层，原装 DSH 直接可用。

## 一句话简介（GitHub About，350 字符内）

> 给 DeepSeek Harness 换「我」和「助手」的对话头像与立绘，原装可用，不依赖 wallpaper-engine。任意 PNG/JPG/WebP 上传、两侧独立切换、60 张图库、内置去背景、WinForms 桌面切换器，零依赖。

## 它能干什么

**两侧独立**：`user`（你的消息）和 `ai`（助手消息）是两个互不干扰的槽位，各存各的图，随时切换，不影响另一边。

**图片图库**：上传按内容寻址命名（`user-<sha256前12位>.png`），重复传同一张图不会产生副本。用过的图全部留在库里：可以再切回旧图、删掉单张、清空整个库。删掉正被使用的那张，会自动回落到最新的剩余图。库容量 60 张，存储配额 64 MB，满了先淘汰最久未使用的非当前图。

**四层适配器渲染**：客户端先探测宿主支持什么，再挑一层真能出画面的最省方案：
`slot`（宿主插槽 API）→ `css`（声明式伪元素，零注入节点）→ `dom`（叠加节点兜底）→ `none`。
挑完不是信版本号，而是读真实聊天行的计算样式来验证。CSS 层被 `overflow:hidden` 或 paint containment 吃掉时，同一次加载内自动切到 DOM 层。

**不跟别人打架**：某一已经插过头像节点（比如 wallpaper-engine），它就主动让位，不叠第二张。默认模式完全不改行布局，头像画在行框外面；要行内让位就把 `localStorage['das-shift'] = '1'`。

**不轮询**：状态只在挂载时、标签页可见性变化时、`das:refresh` 事件、storage 变化时拉取。DOM 变更用 `requestIdleCallback` 去抖。没有任何定时器在跑。

**干净卸载**：`apply()` 返回 dispose 函数。每个观察器、监听器、注入的 style 标签、属性、节点都登记在 disposer 栈里，逆序回收，禁用或热重载后不留残渣。

**去背景**：两套算法，无模型、无联网、无额外依赖。`detail` 走高频能量，把锐利的角色从虚化背景里分出来；`warm` 走「红减蓝」暖度分割，配行跨度填充与边界灌水补洞，把角色从暖色沙地或墙面前分出来。都输出 1024 px 透明 PNG，并顺带生成多尺寸 `.ico`（16/32/48/64/128/256）。

**桌面 GUI**：`gui/AvatarTool.cs` 单文件 C# 5 WinForms，用 .NET Framework 4 自带的 `csc.exe` 编译，不用 SDK、不用 NuGet。按钮：选图、设为「我」、设为「助手」、设为立绘、检查连接、打开头像目录、去背景、恢复默认。

## 接口

宿主半边挂在 `/avatar-switcher`：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/state` | 当前生效文件名、能力、限额、健康回执 |
| GET | `/library` | 图库全量：side/bytes/mtime/sha/active |
| POST | `/library/apply` | `{"name":"user-abc123.png"}` 切到库里某张 |
| DELETE | `/library/item/<name>` | 删单张 |
| DELETE | `/library` | 清空整个图库 |
| GET | `/user`、`/ai` | 出当前生效的图 |
| POST | `/user`、`/ai` | 上传并设为当前（裸 body，image/png、jpeg、webp） |
| DELETE | `/user`、`/ai` | 取消该侧选中，图留在库里 |
| DELETE | `/all` | 两侧一起取消 |
| GET/POST | `/health` | 渲染层回执：layer、rows、mountedAt、abi |

浏览器发起的写请求（带 `Origin` 或 `Sec-Fetch-Site`）必须带 `x-avatar-token`，与 `~/.dsh-avatar-switcher/token`（0600，16 字节随机）比对。本机非浏览器客户端直接放行。上传按文件魔数校验，不看 `Content-Type`：401 `token-required`、415 `not a real png/jpeg/webp`、507 `quota exceeded`。所有响应都带 `x-content-type-options: nosniff`。

## 安装

```cmd
python install_bundle.py    :: 契约门 -> 拷到 %USERPROFILE%/.dsh/plugins -> 建 junction -> 写进 profile bundles
python check.py             :: 重启后：打印 "avatar-switcher LIVE" 与 /state
node verify-plugin.mjs .    :: 静态契约校验，退出码 0 = PASS
node test-host.mjs          :: 假 webServer 冒烟，数据目录用临时目录
```

`verify-plugin.mjs` 不通过，安装脚本直接拒绝安装。导不出来 apply 的插件会把宿主 bootstrap 干崩，这种坑不值得留。

## 环境要求

- DeepSeek Harness 桌面版 `0.2.2-rc.1`（`dshTarget`），cordis `4.1.0`
- Node `>= 22.5`（宿主半边只用内置模块）
- 宿主暴露 `webServer` 服务
- 走 bundle 式安装：只往 `cordis.patch.yml` 插一行，应用重写 patch 文件时会被抹掉

## 目录

```
plugin/    宿主半边 lib/index.js、浏览器半边 lib/client.js、安装器、契约校验、冒烟
scripts/   set_avatar.py（user|ai|mascot|list|probe）、cutout.py（detail|warm）
gui/       AvatarTool.cs  ->  DSH头像切换器.exe
tools/     开发期脚本：端口探测、同步分发、市场查重、备份
```
