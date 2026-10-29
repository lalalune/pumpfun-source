#!/usr/bin/env python3
"""scan.py <blk> [base MOVES]: move blk after every other block, report difflines (parallel)."""
import sys,os,subprocess,concurrent.futures as cf
sys.path.insert(0,os.path.dirname(__file__)); import irlib
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-sellv2-b')
blk=sys.argv[1]; basem=sys.argv[2] if len(sys.argv)>2 else ''
t=open(os.environ.get('IRBASE',OUT+'/out/base/pump_recovered.ll')).read()
pre,parts,post=irlib.split(t); L=[irlib.label(p) for p in parts][1:]
def run(i_l):
    i,l=i_l
    if l==blk: return None
    m=(basem+';' if basem else '')+f'after:{blk}:{l}'
    env=dict(os.environ,MOVES=m,Q='1')
    r=subprocess.run(['python3',OUT+'/scripts/irx.py',f'scan_{blk}_{i}',OUT+'/edits/moves.py'],env=env,capture_output=True,text=True)
    s=r.stdout.strip().split('\n')[0]
    try: d=int(s.split('difflines=')[1]); n=int(s.split('cand=')[1].split()[0])
    except: d=99999;n=0
    subprocess.run(['rm','-rf',OUT+f'/irexp/scan_{blk}_{i}'])
    return (d,n,i,l)
with cf.ThreadPoolExecutor(int(os.environ.get('J','8'))) as ex:
    res=[r for r in ex.map(run,enumerate(L)) if r]
res.sort()
for r in res[:int(os.environ.get('TOP','15'))]: print(*r)
