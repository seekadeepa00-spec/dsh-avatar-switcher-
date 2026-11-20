import io, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8")
src = r"D:\插件方向\dsh-avatar-plugin\lib\client.js"
targets = [
    r"D:\插件方向\dsh-avatar-skill\plugin\lib\client.js",
    r"D:\编程（日常使用）\github插件\我的skill\plugin\lib\client.js",
    r"C:\Users\38354\Desktop\源代码\lib\client.js",
    r"C:\Users\38354\.dsh\plugins\dsh-avatar-switcher\lib\client.js",
    r"C:\Users\38354\.dsh\profiles\desktop\node_modules\dsh-plugin-avatar-switcher\lib\client.js",
]
data = io.open(src, encoding="utf-8").read() if not isinstance(src, str) else open(src, "rb").read()
print("src %d B" % len(data))
for t in targets:
    d = os.path.dirname(t)
    if not os.path.isdir(d):
        print("SKIP (no dir)", t)
        continue
    open(t, "wb").write(data)
    print("wrote %6d B  %s" % (os.path.getsize(t), t))
