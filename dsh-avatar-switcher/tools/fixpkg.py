import io, os, json, shutil, sys

pk = {
  "name": "dsh-plugin-avatar-switcher",
  "version": "1.0.0",
  "private": True,
  "type": "module",
  "main": "./lib/index.js",
  "description": "Custom chat avatars (user / assistant) for a stock DeepSeek Harness install - no wallpaper-engine required.",
  "license": "MIT",
  "exports": {
    ".": "./lib/index.js",
    "./client": "./lib/client.js",
    "./client.js": "./lib/client.js",
    "./cordis.patch.yml": "./cordis.patch.yml",
    "./package.json": "./package.json"
  },
  "dsh": {
    "id": "dsh-avatar-switcher",
    "name": "DSH Avatar Switcher",
    "version": "1.0.0",
    "bundle": {"patch": "./cordis.patch.yml"},
    "client": {
      "inject": ["@deepseek-ai/dsh-client-runtime"],
      "platform": "web",
      "immediately": True
    }
  },
  "dshTarget": "0.2.2-rc.1",
  "engines": {"node": ">=22.5"}
}

text = json.dumps(pk, ensure_ascii=False, indent=2) + "\n"
targets = [
    r"D:\插件方向\dsh-avatar-plugin\package.json",
    r"D:\插件方向\dsh-avatar-skill\plugin\package.json",
    r"D:\编程（日常使用）\github插件\我的skill\plugin\package.json",
    r"C:\Users\38354\.dsh\plugins\dsh-avatar-switcher\package.json",
    r"C:\Users\38354\.dsh\profiles\desktop\node_modules\dsh-plugin-avatar-switcher\package.json",
]
for t in targets:
    d = os.path.dirname(t)
    if not os.path.isdir(d):
        print("skip (no dir): %s" % t)
        continue
    io.open(t, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote %s %d" % (t, os.path.getsize(t)))
sys.stdout.reconfigure(encoding="utf-8")
