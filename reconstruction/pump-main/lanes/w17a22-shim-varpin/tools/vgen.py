#!/usr/bin/env python3
"""vgen.py <slim.ll> <edits.jsonl>: one llvm.var.annotation pin per alloca of admin_cto validate/execute/wallet/sweep
(experiment only). Placements: A = right after the alloca's first write (store / memcpy dest / call arg),
B = right before the first non-intrinsic call after that write (the value must then live in memory across it),
C = right after the alloca's lifetime.start (or entry when it has none).
Edit format matches gen.py/screen.py: {id,kind,cls,fn,rep:{line:[newlines]},extra:[module lines]}."""
import sys,re,json
FN={'validate':r'admin_cto8validate17h','execute':r'admin_cto7execute17h','wallet':r'admin_cto7execute6wallet17h','sweep':r'admin_cto7execute5sweep17h'}
DECL='declare void @llvm.var.annotation.p0.p0(ptr, ptr, ptr, i32, ptr)'
VAL=r'(%[\w.$-]+|%"[^"]+")'
def ann(p): return f'  call void @llvm.var.annotation.p0.p0(ptr {p}, ptr null, ptr null, i32 0, ptr null)'
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
INTR=re.compile(r'call [^@]*@llvm\.(lifetime|memcpy|memset|memmove|dbg|assume|expect|var\.annotation)')
def main(src,dst,places='ABC'):
    L=open(src).read().split('\n'); R=ranges(L); E=[]
    for fn,(a,b) in R.items():
        allocas=[]; derived={}
        for i in range(a,b):
            m=re.match(r'^\s+'+VAL+r' = alloca ',L[i])
            if m: allocas.append((m.group(1),i))
        names={x for x,_ in allocas}
        # derived pointers (GEPs / bitcasts of an alloca, transitively)
        for i in range(a,b):
            m=re.match(r'^\s+'+VAL+r' = getelementptr (?:inbounds )?[^,]+, ptr '+VAL,L[i])
            if m:
                base=m.group(2); base=derived.get(base,base)
                if base in names: derived[m.group(1)]=base
        users={x:[] for x in names}
        for i in range(a+1,b):
            l=L[i]
            if re.match(r'^\s+'+VAL+r' = alloca ',l): continue
            for v in set(re.findall(r'%[\w.$-]+|%"[^"]+"',l)):
                base=v if v in names else derived.get(v)
                if base is not None and not re.match(r'^\s+'+re.escape(v)+r' = getelementptr',l): users[base].append(i)
        for x,ai in allocas:
            U=sorted(set(users[x]))
            if not U: continue
            ls=[i for i in U if 'llvm.lifetime.start' in L[i]]
            w=[i for i in U if 'llvm.lifetime' not in L[i]]
            if not w: continue
            first=w[0]
            def ok_after(i):
                s=L[i].strip()
                return not re.match(r'^(br|switch|ret|unreachable|resume)\b',s) and not re.match(r'^'+VAL+r' = phi',s)
            pts={}
            if 'A' in places and ok_after(first): pts['A']=first+1
            if 'B' in places:
                k=first+1; blk=None
                while k<b:
                    s=L[k]
                    if re.match(r'^\s+(%\S+ = )?(tail )?call ',s) and not INTR.search(s): break
                    k+=1
                if k<b and k>first: pts['B']=k
            if 'C' in places:
                pts['C']=(ls[0]+1) if ls else None
                if pts['C'] is None:
                    # entry block: right after the last alloca line
                    k=a+1
                    while re.match(r'^\s+'+VAL+r' = alloca ',L[k]) or L[k].strip()=='start:': k+=1
                    pts['C']=k
            seen=set()
            for pl,pos in pts.items():
                if pos is None or pos in seen: continue
                seen.add(pos)
                E.append({'id':f'va{pl}:{fn}:{x}','kind':'vann','cls':pl,'fn':fn,'rep':{pos:[ann(x),L[pos]]},'extra':[DECL],'src':L[ai].strip()[:80]+' @ '+L[pos].strip()[:60]})
    with open(dst,'w') as f:
        for e in E: f.write(json.dumps(e)+'\n')
    import collections
    print(len(E),collections.Counter((e['fn'],e['cls']) for e in E))
if __name__=='__main__': main(*sys.argv[1:])
