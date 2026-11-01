#!/usr/bin/env python3
"""gen.py <slim.ll> <edits.jsonl>: enumerate shim-expressible single IR edits on the pre-opt bodies of
admin_cto validate/execute/wallet/sweep (experiment only). Edit = {id,kind,cls,fn,rep:{line:[newlines]},extra:[module lines]}."""
import sys,os,re,json
FN={'validate':r'admin_cto8validate17h','execute':r'admin_cto7execute17h','wallet':r'admin_cto7execute6wallet17h','sweep':r'admin_cto7execute5sweep17h'}
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
VAL=r'(%[\w.$-]+|%"[^"]+")'
def main(src,dst):
    L=open(src).read().split('\n'); R=ranges(L); E=[]
    W={'t':'!{!"branch_weights", i32 2000, i32 1}','f':'!{!"branch_weights", i32 1, i32 2000}'}
    for fn,(a,b) in R.items():
        allocas=set(); blk='start'; blkof={}; defs={}; succ={}; order=['start']; gbase={}
        for i in range(a,b):
            l=L[i]
            m=re.match(r'^\s+'+VAL+r' = alloca ',l)
            if m: allocas.add(m.group(1))
            m=re.match(r'^\s+'+VAL+r' = getelementptr [^,]+, ptr '+VAL,l)
            if m: gbase[m.group(1)]=gbase.get(m.group(2),m.group(2))
            m=re.match(r'^("?[\w.$-]+"?):',l)
            if m: blk=m.group(1).strip('"'); order.append(blk)
            blkof[i]=blk
            m=re.match(r'^\s+'+VAL+r' = ',l)
            if m: defs[m.group(1)]=i
            if re.match(r'^\s+(br|switch|invoke|ret|unreachable|resume)\b',l) or (l.strip().startswith('i64 ') and 'label' in l):
                succ.setdefault(blk,set()).update(x.strip('"') for x in re.findall(r'label %("[^"]+"|[\w.$-]+)',l))
        # dominators (iterative)
        preds={k:set() for k in order}
        for k,v in succ.items():
            for t in v:
                if t in preds: preds[t].add(k)
        dom={k:set(order) for k in order}; dom['start']={'start'}
        ch=True
        while ch:
            ch=False
            for k in order[1:]:
                ps=[dom[p] for p in preds[k] if p in dom]
                nd=set.intersection(*ps)|{k} if ps else {k}
                if nd!=dom[k]: dom[k]=nd; ch=True
        def base(p): return gbase.get(p,p)
        for i in range(a+1,b):
            l=L[i]
            # volatile loads
            m=re.match(r'^(\s+'+VAL+r' = )load (?!volatile)([^,]+), ptr '+VAL+r'(.*)$',l)
            if m:
                p=m.group(4); cls='loc' if base(p) in allocas else ('glb' if p.startswith('@') else 'fld')
                E.append({'id':f'vl:{fn}:{i}','kind':'vload','cls':cls,'fn':fn,'rep':{i:[m.group(1)+'load volatile '+m.group(3)+', ptr '+p+m.group(5)]},'src':l.strip()[:140]})
                # rereads: non-phi uses of the loaded value in other blocks
                if cls=='fld':
                    v=m.group(2); ty=m.group(3); k=0
                    for j in range(i+1,b):
                        lj=L[j]
                        if re.search(re.escape(v)+r'(?![\w.$-])',lj) and not re.match(r'^\s+'+VAL+r' = phi',lj) and blkof.get(j)!=blkof[i]:
                            nv=v+'.rr'+str(j)
                            new=re.sub(re.escape(v)+r'(?![\w.$-])',nv,lj)
                            E.append({'id':f'rr:{fn}:{i}:{j}','kind':'reread','cls':cls,'fn':fn,'rep':{j:['  '+nv+' = load volatile '+ty+', ptr '+p+m.group(5),new]},'src':l.strip()[:80]+' @ '+lj.strip()[:60]})
                            k+=1
                            if k>=6: break
                continue
            m=re.match(r'^(\s+)store (?!volatile)(.*), ptr '+VAL+r'(.*)$',l)
            if m:
                p=m.group(3); cls='loc' if base(p) in allocas else ('glb' if p.startswith('@') else 'fld')
                E.append({'id':f'vs:{fn}:{i}','kind':'vstore','cls':cls,'fn':fn,'rep':{i:[m.group(1)+'store volatile '+m.group(2)+', ptr '+p+m.group(4)]},'src':l.strip()[:140]})
                continue
            m=re.match(r'^(\s+br i1 '+VAL+r', label %[^,]+, label %\S+)(.*)$',l)
            if m and '!prof' not in l:
                for d in 'tf':
                    E.append({'id':f'bw{d}:{fn}:{i}','kind':'bw','cls':d,'fn':fn,'rep':{i:[m.group(1)+', !prof !99000'+('1' if d=='t' else '2')+m.group(3)]},'src':l.strip()[:140]})
                continue
            m=re.match(r'^(\s+)switch (\S+) '+VAL+r', label (%\S+) \[$',l)
            if m:
                # cases follow until ']'
                j=i+1; cases=[]
                while L[j].strip()!=']': cases.append(L[j]); j+=1
                n=len(cases)+1
                for t in range(n):
                    w=['1']*n; w[t]='2000'
                    md='!{!"branch_weights", '+', '.join('i32 '+x for x in w)+'}'
                    mid=f'!99{i:05d}{t}'
                    E.append({'id':f'sw{t}:{fn}:{i}','kind':'swbw','cls':str(t),'fn':fn,'rep':{j:['  ], !prof '+mid]},'extra':[mid+' = '+md],'src':l.strip()[:100]})
                continue
            # memory fence (black_box(()) form) at block starts
            if re.match(r'^("?[\w.$-]+"?):',l):
                k=i+1
                while re.match(r'^\s+'+VAL+r' = (phi|landingpad)',L[k]): k+=1
                E.append({'id':f'bf:{fn}:{k}','kind':'fence','cls':'blk','fn':fn,'rep':{k:['  call void asm sideeffect "", "~{memory}"()',L[k]]},'src':l.split(';')[0].strip()[:60]})
        fldval={}
        for i in range(a+1,b):
            m=re.match(r'^\s+'+VAL+r' = load (?!volatile)([^,]+), ptr '+VAL+r'(.*)$',L[i])
            if m and base(m.group(3)) not in allocas and not m.group(3).startswith('@'): fldval[m.group(1)]=(m.group(2),m.group(3),m.group(4),i)
        cpy={}
        for i in range(a+1,b):
            m=re.match(r'^\s+store (?!volatile)(\S+) '+VAL+r', ptr '+VAL,L[i])
            if m and m.group(2) in fldval and base(m.group(3)) in allocas:
                ty,P,rest,li=fldval[m.group(2)]
                if ty==m.group(1): cpy.setdefault(m.group(3),[]).append((P,ty,rest,i))
        for A,lst in cpy.items():
            if len(lst)!=1: continue
            P,ty,rest,si=lst[0]; pdef=defs.get(P); k=0
            for j in range(si+1,b):
                m=re.match(r'^(\s+'+VAL+r' = )load (?!volatile)'+re.escape(ty)+r', ptr '+re.escape(A)+r'(,.*)?$',L[j])
                if not m: continue
                if blkof[j]==blkof[si]: continue
                if pdef is not None and blkof[pdef] not in dom.get(blkof[j],set()): continue
                E.append({'id':f'rc:{fn}:{si}:{j}','kind':'reread','cls':'copy','fn':fn,'rep':{j:[m.group(1)+'load volatile '+ty+', ptr '+P+rest]},'src':L[si].strip()[:70]+' @ '+L[j].strip()[:60]})
                k+=1
                if k>=6: break
        # noalias / attribute drops on params of validate, wallet, sweep (def + call sites)
        if fn!='execute':
            hdr=L[a]; name=re.search(r'@[\w.$-]+|@"[^"]+"',hdr).group(0)
            ps=hdr[hdr.index(name)+len(name)+1:]
            depth=1; k=0
            while depth: 
                if ps[k]=='(': depth+=1
                elif ps[k]==')': depth-=1
                k+=1
            plist=ps[:k-1]
            parts=[]; d=0; cur=''
            for ch in plist:
                if ch in '([{': d+=1
                elif ch in ')]}': d-=1
                if ch==',' and d==0: parts.append(cur); cur=''
                else: cur+=ch
            parts.append(cur)
            for pi,p in enumerate(parts):
                if not p.strip().startswith('ptr'): continue
                for mode in ('noalias','raw'):
                    def strip(s,mode=mode):
                        if mode=='noalias': return re.sub(r'\bnoalias ','',s)
                        s=re.sub(r'\b(noalias|readonly|nonnull|nocapture) ','',s); s=re.sub(r'\b(dereferenceable|dereferenceable_or_null|align) \(?\d+\)? ?','',s)
                        s=re.sub(r'dereferenceable\(\d+\) ','',s); return s
                    np=strip(p)
                    if np==p: continue
                    newhdr=hdr.replace(plist,','.join(parts[:pi]+[np]+parts[pi+1:]),1)
                    rep={a:[newhdr]}
                    # call sites in all 4 functions
                    for fn2,(a2,b2) in R.items():
                        for i2 in range(a2+1,b2):
                            l2=L[i2]
                            if name+'(' in l2 and 'call' in l2:
                                cs=l2[l2.index(name+'(')+len(name)+1:]
                                d=1;k2=0
                                while d:
                                    if cs[k2]=='(': d+=1
                                    elif cs[k2]==')': d-=1
                                    k2+=1
                                al=cs[:k2-1]; aps=[]; d=0; cur=''
                                for ch in al:
                                    if ch in '([{': d+=1
                                    elif ch in ')]}': d-=1
                                    if ch==',' and d==0: aps.append(cur); cur=''
                                    else: cur+=ch
                                aps.append(cur)
                                if pi<len(aps):
                                    aps[pi]=strip(aps[pi]); rep[i2]=[l2.replace(al,','.join(aps),1)]
                    E.append({'id':f'na{mode[0]}:{fn}:{pi}','kind':'noalias','cls':mode,'fn':fn,'rep':rep,'src':p.strip()[:100]})
    with open(dst,'w') as f:
        for e in E: f.write(json.dumps(e)+'\n')
    import collections
    print(len(E),collections.Counter((e['kind'],e['cls']) for e in E))
if __name__=='__main__': main(*sys.argv[1:])
