import io, os, json, shutil, subprocess, sys

SRC = r"D:\插件方向\dsh-avatar-plugin"
DST = r"C:\Users\38354\.dsh\plugins\dsh-avatar-switcher"
PROF = r"C:\Users\38354\.dsh\profiles\desktop"
PKJ = os.path.join(PROF, "package.json")
NAME = "dsh-avatar-switcher"

# 0 硬门：装进 bundles 之前先校验插件契约，FAIL 直接中止（防止 client.js 缺 apply 把 DSH 打崩）
NODE = os.environ.get("DSH_NODE") or r"C:\Users\38354\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe"
VERIFY = os.path.join(SRC, "verify-plugin.mjs")
if os.path.exists(NODE) and os.path.exists(VERIFY):
    v = subprocess.run([NODE, VERIFY, SRC], capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = [ln for ln in (v.stdout or "").splitlines() if ln.startswith("RESULT") or "FAIL" in ln]
    print("\n".join(tail))
    if v.returncode != 0:
        print("ABORT: 契约校验未通过，未安装（DSH 不会崩）")
        sys.exit(1)
else:
    print("WARN: 未找到 node 或 verify-plugin.mjs，跳过预检")

out = []
def p(s): out.append(str(s))

# 1 copy source
if os.path.isdir(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__", "*.pyc"))
p("copied -> %s (%d files)" % (DST, sum(len(f) for _, _, f in os.walk(DST))))

# 2 node_modules junction
link = os.path.join(PROF, "node_modules", NAME)
if os.path.isdir(link):
    p("link exists: %s" % link)
else:
    r = subprocess.run(["cmd", "/c", "mklink", "/J", link, DST], capture_output=True, text=True, encoding="mbcs", errors="replace")
    p("mklink rc=%s %s" % (r.returncode, (r.stdout or r.stderr).strip()))

# 3 package.json dep + bundle
bak = PKJ + ".bak-avatar-switcher"
if not os.path.exists(bak):
    shutil.copy2(PKJ, bak)
pk = json.load(io.open(PKJ, encoding="utf-8"))
pk.setdefault("dependencies", {})[NAME] = "file:../../plugins/" + NAME
b = pk.setdefault("dsh", {}).setdefault("profile", {}).setdefault("bundles", [])
if NAME not in b:
    i = b.index("maodie-armor") + 1 if "maodie-armor" in b else len(b)
    b.insert(i, NAME)
io.open(PKJ, "w", encoding="utf-8", newline="\n").write(json.dumps(pk, ensure_ascii=False, indent=2) + "\n")
p("package.json updated, bundles=%s" % b)

sys.stdout.reconfigure(encoding="utf-8")
print("\n".join(out))
