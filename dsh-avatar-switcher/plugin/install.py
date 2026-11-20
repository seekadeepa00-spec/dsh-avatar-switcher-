import os, shutil, sys, io, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = r'D:\插件方向\dsh-avatar-plugin'
DEST = r'C:\Users\38354\.dsh\profiles\desktop\node_modules\dsh-plugin-avatar-switcher'
PATCH = r'C:\Users\38354\.dsh\profiles\desktop\cordis.patch.yml'

# 1) 拷包
if os.path.isdir(DEST):
    shutil.rmtree(DEST)
os.makedirs(DEST, exist_ok=True)
for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules')]
    rel = os.path.relpath(root, SRC)
    target = DEST if rel == '.' else os.path.join(DEST, rel)
    os.makedirs(target, exist_ok=True)
    for f in files:
        shutil.copy2(os.path.join(root, f), os.path.join(target, f))
print('copied ->', DEST)

# 2) 打补丁层
txt = io.open(PATCH, encoding='utf-8').read()
if 'dsh-plugin-avatar-switcher' in txt:
    print('patch already present')
else:
    block = ("- insert:\n"
             "    - id: avatar-switcher\n"
             "      name: 'dsh-plugin-avatar-switcher'\n")
    if not txt.endswith('\n'):
        txt += '\n'
    io.open(PATCH, 'w', encoding='utf-8', newline='\n').write(txt + block)
    print('patch appended ->', PATCH)

# 3) 自检
for name in ('package.json', 'cordis.patch.yml', r'lib\index.js', r'lib\client.js'):
    p = os.path.join(DEST, name)
    print(('OK  ' if os.path.isfile(p) else 'MISS'), p, os.path.getsize(p) if os.path.isfile(p) else 0)
