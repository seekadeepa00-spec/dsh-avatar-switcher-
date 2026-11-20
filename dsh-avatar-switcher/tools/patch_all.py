import io, os, sys
sys.stdout.reconfigure(encoding="utf-8")

BLOCK = (
    "  exports.name = 'dsh-avatar-switcher';\n"
    "  exports.inject = [];\n"
    "  exports.apply = function apply() {};\n"
)

TARGETS = [
    r"D:\插件方向\dsh-avatar-plugin\lib\client.js",
    r"D:\插件方向\dsh-avatar-skill\plugin\lib\client.js",
    r"D:\编程（日常使用）\github插件\我的skill\plugin\lib\client.js",
    r"C:\Users\38354\Desktop\源代码\lib\client.js",
    r"C:\Users\38354\.dsh\plugins\dsh-avatar-switcher\lib\client.js",
]

for p in TARGETS:
    if not os.path.exists(p):
        print("MISSING  ", p)
        continue
    s = io.open(p, encoding="utf-8").read()
    if "exports.apply" in s:
        print("ALREADY  ", p, len(s.encode()))
        continue
    marker = "  return module.exports;"
    if marker not in s:
        print("NOMARK   ", p)
        continue
    s2 = s.replace(marker, BLOCK + marker, 1)
    io.open(p, "w", encoding="utf-8", newline="\n").write(s2)
    print("PATCHED  ", p, len(s.encode()), "->", len(s2.encode()), "B")
