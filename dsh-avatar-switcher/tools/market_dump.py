import json, sys
out = lambda s: sys.stdout.write(s + "\n")
targets = ['dsh-avatar', 'avatar-top', 'avatar-balance', 'task-mascot', 'falser101/mascot',
           'realtimeavatar', 'emotion-state-portrait', 'cyber-im-avatar', 'avatar-frame',
           'dsh-chat-avatar', 'effort-mascot', 'live2d-avatar']
for f in [r'C:\Users\38354\.dsh\profiles\desktop\.dsh-market\discovery-github-compatibility-v1.json',
          r'C:\Users\38354\.dsh\profiles\desktop\.dsh-market\discovery-compatibility-v1.json']:
    d = json.loads(open(f, 'rb').read().decode('utf-8', 'replace'))
    ent = d.get('entries') or {}
    out("=== %s" % f.rsplit(chr(92), 1)[-1])
    for k, v in ent.items():
        ks = k.replace('\x00', ' | ') if isinstance(k, str) else str(k)
        for t in targets:
            if t in ks:
                out("  %s" % ks[:200])
                out("     %s" % json.dumps(v, ensure_ascii=False)[:300])
                break
