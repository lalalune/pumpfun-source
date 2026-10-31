#!/usr/bin/env python3
"""rolew.py <ref> <var>...: role-matched spill weights of the sharing-arm clone pieces. Role = (clone account, occurrence,
field offset): account from the AccountInfo pointer load (accounts+off, Box deref for global), field from the piece load.
Prints per variant: pieces matched, identical (size,weight), max |w ratio-1|, and the weight-rank order of the 8 clones."""
import sys,os,re,subprocess
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a34-cto-s1clonearray'
sys.path.insert(0,O+'/tools'); import importlib.util as iu
spec=iu.spec_from_file_location('wcmp',O+'/tools/wcmp.py')
def load(n):
    w=__import__('subprocess')
    import runpy
    g=runpy.run_path(O+'/tools/wcmp.py',run_name='lib')
    return g
G=runpy=None
import runpy
src=open(O+'/tools/wcmp.py').read().split("ref=sys.argv[1]")[0]; G={}; exec(src,G)
ACC={104:'pa',0:'au',8:'gl',16:'mi',144:'sc',160:'ev',152:'pr'}
FLD={0:'key',8:'lam',16:'dat',24:'own',32:'rent',40:'sig',41:'wr',42:'ex'}
def roles(n):
    G['fam'](n); t=open(f'{O}/tmp/{n}.pregreedy.mir').read().split('\n')
    body=max(i for i,l in enumerate(t) if l.startswith('body:'))
    call=[i for i,l in enumerate(t) if i>body and 'JAL @' in l and 'admin_cto_sharing_config' in l][0]
    defs={}
    for i in range(body,call):
        m=re.match(r'\s+%(\d+):gpr = (LD[DBWH])_V1 %(\d+), (-?\d+)',t[i])
        if m: defs[int(m.group(1))]=(m.group(2),int(m.group(3)),int(m.group(4)),i)
    # account pointer vregs: LDD %0, off (direct) or LDD (LDD %0, 8), 0 (global box)
    ptr={}
    for v,(op,b,off,i) in defs.items():
        if op=='LDD' and b==0 and off in ACC and off!=8: ptr[v]=(ACC[off],i)
        if op=='LDD' and off==0 and b in defs and defs[b][1]==0 and defs[b][2]==8: ptr[v]=('gl',i)
    # arm window: pieces loaded from pointer vregs defined after the arm start
    start=min(i for (_,i) in ptr.values() if i> call-700) if ptr else 0
    occ={}; R={}
    for v,(a,i) in sorted(ptr.items(),key=lambda x:x[1][1]):
        if i<start: continue
        occ[a]=occ.get(a,0)+1; tag=a+str(occ[a])
        for u,(op,b,off,j) in defs.items():
            if b==v and off in FLD: R[(tag,FLD[off])]=u
    return R
ref=sys.argv[1]; Rr=roles(ref); Wr=G['ralog'](ref)
print(f'{ref}: {len(Rr)} role pieces')
for n in sys.argv[2:]:
    Rv=roles(n); Wv=G['ralog'](n)
    both=[k for k in Rr if k in Rv and Rr[k] in Wr and Rv[k] in Wv]
    same=sum(1 for k in both if Wr[Rr[k]]==Wv[Rv[k]])
    rs=[(Wv[Rv[k]][1]/Wr[Rr[k]][1],k) for k in both if Wr[Rr[k]][1]>0]
    dev=max(rs,key=lambda x:abs(x[0]-1)) if rs else (1,None)
    print(f'{n}: role pieces {len(Rv)} matched {len(both)} identical {same} max w ratio {dev[0]:.3f} at {dev[1]}')
if os.environ.get('PERCLONE'):
    for n in sys.argv[2:]:
        Rv=roles(n); Wv=G['ralog'](n)
        acc={}
        for k in Rr:
            if k in Rv and Rr[k] in Wr and Rv[k] in Wv and Wr[Rr[k]][1]>0:
                acc.setdefault(k[0],[]).append(Wv[Rv[k]][1]/Wr[Rr[k]][1])
        print(n,' '.join(f'{a}:{min(v):.2f}-{max(v):.2f}' for a,v in acc.items()))
