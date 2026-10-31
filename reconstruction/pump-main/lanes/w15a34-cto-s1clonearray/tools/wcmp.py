#!/usr/bin/env python3
"""wcmp.py <ref> <var>...: initial greedy spill weights (RAPRIO_LOG Q lines) of the sharing-arm vreg family, variant vs ref.
Matches vregs by number when the arm's IR is the same (ref family list); prints identical count, max |w ratio - 1| on the
clone pieces (finite weights) and the per-clone piece weights when they differ."""
import sys,os,subprocess
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a34-cto-s1clonearray'
L='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a18-cto-s1greedy/llvmb/bin/llc'
def ralog(n):
    p=f'{O}/tmp/{n}.ralog'
    if not os.path.exists(p):
        env=dict(os.environ); env['RAPRIO_LOG']=p
        subprocess.run([L,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',f'{O}/rx/{n}/m.ll','-stop-after=greedy','-o','/dev/null'],env=env,check=True,capture_output=True)
    d={}
    for l in open(p):
        f=l.split()
        if f and f[0]=='Q':
            v=int(f[1])
            if v in d: continue
            kv=dict(x.split('=',1) for x in f[2:] if '=' in x); d[v]=(int(kv['sz']),float(kv['w']))
    return d
def fam(n):
    p=f'{O}/tmp/{n}.fam'
    if not os.path.exists(p):
        subprocess.run([L,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',f'{O}/rx/{n}/m.ll','-stop-before=greedy','-o',f'{O}/tmp/{n}.pregreedy.mir'],check=True,capture_output=True)
        open(p,'w').write(subprocess.run(['python3',f'{O}/tools/famvregs.py',f'{O}/tmp/{n}.pregreedy.mir'],capture_output=True,text=True).stdout)
    return [int(x) for x in open(p).read().split()]
ref=sys.argv[1]; R=ralog(ref); F=fam(ref)
print(f'{ref}: family {len(F)} vregs')
for n in sys.argv[2:]:
    V=ralog(n); Fv=fam(n)
    both=[v for v in F if v in R and v in V]; same=sum(1 for v in both if R[v]==V[v])
    rs=[V[v][1]/R[v][1] for v in both if R[v]!=V[v] and 0<R[v][1]<1e30 and 0<V[v][1]<1e30]
    dev=max((abs(r-1) for r in rs),default=0.0)
    print(f'{n}: family {len(Fv)} vregs; same-number vregs {len(both)}; identical size+weight {same}; max |w ratio-1| {dev:.4f}'
          +('' if len(Fv)==len(F) else '  (family size differs)'))
