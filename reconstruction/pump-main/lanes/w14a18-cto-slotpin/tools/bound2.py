#!/usr/bin/env python3
"""bound2.py <tag>... : interval-level (pre-StackSlotColoring) pin bound. For bw/<tag>/ex.bc: prep at stack-slot-coloring,
calibrate (colour map -> must equal the real build), then valid interval pin to the original (orig) and to main's frame (main)."""
import sys,os,subprocess,json
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T=O+'/tools'
sys.path.insert(0,T); import slotpin as S
def rat(f):
    s=subprocess.run(['python3',T+'/oratio.py',O+'/orig_fn.txt',f],capture_output=True,text=True).stdout.split()
    r=float(s[1]); n=int(s[4]); return r,n,round(r*(3339+n)/2)
REFM=os.environ.get('REFM','k_main_none')
for tag in sys.argv[1:]:
    d=f'{O}/q/{tag}'; bc=f'{O}/bw/{tag}/ex.bc'
    if not os.path.exists(d+'/objs.json'): S.prep(bc,d,'stack-slot-coloring')
    S.colmap(d,d+'/col.json'); subprocess.run(['python3',T+'/slotpin.py','run',d,d+'/col.json',d+'/col.txt'],capture_output=True)
    cal=open(d+'/col.txt').read()==open(d+'/real.txt').read()
    r,n,M=rat(d+'/real.txt'); row=dict(tag=tag,calibrated=cal,ratio=r,n=n,M=M)
    for mode,ref in (('orig',O+'/orig_fn.txt'),('main',f'{O}/q/{REFM}/real.txt')):
        if not os.path.exists(ref): continue
        S.mkmap2(d,ref,bc,f'{d}/i_{mode}.json')
        subprocess.run(['python3',T+'/slotpin.py','run',d,f'{d}/i_{mode}.json',f'{d}/i_{mode}.txt'],capture_output=True)
        pr,_,pM=rat(f'{d}/i_{mode}.txt'); row[f'i_{mode}']=pr; row[f'i_{mode}_M']=pM
    open(O+'/bound2.jsonl','a').write(json.dumps(row)+'\n')
    print(f"{tag:12s} cal={cal} r={r:.5f} M={M} | interval-pin orig {row.get('i_orig',0):.5f} M={row.get('i_orig_M')} | main-frame M={row.get('i_main_M')}",flush=True)
