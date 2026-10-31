#!/usr/bin/env python3
"""coldiff.py <dir>: per tail piece (array offset), ours colour offset vs the original's slot (mirperm's ORIG map)"""
import sys,re,subprocess,os
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/../t139/mirperm.py').read(); ORIG=eval(re.search(r'ORIG=(\{.*?\})\n',src).group(1))
D=sys.argv[1]
out=subprocess.run(['python3',T+'/../t139/tailfi.py',D+'/pre.mir',D+'/ssc.log'],capture_output=True,text=True).stdout.split('\n')
rows=[re.search(r'col (\d+) (0x[0-9a-f]+) arr (\d+)',l).groups() for l in out if 'arr' in l]
# last run with offsets in ORIG: take the rows after the last occurrence of arr 24
idx=[i for i,r in enumerate(rows) if r[2]=='24']
rows=rows[idx[-1]-60 if idx else 0:]
seen={}
for r in rows:
    a=int(r[2]); off=int(r[1],16)
    if a in ORIG: seen[a]=off
names=['key','lam','data','own','rent','sg','wr','ex']
for e in range(7):
    base=24+48*e; cells=[]
    for k,o in enumerate([0,8,16,24,32,40,41,42]):
        a=base+o
        if a in seen and a in ORIG: cells.append(f"{names[k]}:{(seen[a]-ORIG[a])//8:+d}")
        elif a in ORIG: cells.append(f"{names[k]}:--")
    print(f"E{e} "+' '.join(cells))
