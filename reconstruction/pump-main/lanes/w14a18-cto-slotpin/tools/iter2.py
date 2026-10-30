#!/usr/bin/env python3
"""iter2.py <tag> [iters]: interval-pin to orig, then re-align on the pinned output's raw tokens and re-vote; keep the best"""
import sys,os,subprocess,json
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T=O+'/tools'; sys.path.insert(0,T); import slotpin as S
tag=sys.argv[1]; it=int(sys.argv[2]) if len(sys.argv)>2 else 3; d=f'{O}/q/{tag}'; bc=f'{O}/bw/{tag}/ex.bc'
def rat(f):
    s=subprocess.run(['python3',T+'/oratio.py',O+'/orig_fn.txt',f],capture_output=True,text=True).stdout.split(); return round(float(s[1])*(3339+int(s[4]))/2),s[1]
best=None; src=None
for k in range(it+1):
    S.mkmap2(d,O+'/orig_fn.txt',bc,f'{d}/it{k}.json',alignsrc=src,raw=bool(src))
    subprocess.run(['python3',T+'/slotpin.py','run',d,f'{d}/it{k}.json',f'{d}/it{k}.txt'],capture_output=True)
    M,r=rat(f'{d}/it{k}.txt'); print(tag,'iter',k,'M',M,'ratio',r,flush=True)
    if best is None or M>best[0]: best=(M,r,k)
    src=f'{d}/it{k}.txt'
print(tag,'best',best)
