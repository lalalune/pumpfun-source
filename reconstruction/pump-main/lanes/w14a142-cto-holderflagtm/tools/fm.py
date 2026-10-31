#!/usr/bin/env python3
# fm.py <x.bin|x.o>...: M vs orig with (a) plain tokens, (b) r10 frame offsets masked, (c) frame offsets + registers masked
import sys,os,difflib,re
T=os.path.dirname(os.path.abspath(__file__)); g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
sys.path.insert(0,os.path.join(os.path.dirname(T),'t121'))
from bdis import decode
def fn(p): return open(p,'rb').read() if p.endswith('.bin') else g['elf_fn'](p,g['KEEP'])
def toks(raw,mode):
    out=[]
    for d in decode(raw):
        s=d['txt']
        if s.startswith('call'): s='call'
        if s.startswith('lddw'): s=re.sub(r',.*',',K',s)
        if s.startswith('j'): s=re.sub(r'[+-]\d+$','J',s)
        if mode>=1: s=re.sub(r'r10([+-]\d+)','r10F',s)
        if mode>=2: s=re.sub(r'\br\d\b','R',s)
        out.append(s)
    return out
O=g['orig_window']()
for p in sys.argv[1:]:
    c=fn(p); r=[]
    for m in (0,1,2):
        a=toks(O,m); b=toks(c,m); sm=difflib.SequenceMatcher(None,a,b,autojunk=False); r.append(sum(x[2] for x in sm.get_matching_blocks()))
    print(p, len(c), 'M0=%d Mframe=%d Mframe+reg=%d'%tuple(r))
