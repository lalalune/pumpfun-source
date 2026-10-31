#!/usr/bin/env python3
"""longsp.py <dir>: spill intervals live across the sharing-CPI tail run (not tail pieces), their colour/offset/weight;
marks swept's FI (the reload feeding the event +184 store)."""
import sys,re,os,subprocess
D=sys.argv[1]; T=os.path.dirname(os.path.abspath(__file__))
log=open(D+'/ssc.log').read(); pre=open(D+'/pre.mir').read().split('\n')
SUBK={'B':0,'e':1,'r':2,'d':3}
def iv(s): return [(int(a)*4+SUBK[b],int(c)*4+SUBK[d]) for a,b,c,d in re.findall(r'\[(\d+)([Berd]),(\d+)([Berd]):\d+\)',s)]
IV={int(m.group(1)):iv(m.group(2)) for m in re.finditer(r'^SS#(\d+) (.*)$',log,re.M)}
W={int(m.group(1)):float(m.group(2)) for m in re.finditer(r'^SS#(\d+) .*weight:(\S+)',log,re.M)}
COL={int(a):int(b) for a,b in re.findall(r'Assigning fi#(\d+) to fi#(\d+)',log)}
for f in IV: COL.setdefault(f,f)
out=subprocess.run(['python3',T+'/../t139/tailfi.py',D+'/pre.mir',D+'/ssc.log'],capture_output=True,text=True).stdout.split('\n')
rows=[(int(re.search(r'fi (\d+)',l).group(1)),int(re.search(r'arr (\d+)',l).group(1))) for l in out if 'arr' in l]
idx=[i for i,r in enumerate(rows) if r[1]==24]; rows=rows[idx[-1]-60 if idx else 0:]
tail={f for f,a in rows if 24<=a<=330}
lo=min(IV[f][0][0] for f in tail); hi=max(IV[f][-1][1] for f in tail)
sw=None
for i,l in enumerate(pre):
    m=re.match(r'\s+\$(r\d+) = LDD_V1 %stack\.(\d+), 0',l)
    if m and i+1<len(pre) and re.match(r'\s+STD_V1 killed \$'+m.group(1)+r', %stack\.\d+\._55\.i9\d, 184 ',pre[i+1]): sw=int(m.group(2))
def live_at(f,x): return any(a<=x<b for a,b in IV[f])
print(f'tail FIs {len(tail)} range {lo//4}-{hi//4}; swept FI {sw} colour {COL.get(sw)}')
for f in sorted(IV,key=lambda f:COL[f]):
    if f in tail: continue
    if live_at(f,lo) or live_at(f,(lo+hi)//2) or live_at(f,hi-1):
        n=sum(live_at(f,x) for x in (lo,(lo+hi)//2,hi-1))
        c=COL[f]; print(f'  SS#{f} col {c} off {hex(0x8e0+8*(c-179))} w {W.get(f,0):.2e} span {IV[f][0][0]//4}-{IV[f][-1][1]//4} live@lo/mid/hi {n}{"  <- swept" if f==sw else ""}')
