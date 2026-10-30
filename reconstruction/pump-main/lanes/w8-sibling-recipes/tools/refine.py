"""Refine ambiguous pairs by callee consistency + pointee bytes; dump rodata offset map."""
import sys, json, struct, bisect, hashlib
from collections import defaultdict, Counter
sys.path.insert(0,__file__.rsplit('/',1)[0])
import census as C
from pathlib import Path
cpath=Path(sys.argv[1]); outp=Path(sys.argv[2])
orig=(C.BASE/'original.so').read_bytes(); osec=C.sections(orig)
cand=cpath.read_bytes(); csec=C.sections(cand)
wins=C.original_windows(); winfo={w['start']:w for w in wins}; ostarts=sorted(winfo)
byaddr={}
for a,s,n in C.candidate_functions(cpath): byaddr.setdefault(a,(a,s,[]))[2].append(n)
cinfo={a:(s,n) for a,s,n in byaddr.values()}; cstarts=sorted(cinfo)
craw={a:C.body(cand,csec,a,cinfo[a][0]) for a in cstarts}
cls=defaultdict(list)
for a in cstarts: cls[(cinfo[a][0],hashlib.sha256(C.normalize(craw[a],a,csec)).digest())].append(a)
ocls=defaultdict(list)
for w in wins: ocls[(w['bytes'],hashlib.sha256(w['norm']).digest())].append(w['start'])
def owin(x):
    i=bisect.bisect_right(ostarts,x)-1; return ostarts[i] if i>=0 else None
def cfn(x):
    i=bisect.bisect_right(cstarts,x)-1; return cstarts[i] if i>=0 else None
def pointee(blob,secs,v,n=24):
    for nm,s in secs.items():
        if s['addr']>0 and s['addr']<=v<s['addr']+s['size'] and nm!='.text':
            o=v-s['addr']+s['offset']; return nm,blob[o:o+n]
    return None
oops={s:C.operands(winfo[s]['raw'],s,osec) for s in ostarts}
cops={a:C.operands(craw[a],a,csec) for a in cstarts}
pair={}
for k,ws in ocls.items():
    cs=sorted(cls.get(k,[])); ws=sorted(ws); used=set()
    for s in ws:
        for a in cs:
            if a not in used and craw[a]==winfo[s]['raw']: pair[s]=a; used.add(a); break
    rest=[a for a in cs if a not in used]
    for s in ws:
        if s not in pair and rest: pair[s]=rest.pop(0)
def sim(s,a,pair):
    sc=0
    for x,y in zip(oops[s],cops[a]):
        if x[1]=='call':
            if pair.get(owin(x[2]))==cfn(y[2]): sc+=2
        else:
            if x[3]=='.text':
                if pair.get(owin(x[2]))==cfn(y[2]): sc+=2
            else:
                p=pointee(orig,osec,x[2]); q=pointee(cand,csec,y[2])
                if p and q and p[1]==q[1]: sc+=1
    return sc
for it in range(4):
    newp={k:v for k,v in pair.items()}
    for k,ws in ocls.items():
        cs=cls.get(k,[])
        if not cs or (len(ws)==1 and len(cs)==1): continue
        cand_pairs=sorted(((sim(s,a,pair)+(1000 if craw[a]==winfo[s]['raw'] else 0),pair.get(s)==a,s,a) for s in ws for a in cs),reverse=True)
        us,ua=set(),set()
        for sc,_,s,a in cand_pairs:
            if s in us or a in ua: continue
            # prefer raw-equal
            newp[s]=a; us.add(s); ua.add(a)
    pair=newp
for s,rx in C.UNMATCHED_NAMES.items():
    import re
    hits=[a for a in cstarts if any(re.search(rx,n) for n in cinfo[a][1])]
    if hits: pair[s]=hits[0]
# order
seq=[(s,pair[s]) for s in ostarts if s in pair]
vals=[c for _,c in seq]
tails,tidx,prev=[],[],[-1]*len(vals)
for i,v in enumerate(vals):
    j=bisect.bisect_left(tails,v)
    if j==len(tails): tails.append(v); tidx.append(i)
    else: tails[j]=v; tidx[j]=i
    prev[i]=tidx[j-1] if j>0 else -1
lis=set();k=tidx[-1]
while k>=0: lis.add(k); k=prev[k]
ooo=[(hex(seq[i][0]),hex(seq[i][1]),winfo[seq[i][0]]['bytes'],cinfo[seq[i][1]][1][0]) for i in range(len(seq)) if i not in lis]
# operand census and rodata map
calls=Counter(); ld=Counter(); romap=Counter(); drmap=Counter(); badcalls=[]
for s in ostarts:
    a=pair.get(s)
    if a is None or s in C.UNMATCHED_NAMES: continue
    for x,y in zip(oops[s],cops[a]):
        if x[1]=='call':
            if x[3]==y[3]: calls['same_imm']+=1
            elif pair.get(owin(x[2]))==cfn(y[2]): calls['same_callee']+=1
            else: calls['diff_callee']+=1; badcalls.append((hex(s),hex(x[2]),hex(y[2])))
        else:
            if x[2]==y[2]: ld['same_value']+=1; continue
            if x[3]=='.text': ld['text']+=1; continue
            oo=x[2]-osec[x[3]]['addr']; co=y[2]-csec[y[3]]['addr']
            ld[(x[3],y[3],oo==co)]+=1
            if x[3]=='.rodata': romap[(oo,co)]+=1
            else: drmap[(oo,co)]+=1
json.dump({'pair':{hex(k):hex(v) for k,v in pair.items()},'ooo':ooo,'calls':dict(calls),'lddw':{str(k):v for k,v in ld.items()},
  'badcalls':badcalls,'romap':sorted([o,c,n] for (o,c),n in romap.items()),'drmap':sorted([o,c,n] for (o,c),n in drmap.items())},open(outp,'w'),indent=0)
print('lis',len(lis),'ooo',len(ooo)); print(calls); print(ld); print('badcalls',len(badcalls))
