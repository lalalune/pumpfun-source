#!/usr/bin/env python3
"""amove.py <in xdir> <out xdir> <alloca>:<after-alloca> ... : move static allocas inside execute's entry block of ex.ll
(IR-only frame experiment), then llc + ratio + frame map via xo.sh. 'after' may be ^ (first) or $ (last alloca)."""
import sys,re,subprocess,os
src,dst=sys.argv[1],sys.argv[2]; T=os.path.dirname(os.path.abspath(__file__))
L=open(src+'/ex.ll').read().split('\n')
f=next(i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l)
for mv in sys.argv[3:]:
    a,b=mv.split(':')
    ia=next(i for i in range(f,len(L)) if L[i].strip().startswith(f'%{a} = alloca'))
    line=L.pop(ia)
    allocs=[i for i in range(f,f+3000) if re.match(r'\s+%\S+ = alloca',L[i])]
    if b=='^': ib=allocs[0]
    elif b=='$': ib=allocs[-1]+1
    else: ib=next(i for i in allocs if L[i].strip().startswith(f'%{b} = alloca'))+1
    L.insert(ib,line)
os.makedirs(dst,exist_ok=True); open(dst+'/in.ll','w').write('\n'.join(L))
r=subprocess.run(['bash',T+'/xo.sh',dst+'/in.ll',dst,'mir'],capture_output=True,text=True); print(r.stdout.strip(),r.stderr[-300:])
os.remove(dst+'/in.ll'); os.path.exists(dst+'/ex.bc') and os.remove(dst+'/ex.bc')
