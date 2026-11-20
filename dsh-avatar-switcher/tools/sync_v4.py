import os, shutil, subprocess, sys, io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"D:\插件方向\dsh-avatar-plugin"
TARGETS = [
    r"C:\Users\38354\.dsh\plugins\dsh-avatar-switcher",
    r"D:\插件方向\dsh-avatar-skill\plugin",
    r"D:\编程（日常使用）\github插件\我的skill\plugin",
    r"C:\Users\38354\Desktop\源代码",
]
FILES = [
    ("lib/index.js", "lib/index.js"),
    ("lib/client.js", "lib/client.js"),
    ("verify-plugin.mjs", "verify-plugin.mjs"),
    ("install_bundle.py", "install_bundle.py"),
    ("test-host.mjs", "test-host.mjs"),
]

READMES = [
    r"D:\插件方向\dsh-avatar-plugin\README.md",
    r"D:\插件方向\dsh-avatar-skill\plugin\README.md",
    r"D:\编程（日常使用）\github插件\我的skill\plugin\README.md",
    r"C:\Users\38354\Desktop\源代码\README.md",
]
SECTION = """

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
| GET | `/avatar-switcher/<user\\|ai>` | 出图，`immutable` 缓存 |
| POST | `/avatar-switcher/<user\\|ai>` | raw body，需魔数校验；浏览器来源必须带 `x-avatar-token` |
| GET/POST | `/avatar-switcher/health` | 客户端上报渲染层与行数 |
| DELETE | `/avatar-switcher/<side>` | 清单侧 |
| DELETE | `/avatar-switcher/all` | 清两侧 |
"""

NUKE = "\n## 接口表\n"


def patches():
    for p in READMES:
        if not os.path.exists(p):
            print("readme missing:", p)
            continue
        s = io.open(p, encoding="utf-8").read()
        if "四层适配器" in s:
            print("readme already v3:", p)
            continue
        # 去掉旧接口表段落（到文件末尾或下一个二级标题），再追加 v3 段
        idx = s.find(NUKE)
        if idx != -1:
            s = s[:idx]
        s = s.rstrip() + SECTION
        io.open(p, "w", encoding="utf-8").write(s)
        print("readme v3 ->", p, len(s))


def sync():
    for t in TARGETS:
        if not os.path.isdir(t):
            print("skip missing target:", t)
            continue
        for rel_src, rel_dst in FILES:
            s = os.path.join(SRC, rel_src)
            d = os.path.join(t, rel_dst)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
        print("synced ->", t)


patches()
sync()

PY = sys.executable
NODE = r"C:\Users\38354\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe"
print("---- reinstall (with contract gate)")
r = subprocess.run([PY, os.path.join(SRC, "install_bundle.py")], capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout.strip())
if r.returncode != 0:
    print("INSTALL FAILED")
    print(r.stderr.strip()[:2000])
    raise SystemExit(1)

print("---- verify installed copy")
r2 = subprocess.run([NODE, os.path.join(r"C:\Users\38354\.dsh\plugins\dsh-avatar-switcher", "verify-plugin.mjs"), r"C:\Users\38354\.dsh\plugins\dsh-avatar-switcher"], capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r2.stdout.strip()[-600:])
print("---- backup dirs")
b = r"D:\插件方向\backup"
if os.path.isdir(b):
    for n in sorted(os.listdir(b)):
        p = os.path.join(b, n)
        if os.path.isdir(p):
            print(" ", n, len(os.listdir(p)), "files")
