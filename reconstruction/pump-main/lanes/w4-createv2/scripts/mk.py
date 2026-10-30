#!/usr/bin/env python3
"""mk.py <name> <edit.py> [from=base]: copy src/<from> to src/<name> and apply EDITS (list of (old,new)) to src/create_v2.rs (or FILE)."""
import sys,runpy,shutil,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-createv2')
name,ed=sys.argv[1],sys.argv[2]; frm=sys.argv[3] if len(sys.argv)>3 else 'base'
d=O+'/src/'+name
if os.path.exists(d): shutil.rmtree(d)
shutil.copytree(O+'/src/'+frm,d)
g=runpy.run_path(ed); f=d+'/src/'+g.get('FILE','create_v2.rs')
t=open(f).read()
for a,b in g['EDITS']:
    assert t.count(a)==1,('not unique/found',a[:80],t.count(a)); t=t.replace(a,b)
t+=g.get('APPEND','')
open(f,'w').write(t); print('ok',name)
