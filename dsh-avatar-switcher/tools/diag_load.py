import io, os, json, socket, urllib.request, glob, time, sys

P = r"C:\Users\38354\.dsh\profiles\desktop"
out = []
def p(s): out.append(str(s))

p("== cordis.patch.yml")
try:
    p(io.open(os.path.join(P, "cordis.patch.yml"), encoding="utf-8").read())
except Exception as e:
    p("ERR %s" % e)

p("== plugin files")
d = os.path.join(P, "node_modules", "dsh-plugin-avatar-switcher")
for root, dirs, files in os.walk(d):
    for f in files:
        fp = os.path.join(root, f)
        p("  %s %s" % (os.path.relpath(fp, d), os.path.getsize(fp)))

p("== settings.json engines/peer")
try:
    pk = json.load(io.open(os.path.join(d, "package.json"), encoding="utf-8"))
    p(json.dumps(pk, ensure_ascii=False, indent=1))
except Exception as e:
    p("ERR %s" % e)

def get(port, path, t=0.4):
    try:
        r = urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path), timeout=t)
        return r.status, r.read()[:200]
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return None, b""

p("== ports")
ports = set()
import re
try:
    s = os.popen("netstat -ano").read()
    for m in re.finditer(r"(?:127\.0\.0\.1|0\.0\.0\.0):(\d+)\s", s):
        ports.add(int(m.group(1)))
except Exception as e:
    p("netstat err %s" % e)
for port in sorted(ports):
    st, body = get(port, "/wallpaper-engine/settings")
    st2, body2 = get(port, "/avatar-switcher/state")
    if st or st2:
        p("  %d wp=%s av=%s %s" % (port, st, st2, body2[:120]))

p("== recent logs")
cut = time.time() - 7200
hits = []
for base in (r"C:\Users\38354\.dsh", r"C:\Users\38354\.dsh-maodie-console"):
    for root, dirs, files in os.walk(base):
        if root.count(os.sep) - base.count(os.sep) > 2:
            dirs[:] = []
        for f in files:
            if not f.lower().endswith((".log", ".ndjson", ".txt")):
                continue
            fp = os.path.join(root, f)
            try:
                if os.path.getmtime(fp) < cut:
                    continue
                txt = io.open(fp, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            if "avatar-switcher" in txt:
                for line in txt.splitlines():
                    if "avatar-switcher" in line:
                        hits.append("%s :: %s" % (os.path.basename(fp), line[:300]))
p("hits=%d" % len(hits))
for h in hits[-25:]:
    p("  " + h)

sys.stdout.reconfigure(encoding="utf-8")
print("\n".join(out))
