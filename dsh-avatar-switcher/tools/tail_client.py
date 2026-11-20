import io, sys
sys.stdout.reconfigure(encoding="utf-8")
p = r"C:\Users\38354\Desktop\源代码\lib\client.js"
src = io.open(p, encoding="utf-8").read().split("\n")
print("client.js lines:", len(src))
keys = ("apply", "sweep", "boot", "reload", "module.exports", "MutationObserver", "setInterval", "loadState")
for i, ln in enumerate(src, 1):
    if any(k in ln for k in keys):
        print("%4d | %s" % (i, ln.rstrip()[:150]))
print("--- tail 12 ---")
for i in range(max(1, len(src) - 12), len(src) + 1):
    print("%4d | %s" % (i, src[i - 1].rstrip()[:150]))
