import json, sys
out = lambda s: sys.stdout.write(s + "\n")
KEYS = ['avatar', 'mascot', 'portrait', '头像', '立绘']
for f in [r'C:\Users\38354\.dsh\profiles\desktop\.dsh-market\discovery-github-compatibility-v1.json',
          r'C:\Users\38354\.dsh\profiles\desktop\.dsh-market\discovery-compatibility-v1.json']:
    d = json.loads(open(f, 'rb').read().decode('utf-8', 'replace'))
    ent = d.get('entries')
    out("=== %s type=%s n=%d" % (f.rsplit(chr(92), 1)[-1], type(ent).__name__, len(ent)))
    items = list(ent.items()) if isinstance(ent, dict) else list(enumerate(ent))
    k0, v0 = items[0]
    out("    key0=%s val=%s" % (str(k0)[:60], json.dumps(v0, ensure_ascii=False)[:400]))
    hits = 0
    for k, it in items:
        blob = json.dumps(it, ensure_ascii=False).lower() + ' ' + str(k).lower()
        if any(x in blob for x in KEYS):
            hits += 1
            if isinstance(it, dict):
                nm = it.get('name') or it.get('id') or it.get('package') or it.get('title') or k
                ds = (it.get('description') or it.get('summary') or '')[:120]
            else:
                nm, ds = k, str(it)[:120]
            out("    HIT %s | %s" % (nm, ds))
            if hits >= 60:
                out("    ... more suppressed"); break
    out("    hits=%d" % hits)
