#!/usr/bin/env python3
"""floo.py <rx name> <force csv> <tag>: leave-one-out of each sticky force: joint (Mhc of the forced build via mpf.py) without it."""
import sys,os,json,subprocess
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
n,F,tag=sys.argv[1],sys.argv[2],sys.argv[3]; fs=F.split(',')
def joint(force,name):
    env=dict(os.environ,RAPRIO_STICKY='1',RAPRIO_FORCE=force,MP_LLC='llcf.sh',HC='1')
    p=subprocess.run(['python3',O+'/s16/mpf.py',name,O+f'/rx/{n}/m.ll'],capture_output=True,text=True,env=env,cwd=O)
    return json.loads(p.stdout.strip().splitlines()[-1])
full=joint(F,f'lo_{tag}_all'); print(json.dumps({'drop':None,'M':full['M'],'Mhc':full['Mhc'],'bytes':full['bytes']}),flush=True)
for i,f in enumerate(fs):
    r=joint(','.join(fs[:i]+fs[i+1:]),f'lo_{tag}_{i}')
    print(json.dumps({'drop':f,'M':r['M'],'Mhc':r['Mhc'],'bytes':r['bytes'],'dMhc':r['Mhc']-full['Mhc']}),flush=True)
