#!/usr/bin/env python3
"""tab.py name...: one TSV row per cell from res/ev_<name>.txt (+ stack/<name>.txt if present)."""
import sys,re,json,os
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a22-cto-s3outline'
print('\t'.join(['cell','bytes','M','Mperm','Mhc','skM','rfj','lddw','err_order','660','bb56i_extra','chunk3000_M','acc_base_regs','restored_M','restored_Mhc']))
for n in sys.argv[1:]:
    p=f'{O}/res/ev_{n}.txt'
    if not os.path.exists(p): continue
    t=open(p).read()
    sc=re.search(r'"M": (\d+).*?"skM": (\d+)',t); mp=re.search(r'"Mperm": (\d+), "Mhc": (\d+)',t)
    by=re.search(r'"bytes": (\d+)',t)
    eo=re.search(r'lddw=(\d+) (.*)',t); errs=eo.group(2).split() if eo else []
    order=' '.join(e.split('@')[0] for e in errs if e.split('@')[0] in ('289','298','306','296','326','312','307','330','338','334'))
    s660=[e.split('@')[1] for e in errs if e.startswith('660@')]
    ar=re.search(r"joins \[\('[^']+', \[[^\]]*\], \[([^\]]*)\]\)",t)
    ch=re.search(r'chunkM\[3000,3800\)=\s*(\d+).*?cand base regs: ([^e]*?)(?:  e\.g\.|$)',t,re.M)
    rf=re.search(r'^\S+ (\d+)',t.strip().split('\n')[-1])
    rM=rMhc='';sp=f'{O}/stack/{n}.txt'
    if os.path.exists(sp):
        st=open(sp).read(); m=re.search(r' M (\d+) share',st); rM=m.group(1) if m else ''
        m=re.search(r'phr \{[^}]*"Mhc": (\d+)',st); rMhc=m.group(1) if m else ''
    print('\t'.join(x or '-' for x in [n,by.group(1) if by else '',sc.group(1) if sc else '',mp.group(1) if mp else '',mp.group(2) if mp else '',sc.group(2) if sc else '',
        rf.group(1) if rf else '',eo.group(1) if eo else '',order,s660[0] if s660 else '',(ar.group(1).replace("'","") if ar else ''),
        ch.group(1) if ch else '',(ch.group(2).strip() if ch else ''),rM,rMhc]))
