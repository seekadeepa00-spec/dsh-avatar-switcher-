import json, io, sys
out = []
def p(s): out.append(str(s))
for f in ("gh1", "gh2"):
    try:
        d = json.load(io.open(r"D:\插件方向\gh\%s.json" % f, encoding="utf-8"))
    except Exception as e:
        p("%s parse fail %s" % (f, e)); continue
    p("== %s total=%s" % (f, d.get("total_count")))
    for it in (d.get("items") or [])[:20]:
        p("  %-45s stars=%-5s %s" % (it["full_name"], it.get("stargazers_count"), (it.get("description") or "")[:90]))
for f in ("np1", "np2"):
    try:
        d = json.load(io.open(r"D:\插件方向\gh\%s.json" % f, encoding="utf-8"))
    except Exception as e:
        p("%s parse fail %s" % (f, e)); continue
    latest = d.get("dist-tags", {}).get("latest")
    p("== npm %s latest=%s :: %s" % (d.get("name"), latest, (d.get("description") or "")[:160]))
    p("   keywords=%s" % (d.get("keywords"),))
    p("   time.created=%s modified=%s" % (d.get("time", {}).get("created"), d.get("time", {}).get("modified")))
sys.stdout.reconfigure(encoding="utf-8")
print("\n".join(out))
