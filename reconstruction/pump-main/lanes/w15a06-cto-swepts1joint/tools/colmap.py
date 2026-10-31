#!/usr/bin/env python3
"""colmap.py <dir> [lo_off hi_off]: colour -> FIs (tail piece arr offset, or non-tail span/weight) for frame offsets in range"""
import sys,re,os,subprocess
D=sys.argv[1]; T=os.path.dirname(os.path.abspath(__file__)); lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0x8d0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 0xad0
log=open(D+'/ssc.log').read()
SUBK={'B':0,'e':1,'r':2,'d':3}
IV={int(m.group(1)):[(int(a),int(c)) for a,b,c,d in re.findall(r'\[(\d+)([Berd]),(\d+)([Berd]):\d+\)',m.group(2))] for m in re.finditer(r'^SS#(\d+) (.*)$',log,re.M)}
W={int(m.group(1)):float(m.group(2)) for m in re.finditer(r'^SS#(\d+) .*weight:(\S+)',log,re.M)}
COL={int(a):int(b) for a,b in re.findall(r'Assigning fi#(\d+) to fi#(\d+)',log)}
for f in IV: COL.setdefault(f,f)
out=subprocess.run(['python3',T+'/../t139/tailfi.py',D+'/pre.mir',D+'/ssc.log'],capture_output=True,text=True).stdout.split('\n')
rows=[(int(re.search(r'fi (\d+)',l).group(1)),int(re.search(r'arr (\d+)',l).group(1))) for l in out if 'arr' in l]
idx=[i for i,r in enumerate(rows) if r[1]==24]; rows=rows[idx[-1]-60 if idx else 0:]
arr={f:a for f,a in rows if 24<=a<=330}
nm=['key','lam','data','own','rent','sg','wr','ex']; po={0:0,8:1,16:2,24:3,32:4,40:5,41:6,42:7}
by={}
for f,c in COL.items(): by.setdefault(c,[]).append(f)
for c in sorted(by):
    off=0x8e0+8*(c-179)
    if not lo<=off<hi: continue
    cells=[]
    for f in sorted(by[c],key=lambda f:IV[f][0][0]):
        if f in arr: a=arr[f]; e=(a-24)//48; cells.append(f"E{e}.{nm[po[(a-24)%48]]}[{IV[f][0][0]}-{IV[f][-1][1]}]")
        else: cells.append(f"SS#{f}[{IV[f][0][0]}-{IV[f][-1][1]} w{W.get(f,0):.1e}]")
    print(hex(off),c,' '.join(cells))
