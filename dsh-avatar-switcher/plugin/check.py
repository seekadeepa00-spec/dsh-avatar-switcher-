import re, subprocess, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8")

def ports():
    out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, errors="replace").stdout
    return sorted({int(m) for m in re.findall(r"127\.0\.0\.1:(\d+)\s+\S+\s+LISTENING", out)})

def probe(p, path):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d%s" % (p, path), timeout=0.7) as r:
            return r.status, r.read(300).decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", 0), ""

for p in ports():
    st, body = probe(p, "/avatar-switcher/state")
    if st == 200 and body.startswith("{"):
        print("GUI port %d  avatar-switcher LIVE" % p)
        print("state:", body)
        for side in ("user", "ai"):
            s2, _ = probe(p, "/avatar-switcher/" + side)
            print("GET /avatar-switcher/%s -> %s" % (side, s2))
        break
else:
    print("avatar-switcher not loaded yet (restart DSH, then rerun)")
