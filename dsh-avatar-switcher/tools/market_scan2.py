import json, sys
out = lambda s: sys.stdout.write(s + "\n")
KEYS = ['avatar', 'mascot', 'portrait', '头像', '立绘', '脸']
for f in [r'C:\Users\38354\.dsh\profiles\desktop\.dsh-market\discovery-github-compatibility-v1.json',
          r'C:\Users\38354\.dsh\profiles\desktop\.dsh-market\discovery-compatibility-v1.json']:
    raw = open(f, 'rb').read().decode('utf-8', 'replace')
    d = json.loads(raw)
    rows = d.get('entries') or []
    out("=== %s entries=%d schema=%s" % (f.rsplit(chr(92), 1)[-1], len(rows), d.get('schema')))
    if rows:
        out("    sample=%s" % json.dumps(rows[0], ensure_ascii=False)[:400])
    hits = 0
    for it in rows:
        blob = json.dumps(it, ensure_ascii=False).lower()
        if any(k.lower() in blob for k in KEYS):
            hits += 1
            nm = it.get('name') or it.get('id') or it.get('package') or it.get('title') or '?'
            ds = (it.get('description') or it.get('summary') or it.get('desc') or '')[:120]
            out("    HIT %s | %s" % (nm, ds))
    out("    hits=%d" % hits)
