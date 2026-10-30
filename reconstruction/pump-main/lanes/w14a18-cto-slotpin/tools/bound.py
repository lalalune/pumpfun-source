#!/usr/bin/env python3
"""bound.py <tag>... : for each bw/<tag>/ex.bc: prep, pin spills (and all objects) to the original's slots (mode b) and to
RAR+w12's slots (mode a, ref bw/k_rar_12), print ratio/M table and append to bound.jsonl"""
import sys,os,subprocess,json,re
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T=O+'/tools'
sys.path.insert(0,T); import slotpin
def rat(f):
    s=subprocess.run(['python3',T+'/oratio.py',O+'/orig_fn.txt',f],capture_output=True,text=True).stdout
    r=float(s.split()[1]); n=int(s.split()[4]); b=int(s.split()[6]); return r,n,b
def msk(f): return float(subprocess.run(['python3',T+'/mratio2.py',O+'/orig_fn.txt',f],capture_output=True,text=True).stdout.split()[-1])
M=lambda r,n:round(r*(3339+n)/2)
REFA=os.environ.get('REFA','k_rar_12')
for tag in sys.argv[1:]:
    d=f'{O}/p/{tag}'
    if not os.path.exists(d+'/objs.json'): slotpin.prep(f'{O}/bw/{tag}/ex.bc',d)
    r,n,b=rat(d+'/direct.txt'); mk=msk(d+'/direct.txt')
    row=dict(tag=tag,bytes=b,n=n,ratio=r,M=M(r,n),maskedM=M(mk,n),nspill=sum(1 for v in json.load(open(d+'/objs.json')).values() if v['type']=='spill-slot'))
    for mode,ref in (('b',O+'/orig_fn.txt'),('a',f'{O}/p/{REFA}/direct.txt'),('m',f'{O}/p/{os.environ.get("REFM","k_main_none")}/direct.txt')):
        if mode!='b' and not os.path.exists(ref): continue
        for k in ('spill','all'):
            mp,mv,nv=slotpin.mkmap(d,ref,k,f'{d}/m{mode}_{k}.json')
            subprocess.run(['python3',T+'/slotpin.py','run',d,f'{d}/m{mode}_{k}.json',f'{d}/o{mode}_{k}.txt'],capture_output=True)
            pr,_,_=rat(f'{d}/o{mode}_{k}.txt'); row[f'{mode}_{k}']=pr; row[f'{mode}_{k}_M']=M(pr,n); row[f'{mode}_{k}_moved']=mv
    open(O+'/bound.jsonl','a').write(json.dumps(row)+'\n')
    print(f"{tag:12s} B={b} r={r:.5f} M={row['M']} mM={row['maskedM']} | orig-pin spill {row['b_spill']:.5f} M={row['b_spill_M']} all {row['b_all']:.5f} M={row['b_all_M']}"+(f" | rar-pin spill M={row['a_spill_M']}" if 'a_spill' in row else '')+(f" | main-pin spill M={row['m_spill_M']} all M={row['m_all_M']}" if 'm_spill' in row else ''),flush=True)
