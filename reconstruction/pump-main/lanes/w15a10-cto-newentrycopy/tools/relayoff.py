# relayoff.py <in.s> <out.s> <ranges>: ranges "lo-hi,lo-hi,..." (hex byte offsets per lay.py) concatenated in the given order
import sys,re,importlib.util,subprocess,os
T='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a10-cto-newentrycopy/t93'
sv=sys.argv; sys.argv=['x']
sp=importlib.util.spec_from_file_location('relay',T+'/relay.py'); R=importlib.util.module_from_spec(sp); sp.loader.exec_module(R); sys.argv=sv
src,dst,rs=sv[1:4]
pre,bl,post=R.parse(src)
offs=[];o=0
for n,b in bl:
    offs.append(o)
    for l in b[1:]:
        s=l.strip()
        if s and not s.startswith(('#','.')) and not re.match(r'^\S+:',l): o+= 16 if s.startswith('lddw') else 8
names=[]
for r in rs.split(','):
    lo,hi=[int(x,16) for x in r.split('-')]
    names+= [bl[i][0] for i in range(len(bl)) if lo<=offs[i]<hi]
r=subprocess.run(['python3',T+'/relay.py',src,dst,','.join(names)],capture_output=True,text=True,cwd=T)
print(r.stdout.strip()[-400:], r.stderr[-400:])
