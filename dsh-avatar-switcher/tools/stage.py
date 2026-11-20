# -*- coding: utf-8 -*-
import os, shutil, subprocess, sys, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SRC = r'D:\插件方向\dsh-avatar-skill'
DST = r'D:\编程（日常使用）\github插件\我的skill'
D = r'D:\编程（日常使用）\github插件'

def sh(cmd, cwd=None, t=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', cwd=cwd, timeout=t,
                           stdin=subprocess.DEVNULL)
        return r.returncode, (r.stdout or '').strip(), (r.stderr or '').strip()
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', '', ''

# 1) sibling repos: remotes + whether credentials are already stored
for name in os.listdir(D):
    gp = os.path.join(D, name, '.git')
    if os.path.isdir(gp):
        rc, out, _ = sh('git remote -v', cwd=os.path.join(D, name))
        rc2, br, _ = sh('git rev-parse --abbrev-ref HEAD', cwd=os.path.join(D, name))
        print('REPO', name, '| branch', br, '|', out.replace('\n', ' || '))

# 2) copy repo
IGN = shutil.ignore_patterns('__pycache__', '*.pyc', 'node_modules', '.git')
if os.path.isdir(os.path.join(SRC, '.git')):
    # copy without .git, re-init fresh in place
    pass
for item in os.listdir(SRC):
    src = os.path.join(SRC, item)
    dst = os.path.join(DST, item)
    if os.path.isdir(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=IGN)
    else:
        shutil.copy2(src, dst)
print('COPIED', sorted(os.listdir(DST)))

# 3) git init + commit
print('INIT', sh('git init -b main', cwd=DST))
print('NAME', sh('git config user.name "maodie"', cwd=DST))
print('MAIL', sh('git config user.email "maodie@local"', cwd=DST))
print('ADD', sh('git add -A', cwd=DST))
print('MODE', sh('git -c core.quotepath=false status --short', cwd=DST)[1][:800])
print('COMMIT', sh('git commit -m "feat: dsh-avatar-switcher skill + standalone plugin + desktop GUI"', cwd=DST))
print('LOG', sh('git --no-pager log --oneline -1', cwd=DST)[1])
print('FILES', sh('git --no-pager ls-files', cwd=DST)[1][:1200])
