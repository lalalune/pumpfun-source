#!/usr/bin/env python3
"""lv.py <fn.bin>...: L1 (frame masked) and L2 (frame+registers masked) difflib ratios (cls.py masks), plus per-0x800 L2 matched counts."""
import sys,os,difflib,types
T=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'t84')
C=types.ModuleType('C'); _s=open(T+'/cls.py').read(); C.__dict__['__file__']=T+'/cls.py'; exec(_s[:_s.index('def main')],C.__dict__)
O=open(os.path.join(os.path.dirname(T),'orig.bin'),'rb').read()
def toks(raw,l): return [C.mask(t,l) for _,t in C.insns(raw)]
def offs(raw): return [o for o,_ in C.insns(raw)]
O1,O2=toks(O,1),toks(O,2); oo=offs(O)
for f in sys.argv[1:]:
    c=open(f,'rb').read(); r=[]
    for l,Ot in ((1,O1),(2,O2)):
        sm=difflib.SequenceMatcher(None,Ot,toks(c,l),autojunk=False); r.append(round(sm.ratio(),5))
        if l==2:
            ch={}
            for a,b,m in sm.get_matching_blocks():
                for k in range(m): ch[oo[a+k]//0x800]=ch.get(oo[a+k]//0x800,0)+1
            M2=sum(ch.values())
    print(f, 'L1',r[0],'L2',r[1],'M2',M2,' '.join(f'{k*0x800:x}:{v}' for k,v in sorted(ch.items())))
