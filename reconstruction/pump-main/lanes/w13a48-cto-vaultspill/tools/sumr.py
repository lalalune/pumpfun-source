import json,sys
for l in open(sys.argv[1]):
    n,js=l.split(' ',1)
    try: d=json.loads(js[:js.index('}')+1])
    except Exception: print(n,'?'); continue
    fb=js[js.index('}')+1:].strip()
    print(f"{n:22} ok={d['ok']} raw={d['raw']} rl={len(d['rl'] or [])} ratio={d['ratio']} slots={d['slots']} bytes={d['bytes']} {fb}")
