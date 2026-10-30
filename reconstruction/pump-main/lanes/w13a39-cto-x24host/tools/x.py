#!/usr/bin/env python3
"""x.py <module.ll> <name> <spec> [edits.py] : text EDITS (old,new pairs, exactly once) then iredit spec; llc oracle; with OM=1 also objmap."""
import sys,os,json,runpy,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import iredit, ctoracle
iredit.ORIG=ctoracle.orig_tokens()
mod=open(sys.argv[1]).read(); name=sys.argv[2]; spec=sys.argv[3] if len(sys.argv)>3 else ''
if len(sys.argv)>4:
    for e in runpy.run_path(sys.argv[4])['EDITS']:
        if callable(e): mod=e(mod); continue
        a,b=e; c=mod.count(a); assert c==1,(c,a[:150]); mod=mod.replace(a,b)
os.makedirs('t/'+name,exist_ok=True)
os.environ['PF']='1'
m=iredit.run_spec(mod,'t/'+name,spec,keep=False)
print(json.dumps({'name':name,**m}))
if os.environ.get('OM'):
    open('t/'+name+'/in.ll','w').write(mod)
    subprocess.run(['bash','tools/omap.sh','t/'+name+'/in.ll',spec,'om/'+name],capture_output=True)
    os.remove('t/'+name+'/in.ll')
