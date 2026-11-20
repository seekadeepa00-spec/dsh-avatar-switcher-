import io, os, sys, re
sys.stdout.reconfigure(encoding="utf-8")
for p in [r"D:\插件方向\dsh-avatar-plugin\lib\index.js",
          r"D:\插件方向\dsh-avatar-plugin\lib\client.js",
          r"C:\Users\38354\.dsh\plugins\dsh-avatar-switcher\lib\client.js"]:
    if not os.path.exists(p):
        print("MISSING", p); continue
    s = io.open(p, encoding="utf-8", errors="replace").read()
    lines = s.split("\n")
    print("=== %s  %d B  %d lines" % (p, len(s.encode()), len(lines)))
    for i, ln in enumerate(lines, 1):
        if re.search(r"(export|module\.exports|__ModuleLoader__|exports\.)", ln):
            print("  %4d| %s" % (i, ln.strip()[:150]))
