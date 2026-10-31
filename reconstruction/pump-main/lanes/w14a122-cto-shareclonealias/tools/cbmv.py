#!/usr/bin/env python3
"""cbmv.py <m.ll> <out.jsonl> [radius] [procs]: cross-block field-load placement oracle for the sharing CPI clone run.
Each 'field load' (a load in bb35..the admin_cto_sharing_config call whose value is only stored into the CPI
AccountInfo pieces), together with its private gep, is moved to the top or the bottom (before the terminator) of every
chain block within RADIUS chain blocks, then llc + score (px2). Oracle only: a move across an Rc clone of the SAME
literal is a literal field reorder in source; a move across another clone is a let-binding/clone-order change."""
import sys,os,re,json,multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import px2
src,outp=sys.argv[1],sys.argv[2]; R=int(sys.argv[3]) if len(sys.argv)>3 else 4; P=int(sys.argv[4]) if len(sys.argv)>4 else 3
L=open(src).read().split('\n')
f0=next(i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l)
s=next(i for i in range(f0,len(L)) if L[i].startswith('bb35:'))
e=next(i for i in range(s,len(L)) if 'admin_cto_sharing_config17' in L[i] and 'call' in L[i])
fend=next(i for i in range(e,len(L)) if L[i]=='}')
body='\n'.join(L[f0:fend])
def uses(v): return len(re.findall(re.escape(v)+r'(?![\w.])',body))-1
# chain blocks (non-trap) in [s,e]
blocks=[]; i=s
while i<=e:
    if L[i] and not L[i].startswith(' ') and L[i].rstrip().endswith(tuple([':']) ) or (L[i] and not L[i].startswith(' ') and ': ' in L[i] and L[i].split(':')[0] and '; preds' in L[i]):
        j=i+1
        while j<len(L) and L[j].startswith(' '): j+=1
        trap=any('llvm.trap' in L[k] for k in range(i,j))
        if not trap: blocks.append((i,j-1))
        i=j; continue
    i+=1
units=[]
for i in range(s,e):
    m=re.match(r'  (%[\w.]+) = load (i8|i64|ptr), ptr (%[\w.]+), align',L[i])
    if not m: continue
    v,ty,p=m.groups()
    ul=[l for l in L[s:fend] if re.search(re.escape(v)+r'(?![\w.])',l) and not l.startswith('  '+v+' =')]
    if not(len(ul)==1 and ul[0].lstrip().startswith('store') and ('_122.sroa' in ul[0] or '_121.sroa' in ul[0] or '%v668' in ul[0] or '%v669' in ul[0])): continue
    lines=[i]
    if i>0 and L[i-1].startswith('  '+p+' = getelementptr') and uses(p)==1: lines=[i-1,i]
    base=re.search(r'getelementptr inbounds i8, ptr (%[\w.]+)',L[lines[0]]) if len(lines)==2 else None
    base=base.group(1) if base else p
    bi=next(k for k,(a,b) in enumerate(blocks) if a<=i<=b)
    units.append((lines,base,bi,v))
def defline(v):
    for k in range(f0,fend):
        if L[k].startswith('  '+v+' ='): return k
    return f0  # argument
jobs=[]
for lines,base,bi,v in units:
    dl=defline(base)
    for bj in range(max(0,bi-R),min(len(blocks),bi+R+1)):
        a,b=blocks[bj]
        for pos,ins in (('top',a+1),('bot',b)):
            if ins in lines or ins==lines[-1]+1 and pos=='bot' and bj==bi: pass
            if bj==bi and ((pos=='top' and ins==lines[0]) or (pos=='bot' and ins==lines[-1]+1)): continue
            if dl>=ins: continue
            if bj>=len(blocks)-1 and pos=='bot': pass
            jobs.append((v,lines,ins,f'{v}@{bj}{pos}',bi))
def run(job):
    v,lines,ins,name,bi=job
    M=list(L); moved=[M[k] for k in lines]
    for k in sorted(lines,reverse=True): M[k]=None
    M[ins]=('\n'.join(moved)+'\n'+M[ins]) if M[ins] is not None else '\n'.join(moved)
    t='\n'.join(x for x in M if x is not None)
    fn=f'/tmp/cbmv_{os.getpid()}.ll'
    d=os.path.join(os.path.dirname(os.path.abspath(outp)),'cbtmp'); os.makedirs(d,exist_ok=True); fn=f'{d}/{os.getpid()}.ll'
    open(fn,'w').write(t); r=px2.run(fn); r['name']=name; r['from']=bi
    r.pop('ch',None) if 'err' not in r else None
    return r
if __name__=='__main__':
    print(len(units),'units',len(blocks),'blocks',len(jobs),'jobs',file=sys.stderr)
    with mp.Pool(P) as pool, open(outp,'w') as o:
        for r in pool.imap_unordered(run,jobs):
            o.write(json.dumps(r)+'\n'); o.flush()
