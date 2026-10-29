#!/usr/bin/env python3
"""scan2.py <mode:after|before> <tgt> [base MOVES]: move every block to after/before tgt; report difflines."""
import sys,os,subprocess,concurrent.futures as cf
sys.path.insert(0,os.path.dirname(__file__)); import irlib
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-sellv2-b')
mode,tgt=sys.argv[1],sys.argv[2]; basem=sys.argv[3] if len(sys.argv)>3 else ''
t=open(os.environ.get('IRBASE',OUT+'/out/base/pump_recovered.ll')).read()
pre,parts,post=irlib.split(t); L=[irlib.label(p) for p in parts][1:]
def run(i_l):
    i,l=i_l
    if l==tgt: return None
    m=(basem+';' if basem else '')+f'{mode}:{l}:{tgt}'
    env=dict(os.environ,MOVES=m,Q='1')
    r=subprocess.run(['python3',OUT+'/scripts/irx.py',f'scan2_{i}',OUT+'/edits/moves.py'],env=env,capture_output=True,text=True)
    s=r.stdout.strip().split('\n')[0]
    try: d=int(s.split('difflines=')[1]); n=int(s.split('cand=')[1].split()[0])
    except: d=99999;n=0
    subprocess.run(['rm','-rf',OUT+f'/irexp/scan2_{i}'])
    return (d,n,i,l)
with cf.ThreadPoolExecutor(int(os.environ.get('J','8'))) as ex:
    res=[r for r in ex.map(run,enumerate(L)) if r]
res.sort()
for r in res[:int(os.environ.get('TOP','15'))]: print(*r)
