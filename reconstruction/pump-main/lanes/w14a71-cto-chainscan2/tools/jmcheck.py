#!/usr/bin/env python3
"""jmcheck.py <m.s> <LABEL:BEFORE>...: for each single placement move (mvblk semantics, chain = block up to its ja/exit
end as blkscan --chains), report ratio, jump-offset-masked ratio (jm: off field of every jmp-class insn zeroed) and
frame-masked ratio vs the original. A move whose gain disappears under jm is pure jump-distance compensation (it pays
because it shortens/lengthens jumps over other size differences), not a block-order match. Experiment only."""
import sys,os,re,json,subprocess,tempfile,difflib
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O=G['orig_window']()
def toks(raw,jm=False,fr=False):
    out=[]
    for t in G['mask'](raw):
        t=bytearray(t); op=t[0]; cls=op&7; dst=t[1]&15; s=t[1]>>4
        if jm and cls==5 and op not in (0x85,0x95): t[2:4]=b'\0\0'
        if fr and cls in (1,2,3) and (dst==10 or s==10): t[2:4]=b'\0\0'
        out.append(bytes(t))
    return out
def met(c):
    return [round(difflib.SequenceMatcher(None,toks(O,jm,fr),toks(c,jm,fr),autojunk=False).ratio(),5) for jm,fr in ((0,0),(1,0),(1,1))]
S=sys.argv[1]; L=open(S).read().split('\n')
fs=[k for k,l in enumerate(L) if re.match(r'^_ZN14pump_recovered9admin_cto7execute\w*:',l)][0]
fe=[k for k,l in enumerate(L) if l.startswith('.Lfunc_end0')][0]
def isstart(l): return re.match(r'^(LBB0_\d+:|# %bb\.\d+:)',l) is not None
st=[k for k in range(fs+1,fe) if isstart(L[k])]; bl=list(zip(st,st[1:]+[fe]))
def last(b):
    xs=[l.strip() for l in L[b[0]+1:b[1]] if l.strip() and not l.strip().startswith(('#','.'))]
    return xs[-1] if xs else ''
term=[last(b).startswith('ja ') or last(b)=='exit' for b in bl]
ch=[]; cur=None
for i,b in enumerate(bl):
    cur=b if cur is None else (cur[0],b[1])
    if term[i]: ch.append(cur); cur=None
names=[L[c[0]].split(':')[0].replace('# ','') for c in ch]
pre=L[:ch[0][0]]; post=L[fe:]
def asm(order):
    body=[]
    for i in order: body+=L[ch[i][0]:ch[i][1]]
    return '\n'.join(pre+body+post)
def build(text):
    with tempfile.TemporaryDirectory() as d:
        open(d+'/a.s','w').write(text)
        subprocess.run([SDK+'/clang','-cc1as','-triple','sbf','-target-feature','+store-imm','-target-feature','+jmp-ext','-filetype','obj',d+'/a.s','-o',d+'/a.o'],check=True,capture_output=True)
        return G['elf_fn'](d+'/a.o',G['KEEP'])
order=list(range(len(ch))); b=met(build(asm(order))); print(json.dumps({'move':'base','ratio_jm_fm':b}))
for mv in sys.argv[2:]:
    lab,bef=mv.split(':'); i=names.index(lab); o=[k for k in order if k!=i]
    p=len(o) if bef=='END' else o.index(names.index(bef)); o=o[:p]+[i]+o[p:]
    m=met(build(asm(o))); print(json.dumps({'move':mv,'ratio_jm_fm':m,'delta':[round(x-y,5) for x,y in zip(m,b)]}))
