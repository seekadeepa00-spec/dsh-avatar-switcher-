import io, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8")

SRC = r"D:\插件方向\dsh-avatar-plugin\verify-plugin.mjs"
DESTS = [
    r"D:\插件方向\dsh-avatar-skill\plugin",
    r"D:\编程（日常使用）\github插件\我的skill\plugin",
    r"C:\Users\38354\Desktop\源代码",
    r"C:\Users\38354\.dsh\plugins\dsh-avatar-switcher",
]
for d in DESTS:
    if not os.path.isdir(d):
        print("NODIR  ", d); continue
    shutil.copy2(SRC, os.path.join(d, "verify-plugin.mjs"))
    print("COPIED ", os.path.join(d, "verify-plugin.mjs"), os.path.getsize(os.path.join(d, "verify-plugin.mjs")))

print("\n--- install_bundle.py ---")
p = r"D:\插件方向\dsh-avatar-plugin\install_bundle.py"
print(io.open(p, encoding="utf-8").read())
