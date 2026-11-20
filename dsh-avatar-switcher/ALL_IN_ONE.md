# dsh-avatar-switcher 全量代码

这是一个目录，所有相关代码都在这里，按用途分层：

```
dsh-avatar-switcher/
├─ plugin/          DSH 插件本体（宿主 index.js + 浏览器 client.js + 安装/校验脚本）
│  ├─ package.json          清单：dsh.id / dsh.bundle.patch / dsh.client.inject
│  ├─ cordis.patch.yml      bundles 补丁行
│  ├─ lib/index.js          宿主：/avatar-switcher/* 路由、token、魔数、配额、图库
│  ├─ lib/client.js         浏览器：slot → css → dom → none 四层适配器
│  ├─ install_bundle.py     安装（先跑 verify-plugin.mjs 契约门，FAIL 不装）
│  ├─ verify-plugin.mjs     一键契约校验（node 跑，退出码 0=PASS 1=FAIL）
│  ├─ test-host.mjs         假 webServer 冒烟（含 token / 魔数 / 路径穿越 / 图库全流程）
│  ├─ check.py              真机验活（扫端口认 /avatar-switcher/state）
│  ├─ probe_gui.py          端口探测
│  └─ README.md             接口表 + v3/v4 章节
├─ scripts/          命令行工具（零依赖，只用标准库）
│  ├─ set_avatar.py         user|ai|mascot|list|probe 六子命令
│  └─ cutout.py             去背景：--mode detail / --mode warm
├─ gui/              桌面程序源码
│  └─ AvatarTool.cs         C# 5 WinForms，编译出 DSH头像切换器.exe
├─ tools/            开发期一次性脚本（探测、同步、打补丁、市场查重）
├─ SKILL.md          skill 说明（给 DSH 读的）
├─ LICENSE           MIT
└─ ALL_IN_ONE.md     本文件
