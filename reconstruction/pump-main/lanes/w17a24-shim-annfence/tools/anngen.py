#!/usr/bin/env python3
"""anngen.py <slim.ll> <edits.jsonl> [families]: enumerate llvm.annotation / llvm.ptr.annotation / llvm.sideeffect
insertions on the pre-opt bodies of admin_cto validate/execute/wallet/sweep (experiment only).
families (comma list, default ai,ap,au,se):
  ai  int annotation after an iN def, ALL uses rerouted through it
  ap  ptr annotation after a ptr def (GEP not alloca-based, load, phi, select, call, extractvalue), ALL uses rerouted
  ax  like ai/ap but only the uses OUTSIDE the def block are rerouted (the ann sits in the def block)
  au  unused-result annotation right after the def (anchor)
  se  llvm.sideeffect at a block head (after phis)
Output format matches w17a06 screen.py."""
import sys,re,json,collections
FN={'validate':r'admin_cto8validate17h','execute':r'admin_cto7execute17h','wallet':r'admin_cto7execute6wallet17h','sweep':r'admin_cto7execute5sweep17h'}
VAL=r'(%[\w.$-]+|%"[^"]+")'
ITY={'i1','i8','i16','i32','i64'}
FLAGS={'nuw','nsw','exact','disjoint','volatile','inbounds','fast','nnan','ninf','nneg','tail','notail','musttail'}
def idecl(t): return f'declare {t} @llvm.annotation.{t}.p0({t}, ptr, ptr, i32)'
PDECL='declare ptr @llvm.ptr.annotation.p0.p0(ptr, ptr, ptr, i32, ptr)'
SDECL='declare void @llvm.sideeffect()'
def icall(nv,t,v,tag): return (f'  {nv} = ' if nv else '  ')+f'call {t} @llvm.annotation.{t}.p0({t} {v}, ptr null, ptr null, i32 {tag})'
def pcall(nv,v,tag): return (f'  {nv} = ' if nv else '  ')+f'call ptr @llvm.ptr.annotation.p0.p0(ptr {v}, ptr null, ptr null, i32 {tag}, ptr null)'
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
    op=m.group(2); rest=m.group(3).strip()
    if op in('icmp','fcmp'): return op,'i1'
    if op in('trunc','zext','sext','ptrtoint','inttoptr','bitcast'):
        return op,l.split(' to ')[-1].split(',')[0].split()[0].strip()
    if op=='getelementptr': return op,'ptr'
    if op=='alloca': return op,None
    if op=='select':
        parts=rest.split(',')
        return op,(parts[1].split()[0] if len(parts)>=2 else None)
    if op=='call':
        toks=[x for x in rest.split() if x not in FLAGS and x not in ('noundef','zeroext','signext','nonnull','noalias','fastcc','coldcc') and not x.startswith(('align','dereferenceable','range('))]
        return op,(toks[0] if toks else None)
    if op=='extractvalue':
        return op,None  # aggregate member type not parsed
    toks=[x for x in rest.split() if x not in FLAGS]
    if not toks: return op,None
    return op,toks[0].rstrip(',')
def main(src,dst,fams='ai,ap,au,se'):
    fams=set(fams.split(','))
    L=open(src).read().split('\n'); R=ranges(L); E=[]; tag=0
    for fn,(a,b) in R.items():
        blkof={}; cur='start'; allocas=set(); gbase={}; heads=[]
        for i in range(a+1,b):
            m=re.match(r'^("?[\w.$-]+"?):',L[i])
            if m: cur=m.group(1); heads.append(i)
            blkof[i]=cur
            m=re.match(r'^\s+'+VAL+r' = alloca ',L[i])
            if m: allocas.add(m.group(1))
            m=re.match(r'^\s+'+VAL+r' = getelementptr [^,]+, ptr '+VAL,L[i])
            if m: gbase[m.group(1)]=gbase.get(m.group(2),m.group(2))
        def base(p): return gbase.get(p,p)
        for i in range(a+1,b):
            l=L[i]; op,t=vtype(l)
            if op is None: continue
            if t not in ITY and t!='ptr': continue
            v=re.match(r'^\s+'+VAL,l).group(1)
            if t=='ptr' and op=='getelementptr':
                m=re.match(r'^\s+'+VAL+r' = getelementptr [^,]+, ptr '+VAL,l)
                if m and base(m.group(2)) in allocas: continue
            pat=re.compile(re.escape(v)+r'(?![\w.$-])')
            ins=i
            if op=='phi':
                k=i
                while re.match(r'^\s+'+VAL+r' = phi',L[k+1]): k+=1
                ins=k
            uses=[j for j in range(a+1,b) if j!=i and pat.search(L[j])]
            if not uses: continue
            xuses=[j for j in uses if blkof.get(j)!=blkof.get(i) or re.match(r'^\s+'+VAL+r' = phi',L[j])]
            fam='ap' if t=='ptr' else 'ai'
            for kind,us in ((fam,uses),('ax',xuses)):
                if kind not in fams or not us: continue
                if kind=='ax' and len(xuses)==len(uses) and fam in fams: continue  # identical to the all-uses edit
                tag+=1; nv=f'%anv{tag}'
                rep={j:[pat.sub(nv,L[j])] for j in us}
                c=pcall(nv,v,tag) if t=='ptr' else icall(nv,t,v,tag)
                if ins in rep: rep[ins]=rep[ins]+[c]
                else: rep[ins]=[L[ins],c]
                E.append({'id':f'{kind}:{fn}:{i}','kind':kind,'cls':op+':'+t,'fn':fn,'rep':rep,'extra':[PDECL if t=='ptr' else idecl(t)],'src':l.strip()[:120],'nuses':len(us),'xuses':len(xuses)})
            if 'au' in fams:
                tag+=1
                c=pcall(None,v,tag) if t=='ptr' else icall(None,t,v,tag)
                c=c.replace('  call','  call',1)
                # unused result: use a fresh name so the textual IR stays valid
                c=c.replace('  call',f'  %anu{tag} = call',1)
                E.append({'id':f'au:{fn}:{i}','kind':'au','cls':op+':'+t,'fn':fn,'rep':{ins:[L[ins],c]},'extra':[PDECL if t=='ptr' else idecl(t)],'src':l.strip()[:120],'nuses':len(uses),'xuses':len(xuses)})
        if 'se' in fams:
            for h in heads:
                k=h
                while re.match(r'^\s+'+VAL+r' = phi',L[k+1]): k+=1
                E.append({'id':f'se:{fn}:{h}','kind':'se','cls':'blk','fn':fn,'rep':{k:[L[k],'  call void @llvm.sideeffect()']},'extra':[SDECL],'src':L[h].strip()[:80]})
    with open(dst,'w') as f:
        for e in E: f.write(json.dumps(e)+'\n')
    print(len(E), collections.Counter((e['fn'],e['kind']) for e in E))
if __name__=='__main__': main(*sys.argv[1:])
