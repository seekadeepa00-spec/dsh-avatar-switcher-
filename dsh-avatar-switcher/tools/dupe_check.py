import os, json, urllib.request, urllib.parse, sys
out = lambda s: sys.stdout.write(s + "\n")

def get(url, timeout=20):
    req = urllib.request.Request(url, headers={'User-Agent': 'dupe-check', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))

# 1) local market dirs
for base in [r'C:\Users\38354\.dsh\profiles\desktop\.dsh-market', r'C:\Users\38354\.dsh\.dsh-market', r'C:\Users\38354\.dsh\storages']:
    if os.path.isdir(base):
        files = []
        for dp, dn, fn in os.walk(base):
            for f in fn:
                p = os.path.join(dp, f)
                try: files.append((os.path.getsize(p), p))
                except OSError: pass
            if len(files) > 400: break
        out("LOCAL %s files=%d" % (base, len(files)))
        for s, p in sorted(files)[:25]:
            out("   %8d %s" % (s, p))
    else:
        out("LOCAL %s MISSING" % base)

# 2) npm registry search for dsh-plugin packages
def npm_search(text, size=250):
    u = "https://registry.npmjs.org/-/v1/search?text=%s&size=%d" % (urllib.parse.quote(text), size)
    try:
        d = get(u)
    except Exception as e:
        out("NPM ERR %s %r" % (text, e)); return []
    return d.get('objects', [])

names = []
for q in ['dsh-plugin', 'deepseek harness plugin', 'dsh avatar', 'avatar switcher dsh']:
    objs = npm_search(q)
    out("NPM q=%r hits=%d" % (q, len(objs)))
    for o in objs:
        p = o['package']
        nm = p['name']; kw = p.get('keywords') or []
        blob = (nm + ' ' + (p.get('description') or '') + ' ' + ' '.join(kw)).lower()
        if any(k in blob for k in ['avatar', '头像', 'mascot', '立绘']):
            out("   HIT %s | %s | %s" % (nm, p.get('version'), (p.get('description') or '')[:90]))
        if nm.startswith('dsh') or 'dsh' in nm:
            names.append(nm)
out("NPM dsh-ish names=%d uniq=%d" % (len(names), len(set(names))))

# 3) GitHub repo search
def gh(q):
    u = "https://api.github.com/search/repositories?q=%s&per_page=30&sort=updated" % urllib.parse.quote(q)
    try:
        return get(u)
    except Exception as e:
        out("GH ERR %s %r" % (q, e)); return {}

for q in ['deepseek harness plugin avatar', 'dsh avatar switcher', 'dsh-plugin avatar', 'deepseek harness avatar', 'dsh-plugin-avatar-switcher', 'deepseek harness mascot']:
    d = gh(q)
    tot = d.get('total_count')
    out("GH q=%r total=%s" % (q, tot))
    for it in (d.get('items') or [])[:10]:
        out("   %s stars=%s %s" % (it['full_name'], it['stargazers_count'], (it.get('description') or '')[:80]))
