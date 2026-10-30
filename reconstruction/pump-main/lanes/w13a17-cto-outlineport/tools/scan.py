#!/usr/bin/env python3
"""scan.py <ex.ll> <outdir> [base-edits-json] : single nolt edit per alloca of execute (on top of base edits), llc-only ratio.
edits: list of ["nolt",name] or ["mv",name,"before",name2]"""
import sys,re,subprocess,os,json,concurrent.futures as cf
src,od=sys.argv[1],sys.argv[2]; base=json.loads(sys.argv[3]) if len(sys.argv)>3 else []
L=open(src).read().split('\n')
s=next(i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l)
e=next(i for i in range(s,len(L)) if L[i]=='}')
def bounds(M):
    s=next(i for i,l in enumerate(M) if l.startswith('define') and 'admin_cto7execute' in l)
    return s,next(i for i in range(s,len(M)) if M[i]=='}')
allocas=[m.group(1) for l in L[s:e] for m in [re.match(r'\s+%(\S+) = alloca',l)] if m]
T=os.path.dirname(os.path.abspath(__file__))
def apply(edits):
    M=L[:]
    for ed in edits:
        s,e=bounds(M)
        if ed[0]=='nolt':
            for i in range(s,e):
                if 'llvm.lifetime' in M[i] and re.search(r'ptr nonnull %'+re.escape(ed[1])+r'\)',M[i]): M[i]=''
        elif ed[0]=='mv':
            a=next(i for i in range(s,e) if re.match(r'\s+%'+re.escape(ed[1])+' = alloca',M[i]))
            line=M[a]; M[a]=''
            b=next(i for i in range(s,e) if re.match(r'\s+%'+re.escape(ed[3])+' = alloca',M[i]))
            M[b]=line+'\n'+M[b] if ed[2]=='before' else M[b]+'\n'+line
            M='\n'.join(M).split('\n')
    return '\n'.join(M)
def run(tag,edits):
    d=f'{od}/{tag}'; os.makedirs(d,exist_ok=True)
    open(f'{d}/in.ll','w').write(apply(edits))
    r=subprocess.run([f'{T}/xo.sh',f'{d}/in.ll',d],capture_output=True,text=True).stdout.strip()
    for f in ('in.ll','ex.bc','ex.o'):
        try: os.remove(f'{d}/{f}')
        except FileNotFoundError: pass
    return tag,edits,r
if __name__=='__main__':
    mode=os.environ.get('MODE','nolt'); anchor=os.environ.get('ANCHOR','holder_key')
    jobs=[('base',base)]
    if 'nolt' in mode: jobs+=[(f'n{i}',base+[['nolt',a]]) for i,a in enumerate(allocas)]
    if 'mv' in mode.split(','): jobs+=[(f'm{i}',base+[['mv',a,'before',anchor]]) for i,a in enumerate(allocas) if a!=anchor]
    if 'mvx' in mode:
        X=os.environ['X']; jobs+=[(f'x{i}',base+[['mv',X,'before',a]]) for i,a in enumerate(allocas) if a!=X]
    if 'pair' in mode:
        cand=json.loads(os.environ['CAND']); jobs+=[(f'p{i}_{j}',base+[cand[i],cand[j]]) for i in range(len(cand)) for j in range(i+1,len(cand))]
    with cf.ThreadPoolExecutor(6) as ex:
        res=list(ex.map(lambda j:run(*j),jobs))
    def rat(r):
        m=re.search(r'ratio ([\d.]+).*bytes (\d+).*lddw (\d+)',r); return (float(m.group(1)),int(m.group(2)),int(m.group(3))) if m else (0,0,0)
    out=sorted(((rat(r),t,ed) for t,ed,r in res),key=lambda x:-x[0][0])
    json.dump([[list(a),t,ed] for a,t,ed in out],open(f'{od}/scan.json','w'))
    for a,t,ed in out[:25]: print(a,t,ed[-1] if ed else '')
