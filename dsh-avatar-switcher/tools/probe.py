# -*- coding: utf-8 -*-
import os, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\编程（日常使用）\github插件\我的skill'
D = r'D:\编程（日常使用）\github插件'

def sh(cmd, cwd=None, t=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', cwd=cwd, timeout=t,
                           stdin=subprocess.DEVNULL)
        return r.returncode, (r.stdout or '').strip()[:300], (r.stderr or '').strip()[:300]
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', '', ''

print('D exists', os.path.isdir(D))
print('D list', os.listdir(D) if os.path.isdir(D) else None)
print('P exists', os.path.isdir(P), 'file', os.path.isfile(P))
if os.path.isdir(P):
    print('P list', os.listdir(P))
    print('P has .git', os.path.isdir(os.path.join(P, '.git')))
print('GITVER', sh('git --version'))
print('NAME', sh('git config --global user.name'))
print('MAIL', sh('git config --global user.email'))
print('CREDHELPER', sh('git config --global credential.helper'))
print('GH', sh('where gh'))
print('MSYS cfg', sh('cat ~/.gitconfig'))
