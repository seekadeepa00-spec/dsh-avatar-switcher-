# -*- coding: utf-8 -*-
import os, time, shutil

root = r"D:\插件方向\backup"
old = os.path.join(root, "dsh-avatar-plugin-%Y%m%d-%H%M%S")
new = os.path.join(root, "dsh-avatar-plugin-" + time.strftime("%Y%m%d-%H%M%S"))

if os.path.isdir(old):
    if os.path.isdir(new):
        shutil.rmtree(new)
    os.rename(old, new)
    print("renamed ->", new)

print("backup dirs:")
for d in sorted(os.listdir(root)):
    p = os.path.join(root, d)
    if os.path.isdir(p):
        n = sum(len(f) for _, _, f in os.walk(p))
        print("  %-34s %3d files" % (d, n))
