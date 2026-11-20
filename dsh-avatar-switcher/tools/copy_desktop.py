import os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8")
src = r"D:\插件方向\dsh-avatar-plugin"
dst = r"C:\Users\38354\Desktop\源代码"
os.makedirs(dst, exist_ok=True)
for dp, dn, fn in os.walk(src):
    dn[:] = [d for d in dn if d not in ("__pycache__", "node_modules", ".git")]
    rel = os.path.relpath(dp, src)
    out = dst if rel == "." else os.path.join(dst, rel)
    os.makedirs(out, exist_ok=True)
    for f in fn:
        shutil.copy2(os.path.join(dp, f), os.path.join(out, f))
n = 0
for dp, dn, fn in os.walk(dst):
    for f in fn:
        p = os.path.join(dp, f)
        n += 1
        print("%-42s %7d B" % (os.path.relpath(p, dst), os.path.getsize(p)))
print("files", n)
