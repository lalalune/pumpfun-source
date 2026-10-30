import json,runpy
K={k['name']:k for k in json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']}
def knob(n): return [(e['old'],e['new']) for e in K[n]['edit']]
def base(name): return runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a20-cto-reloadarm/e/%s.py'%name)['EDITS']
