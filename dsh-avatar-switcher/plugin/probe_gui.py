import re, subprocess, sys, urllib.request, json
sys.stdout.reconfigure(encoding="utf-8")
out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, errors="replace").stdout
ports = sorted({int(m) for m in re.findall(r"127\.0\.0\.1:(\d+)\s+\S+\s+LISTENING", out)})
found = []
for p in ports:
    for path in ("/avatar-switcher/state", "/wallpaper-engine/settings"):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d%s" % (p, path), timeout=0.6) as r:
                body = r.read(400).decode("utf-8", "replace")
                found.append((p, path, r.status, body))
                break
        except Exception as e:
            code = getattr(e, "code", None)
            if code:
                found.append((p, path, code, "err"))
                break
for f in found:
    print("port=%s path=%s status=%s body=%s" % f)
