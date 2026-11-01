import sys,os,collections
sys.path.insert(0,os.path.dirname(__file__))
import shape,srcmap
from win_dm import dm
exec(open(os.path.join(os.path.dirname(__file__),'q1.py')).read().split('by=collections')[0])  # reuse res
by=collections.defaultdict(list)
for w,a,cls,d,s in res: by[w].append((a,cls,d))
names={w[0]:(w[2][0] if w[2] else 'admin_cto') for w in shape.windows()}
rows=[]
for w,v in by.items():
    r=sum(1 for a,c,d in v if c=='A_reload_fp'); rows.append((r,len(v),w))
rows.sort(key=lambda x:(-x[0],-x[1]))
for r,n,w in rows:
    if r==0: break
    print(f'## {w:#08x} {dm(names[w])[:100]}  reload-per-clone {r}/{n} clones')
    for a,c,d in by[w]:
        if c!='A_reload_fp': continue
        u=srcmap.userloc(a-0) if w!=0x22a10 else None
        src=(srcmap.srcline(u[0],u[1]).strip()[:0] if False else '') 
        if u:
            line=srcmap.srcline(u[0],u[1]); col=u[2]
            snip=line[max(0,col-1):col+110].strip()
            print(f'   +{a-w:#06x} {d[:60]:60s} {u[0].split("/")[-1]}:{u[1]}:{col}  {snip}')
        else: print(f'   +{a-w:#06x} {d[:60]}')
