#!/usr/bin/env python3
"""irscan.py <named.ll> <out.jsonl> [-j N] [--span FIRST:LAST]: IR block-order (glue) scan for execute (experiment only).
On BPF a block ending in a conditional branch stays glued to its IR successor (analyzeBranch cannot analyse it), so IR
order is a layout input. Each error group (a block calling PumpError::name plus the following panic/exit blocks) in
the span is moved before every other block of the span; the module is llc'd (registers re-run) and scored by M/jM."""
import sys,os,re,json,subprocess,tempfile,difflib
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O=G['orig_window']()
def toks(raw,jm):
    out=[]
    for t in G['mask'](raw):
        t=bytearray(t); op=t[0]
        if jm and op&7==5 and op not in (0x85,0x95): t[2:4]=b'\0\0'
        out.append(bytes(t))
    return out
OT=[toks(O,0),toks(O,1)]
a=sys.argv[1:]; S,OUTF=a[:2]; J=int(a[a.index('-j')+1]) if '-j' in a else 6
L=open(S).read().split('\n')
fs=[i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l][0]
fe=fs+[i for i,l in enumerate(L[fs:]) if l=='}'][0]
heads=[i for i in range(fs+1,fe) if re.match(r'^([A-Za-z0-9_.$]+|"[^"]+"):',L[i])]
names=[re.match(r'^([A-Za-z0-9_.$]+|"[^"]+"):',L[i]).group(1) for i in heads]
blk=[(heads[k],heads[k+1] if k+1<len(heads) else fe) for k in range(len(heads))]
sp=a[a.index('--span')+1].split(':') if '--span' in a else ['bb5.i','bb76']
lo=names.index(sp[0]); hi=names.index(sp[1])
def body(k): return '\n'.join(L[blk[k][0]:blk[k][1]])
groups=[]; k=lo
while k<hi:
    if 'PumpError4name' in body(k):
        g=[k]; j=k+1
        while j<hi and (re.match(r'^bb3\.',names[j]) or 'exit' in names[j]): g.append(j); j+=1
        groups.append(g); k=j
    else: k+=1
def build(order):
    out=L[:heads[0]]
    for k in order: out+=L[blk[k][0]:blk[k][1]]
    out+=L[fe:]; return '\n'.join(out)
def score(text):
    with tempfile.TemporaryDirectory() as d:
        open(d+'/m.ll','w').write(text)
        r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True)
        if r.returncode: return None
        c=G['elf_fn'](d+'/m.o',G['KEEP'])
    res=[len(c)]
    for jm in (0,1):
        sm=difflib.SequenceMatcher(None,OT[jm],toks(c,jm),autojunk=False); res.append(sum(b.size for b in sm.get_matching_blocks()))
    return res
base=list(range(len(blk)))
def job(arg):
    g,p=arg
    if p in g or p==g[-1]+1: return None
    o=[k for k in base if k not in g]; i=o.index(p); o=o[:i]+g+o[i:]
    return (names[g[0]],names[p],score(build(o)))
if __name__=='__main__':
    b0=score(build(base)); print('base',b0,'groups',[names[g[0]] for g in groups],flush=True)
    jobs=[(g,p) for g in groups for p in range(lo+1,hi+1)]
    with Pool(J) as pool: res=[r for r in pool.map(job,jobs,chunksize=4) if r and r[2]]
    with open(OUTF,'w') as f:
        for r in res: f.write(json.dumps({'grp':r[0],'before':r[1],'bytes':r[2][0],'M':r[2][1],'jM':r[2][2]})+'\n')
    res.sort(key=lambda r:-(r[2][1]))
    for r in res[:15]: print(r[0][:40],'before',r[1][:30],r[2],'dM %+d djM %+d'%(r[2][1]-b0[1],r[2][2]-b0[2]))
