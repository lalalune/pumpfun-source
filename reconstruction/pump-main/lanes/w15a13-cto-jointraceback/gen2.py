# gen2.py: the size-repay screen = base (a8, c2, a8+c2) x every sizeknobs-cto.json knob whose edit applies to main 86e2a6b.
import json,runpy
K=[k for k in json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs'] if k.get('edit')]
src=open('programs/pump/src/creator/admin_cto.rs').read()
K=[k for k in K if all(src.count(e['old'])==1 and e['old'].count('\n')==e['new'].count('\n') for e in k['edit'])]
base={'a8':runpy.run_path('e/a8.py')['EDITS'],'c2':runpy.run_path('e/c2.py')['EDITS']}; base['a8c2']=base['a8']+base['c2']
for b,be in base.items():
    for k in K:
        ke=[(e['old'],e['new']) for e in k['edit']]
        if any(o in bo or bo in o for o,_ in ke for bo,_ in be): continue
        open(f"e/{b}_{k['name']}.py".replace('+','_'),'w').write(f"EDITS={be+ke!r}\nHYP={('size repay: '+b+' + knob '+k['name'])!r}\n")
