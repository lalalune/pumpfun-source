#!/usr/bin/env python3
"""reload2.py <mn.ll> <out.jsonl> : add/remove AccountInfo pointer re-loads (experiment only).
ADD X:off = re-load clone pointer X from its source right before field off's load (source: a.<acct>.<field>).
RM a>b    = drop the duplicate pointer load b (same source as earlier a) and use a (source: x.<field> instead of a path).
MODE=singles (default) | pairs (ADD x RM, the net-zero-size candidates) | JOBS=<file> lines 'op;op'."""
import sys,os,re,json,itertools,subprocess,tempfile,difflib
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/reread.py').read().split('singles=[]')[0]
mll,out=sys.argv[1],sys.argv[2]
sys.argv=['x',mll,out]; G={'__file__':T+'/reread.py'}; exec(src,G)
L=G['L']; OM=G['OM']; g=G['g']; SDK=G['SDK']; ORIG=G['ORIG']
st=next(i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l); en=next(i for i in range(st,len(L)) if L[i]=='}')
clones=[re.match(r'  (%\S+) = ',L[i]).group(1) for i in range(st,en) if re.match(r'  %x[0-9.a-z]* = load ptr, ptr ',L[i])]
seen={}; dups=[]
for i in range(st,en):
    m=re.match(r'  (%\S+) = load ptr, ptr (%\S+?), align 8, ',L[i])
    if m:
        v,s=m.groups()
        if s in seen and i-seen[s][1]<150: dups.append((seen[s][0],v))
        seen[s]=(v,i)
def build(ops):
    adds=[o[1:] for o in ops if o[0]=='ADD']; rms=[o[1:] for o in ops if o[0]=='RM']
    txt=G['build'](adds) if adds else '\n'.join(L)
    for a,b in rms:
        lines=txt.split('\n'); lines=[l for l in lines if not l.startswith('  '+b+' = ')]
        txt=re.sub(re.escape(b)+r'(?![\w.$"])',a,'\n'.join(lines))
    return txt
def lab(ops): return ';'.join('ADD %s:%d'%(o[1],o[2]) if o[0]=='ADD' else 'RM %s>%s'%(o[1],o[2]) for o in ops)
def run(ops):
    lb=lab(ops)
    try: txt=build(ops)
    except Exception as e: return {'lab':lb,'err':repr(e)[:150]}
    d=tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(out))); p=d+'/m.ll'; open(p,'w').write(txt)
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: subprocess.run(['rm','-rf',d]); return {'lab':lb,'err':r.stderr[-150:]}
    c=g['elf_fn'](d+'/m.o',g['KEEP']); subprocess.run(['rm','-rf',d])
    cm=g['mask'](c); M=sum(b.size for b in difflib.SequenceMatcher(None,OM,cm,autojunk=False).get_matching_blocks())
    sd=g['metric'](c,ORIG)[1] if len(c)==len(ORIG) else None
    return {'lab':lb,'ratio':round(2*M/(len(OM)+len(cm)),5),'bytes':len(c),'M':M,'slots':sd}
def parse(s):
    ops=[]
    for t in s.split(';'):
        k,v=t.split(' ',1)
        if k=='ADD': x,o=v.split(':'); ops.append(('ADD',x,int(o)))
        else: a,b=v.split('>'); ops.append(('RM',a,b))
    return ops
adds=[]
for X in clones:
    try: _,_,sites=G['locate'](X); adds+=[('ADD',X,o) for o in sorted(sites)]
    except StopIteration: pass
rms=[('RM',a,b) for a,b in dups]
MODE=os.environ.get('MODE','singles')
if os.environ.get('JOBS'): jobs=[parse(l) for l in open(os.environ['JOBS']).read().split('\n') if l.strip()]
elif MODE=='singles': jobs=[[o] for o in adds+rms]
else:
    A=[parse(l)[0] for l in os.environ['ADDS'].split(',')] if os.environ.get('ADDS') else adds
    R=[parse(l)[0] for l in os.environ['RMS'].split(',')] if os.environ.get('RMS') else rms
    jobs=[[a,r] for a in A for r in R]
print(len(clones),'clones',len(adds),'adds',len(rms),'rms',len(jobs),'jobs',file=sys.stderr)
with ThreadPoolExecutor(int(os.environ.get('NT','4'))) as ex, open(out,'w') as f:
    for r in ex.map(run,jobs): f.write(json.dumps(r)+'\n'); f.flush()
