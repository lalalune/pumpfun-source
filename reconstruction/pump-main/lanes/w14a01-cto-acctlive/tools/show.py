import json
for l in open("res.jsonl"):
    d=json.loads(l); r=d["rx"] or {}; f=d["llcb"] or {}; rl=d["rl"] or {}
    print(d["n"], r.get("ratio"), r.get("bytes"), r.get("slots_diff"), r.get("eq_main"), r.get("error"), f.get("cf"), f.get("bsum"), rl.get("reloads"), rl.get("tag2"))
