#!/usr/bin/env python3
"""comp.py <out.py> <edit.py|-> [knob|+extra.py ...]: compose source EDITS from a lane edit file and size-knob catalog entries."""
import sys,json,runpy
K={k['name']:k for k in json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']}
out,base,*ks=sys.argv[1:]
E=[] if base=='-' else list(runpy.run_path(base)['EDITS'])
for k in ks:
    if k.endswith('.py'): E+=list(runpy.run_path(k)['EDITS'])
    else: E+=[(x['old'],x['new']) for x in K[k]['edit']]
open(out,'w').write('EDITS='+repr(E)+'\n')
