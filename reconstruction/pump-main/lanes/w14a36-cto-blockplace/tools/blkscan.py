#!/usr/bin/env python3
"""blkscan.py <m.s> <out.jsonl> [-j N] [--blocks L1,L2]: placement-only block-move oracle for admin_cto::execute.
Splits llc asm of the function into blocks, and for every movable block (ends in ja/exit, and the block before it
ends in ja/exit, so removing it breaks no fallthrough) tries every insertion point whose previous block ends in
ja/exit. Assembles with cc1as and scores with the rx metric. Registers/frame are unchanged: the result bounds what
moving ONLY that block (e.g. by a block-order source change) is worth."""
import sys,os,re,json,subprocess,tempfile
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
ORIG=G['orig_window']()
args=sys.argv[1:]; S=args.pop(0); OUTF=args.pop(0); J=4; ONLY=None
while args:
    a=args.pop(0)
    if a=='-j': J=int(args.pop(0))
    elif a=='--blocks': ONLY=args.pop(0).split(',')
    elif a=='--chains': pass
L=open(S).read().split('\n')
fs=[k for k,l in enumerate(L) if re.match(r'^_ZN14pump_recovered9admin_cto7execute\w*:',l)][0]
fe=[k for k,l in enumerate(L) if l.startswith('.Lfunc_end0')][0]
def isstart(l): return re.match(r'^(LBB0_\d+:|# %bb\.\d+:)',l) is not None
starts=[k for k in range(fs+1,fe) if isstart(L[k])]
blocks=[]  # (start,end)
for a,b in zip(starts,starts[1:]+[fe]): blocks.append((a,b))
def last(b):
    xs=[l.strip() for l in L[b[0]+1:b[1]] if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('.')]
    return xs[-1] if xs else ''
def name(b): return L[b[0]].split(':')[0].replace('# ','')
term=[last(b).startswith('ja ') or last(b)=='exit' for b in blocks]
def info(b):
    t='\n'.join(L[b[0]:b[1]]); m=re.findall(r'stw \[r10 - 696\], (\d+)',t)
    return (L[b[0]].split('#')[-1].strip()[:60], ','.join(m))
CH='--chains' in sys.argv
if CH:
    nb=[]; cur=None
    for i,b in enumerate(blocks):
        cur=b if cur is None else (cur[0],b[1])
        if term[i]: nb.append(cur); cur=None
    if cur: nb.append(cur)
    blocks=nb; term=[last(b).startswith('ja ') or last(b)=='exit' for b in blocks]
mov=[i for i in range(1,len(blocks)) if term[i] and term[i-1] and name(blocks[i]).startswith('LBB')]
if ONLY: mov=[i for i in mov if name(blocks[i]) in ONLY]
def score(text):
    with tempfile.TemporaryDirectory() as d:
        s=d+'/a.s'; o=d+'/a.o'; open(s,'w').write(text)
        r=subprocess.run([SDK+'/clang','-cc1as','-triple','sbf','-target-feature','+store-imm','-target-feature','+jmp-ext','-filetype','obj',s,'-o',o],capture_output=True,text=True)
        if r.returncode: return None
        c=G['elf_fn'](o,G['KEEP']); rr,sd=G['metric'](c,ORIG); return (round(rr,5),len(c),sd)
pre=L[:blocks[0][0]]; post=L[fe:]
def assemble(order): 
    body=[]
    for i in order: body+=L[blocks[i][0]:blocks[i][1]]
    return '\n'.join(pre+body+post)
base=score(assemble(range(len(blocks))))
def job(i):
    rest=[k for k in range(len(blocks)) if k!=i]
    best=None; res=[]
    for p in range(1,len(rest)+1):
        if p<len(rest) and not name(blocks[rest[p]]).startswith('LBB'): continue
        if not term[rest[p-1]]: continue
        if rest[p-1]==i-1 and (p==len(rest) or rest[p]==i+1): continue  # original spot
        order=rest[:p]+[i]+rest[p:]
        r=score(assemble(order))
        if r: res.append((r[0],p,name(blocks[rest[p]]) if p<len(rest) else 'END',r[1],r[2]))
    res.sort(reverse=True)
    return {'block':name(blocks[i]),'idx':i,'info':info(blocks[i]),'n':blocks[i][1]-blocks[i][0],'base':base,'top':res[:3]}
if __name__=='__main__':
    print(json.dumps({'base':base,'blocks':len(blocks),'movable':len(mov)}),flush=True)
    with Pool(J) as P, open(OUTF,'w') as f:
        for r in P.imap_unordered(job,mov):
            f.write(json.dumps(r)+'\n'); f.flush()
