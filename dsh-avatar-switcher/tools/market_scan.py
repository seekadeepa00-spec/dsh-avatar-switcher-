import json, sys, re
out = lambda s: sys.stdout.write(s + "\n")
KEYS = ['avatar', 'mascot', 'portrait', '头像', '立绘', 'avatarUrl', 'face']
for f in [r'C:\Users\38354\.dsh\profiles\desktop\.dsh-market\discovery-github-compatibility-v1.json',
          r'C:\Users\38354\.dsh\profiles\desktop\.dsh-market\discovery-compatibility-v1.json']:
    try:
        raw = open(f, 'rb').read().decode('utf-8', 'replace')
    except OSError as e:
        out("ERR %s %r" % (f, e)); continue
    d = json.loads(raw)
    out("=== %s top=%s" % (f.rsplit('\\', 1)[-1], type(d).__name__))
    if isinstance(d, dict):
        out("    keys=%s" % list(d.keys())[:12])
        rows = None
        for k in ('items', 'rows', 'entries', 'plugins', 'data', 'results'):
            if isinstance(d.get(k), list):
                rows = d[k]; out("    list key=%s n=%d" % (k, len(rows))); break
    elif isinstance(d, list):
        rows = d; out("    n=%d" % len(d))
    else:
        rows = None
    if not rows:
        continue
    out("    sample=%s" % json.dumps(rows[0])[:300])
    hits = 0
    for it in rows:
        blob = json.dumps(it, ensure_ascii=False).lower()
        if any(k.lower() in blob for k in KEYS):
            hits += 1
            name = it.get('name') or it.get('id') or it.get('package') or it.get('full_name') or '?'
            desc = (it.get('description') or it.get('summary') or '')[:110]
            repo = it.get('repository') or it.get('repo') or it.get('url') or ''
            out("    HIT %s | %s | %s" % (name, desc, str(repo)[:90]))
            if hits > 40: break
    out("    hits=%d" % hits)
