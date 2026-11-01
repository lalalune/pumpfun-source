#!/usr/bin/env python3
"""ptgen.py <slim.ll> <edits.jsonl>: enumerate llvm.bpf.passthrough insertions on the pre-opt bodies of admin_cto
validate/execute/wallet/sweep (experiment only). kinds: pt (all uses of a value through one passthrough),
pb (only the br condition use). Output format matches w17a06 screen.py."""
import sys,re,json
FN={'validate':r'admin_cto8validate17h','execute':r'admin_cto7execute17h','wallet':r'admin_cto7execute6wallet17h','sweep':r'admin_cto7execute5sweep17h'}
VAL=r'(%[\w.$-]+|%"[^"]+")'
TY={'i1','i8','i16','i32','i64','ptr'}
FLAGS={'nuw','nsw','exact','disjoint','volatile','inbounds','fast','nnan','ninf','nneg'}
def mang(t): return 'p0' if t=='ptr' else t
def decl(t): return f'declare {t} @llvm.bpf.passthrough.{mang(t)}.{mang(t)}(i32, {t})'
def call(nv,t,seq,v): return f'  {nv} = call {t} @llvm.bpf.passthrough.{mang(t)}.{mang(t)}(i32 {seq}, {t} {v})'
def ranges(L):
    R={}
    for i,l in enumerate(L):
        if l.startswith('define '):
            for k,p in FN.items():
                if re.search(p,l.split('(')[0]):
                    j=i
                    while L[j]!='}': j+=1
                    R[k]=(i,j)
    return R
def vtype(l):
    m=re.match(r'^\s+'+VAL+r' = (\w+)(.*)$',l)
    if not m: return None,None
    op=m.group(2); rest=m.group(3).split()
    if op=='icmp' or op=='fcmp': return op,'i1'
    if op in('trunc','zext','sext','ptrtoint','inttoptr','bitcast'):
        t=l.split(' to ')[-1].split(',')[0].strip(); return op,t
    if op=='select':
        # select i1 %c, T %a, T %b
        s=m.group(3).strip(); parts=s.split(',')
        if len(parts)>=2: return op,parts[1].split()[0]
        return op,None
    if op=='call': return op,None
    toks=[x for x in rest if x not in FLAGS]
    if not toks: return op,None
    return op,toks[0].rstrip(',')
def main(src,dst):
    L=open(src).read().split('\n'); R=ranges(L); E=[]; seq=1000
    for fn,(a,b) in R.items():
        blkstart={}; cur=a
        for i in range(a+1,b):
            if re.match(r'^("?[\w.$-]+"?):',L[i]): cur=i
            blkstart[i]=cur
        for i in range(a+1,b):
            l=L[i]
            op,t=vtype(l)
            if op is None or t not in TY: continue
            if op in('alloca','getelementptr'): continue
            v=re.match(r'^\s+'+VAL,l).group(1); seq+=1
            nv=f'%ptv{seq}'
            pat=re.compile(re.escape(v)+r'(?![\w.$-])')
            ins=i
            if op=='phi':
                k=i
                while re.match(r'^\s+'+VAL+r' = phi',L[k+1]): k+=1
                ins=k
            rep={}; uses=[]
            for j in range(a+1,b):
                if j==i: continue
                if pat.search(L[j]): uses.append(j)
            if not uses: continue
            for j in uses:
                rep[j]=[pat.sub(nv,L[j])]
            if ins in rep: rep[ins]=rep[ins]+[call(nv,t,seq,v)]
            else: rep[ins]=[L[ins],call(nv,t,seq,v)]
            E.append({'id':f'pt:{fn}:{i}','kind':'pt','cls':op,'fn':fn,'rep':rep,'extra':[decl(t)],'src':l.strip()[:120],'nuses':len(uses)})
            # branch-condition-only form for multi-use i1 values used by a br
            if t=='i1':
                for j in uses:
                    m=re.match(r'^(\s+br i1 )'+re.escape(v)+r'(, label .*)$',L[j])
                    if m and len(uses)>1:
                        seq+=1; nv2=f'%pbv{seq}'
                        E.append({'id':f'pb:{fn}:{j}','kind':'pb','cls':op,'fn':fn,'rep':{j:[call(nv2,'i1',seq,v),m.group(1)+nv2+m.group(2)]},'extra':[decl('i1')],'src':l.strip()[:120]})
    with open(dst,'w') as f:
        for e in E: f.write(json.dumps(e)+'\n')
    import collections
    print(len(E), collections.Counter((e['fn'],e['kind']) for e in E))
if __name__=='__main__': main(*sys.argv[1:])
