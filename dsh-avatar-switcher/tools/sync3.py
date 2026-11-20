# -*- coding: utf-8 -*-
import io, os, shutil, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
REPO = r"D:\插件方向\dsh-avatar-skill"
GH = r"D:\编程（日常使用）\github插件\我的skill"
IGN = {".git", "__pycache__", "node_modules"}
n = 0
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in IGN]
    rel = os.path.relpath(root, REPO)
    out = GH if rel == "." else os.path.join(GH, rel)
    if not os.path.isdir(out):
        os.makedirs(out)
    for f in files:
        if f.endswith(".pyc"):
            continue
        shutil.copy2(os.path.join(root, f), os.path.join(out, f))
        n += 1
print("copied %d files" % n)
for d in ("", "scripts", "gui", "plugin"):
    p = os.path.join(GH, d) if d else GH
    print(d or ".", sorted(x for x in os.listdir(p) if os.path.isfile(os.path.join(p, x))))
def git(*a):
    r = subprocess.run(["git"] + list(a), cwd=GH, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
git("add", "-A")
print(git("commit", "-m", "feat: add skill scripts, SKILL.md, GUI source, LICENSE"))
print(git("log", "--oneline"))
print(git("status", "--short", "--branch"))
print(git("ls-files"))
