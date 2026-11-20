import io, os, sys, shutil
sys.stdout.reconfigure(encoding="utf-8")

GUARD = '''
# 0 硬门：装进 bundles 之前先校验插件契约，FAIL 直接中止（防止 client.js 缺 apply 把 DSH 打崩）
NODE = os.environ.get("DSH_NODE") or r"C:\\Users\\38354\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\node\\bin\\node.exe"
VERIFY = os.path.join(SRC, "verify-plugin.mjs")
if os.path.exists(NODE) and os.path.exists(VERIFY):
    v = subprocess.run([NODE, VERIFY, SRC], capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = [ln for ln in (v.stdout or "").splitlines() if ln.startswith("RESULT") or "FAIL" in ln]
    print("\\n".join(tail))
    if v.returncode != 0:
        print("ABORT: 契约校验未通过，未安装（DSH 不会崩）")
        sys.exit(1)
else:
    print("WARN: 未找到 node 或 verify-plugin.mjs，跳过预检")
'''

for p in [r"D:\插件方向\dsh-avatar-plugin\install_bundle.py",
          r"D:\插件方向\dsh-avatar-skill\plugin\install_bundle.py",
          r"D:\编程（日常使用）\github插件\我的skill\plugin\install_bundle.py",
          r"C:\Users\38354\Desktop\源代码\install_bundle.py"]:
    if not os.path.exists(p):
        print("MISSING ", p); continue
    s = io.open(p, encoding="utf-8").read()
    if "verify-plugin.mjs" in s:
        print("ALREADY ", p); continue
    marker = 'NAME = "dsh-avatar-switcher"\n'
    if marker not in s:
        print("NOMARK  ", p); continue
    s2 = s.replace(marker, marker + GUARD, 1)
    io.open(p, "w", encoding="utf-8", newline="\n").write(s2)
    print("PATCHED ", p, len(s.encode()), "->", len(s2.encode()), "B")

# 清理安装目录里的死目录/软链残留判定
dst = r"C:\Users\38354\.dsh\plugins\dsh-avatar-switcher"
print("dst exists:", os.path.isdir(dst))
