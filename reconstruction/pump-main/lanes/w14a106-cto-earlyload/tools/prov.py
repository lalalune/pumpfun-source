#!/usr/bin/env python3
"""prov.py <fn.bin|orig> [--dump]: forward dataflow load provenance for admin_cto::execute.
Registers/stack slots carry symbolic pointer exprs rooted at entry regs (R1..R5). Prints JSON {expr:[first_off,count,offs]}."""
import sys,struct,json,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import dis as D
def decode(b):
    ins=[];i=0
    while i<len(b):
        op=b[i]; rg=b[i+1]; dst=rg&15; src=rg>>4; off=struct.unpack_from('<h',b,i+2)[0]; imm=struct.unpack_from('<i',b,i+4)[0]
        n=16 if op==0x18 else 8
        ins.append((i,op,dst,src,off,imm,n)); i+=n
    return ins
UNK=None
def analyze(b):
    ins=decode(b); idx={x[0]:k for k,x in enumerate(ins)}
    # successors
    succ={}
    for k,(o,op,dst,src,off,imm,n) in enumerate(ins):
        cls=op&7; s=[]
        if op==0x95: s=[]
        elif cls==5 and op!=0x85:
            t=o+8+off*8
            if (op>>4)==0: s=[t]
            else: s=[ins[k+1][0],t] if k+1<len(ins) else [t]
        else:
            s=[ins[k+1][0]] if k+1<len(ins) else []
        succ[o]=s
    init={'r1':'R1','r2':'R2','r3':'R3','r4':'R4','r5':'R5','r10':'FP'}
    IN={0:init}; work=[0]; loads={}
    OPT='--opt' in sys.argv
    def meet(a,b):
        if not OPT: return {k:v for k,v in a.items() if b.get(k,'#')==v}
        # optimistic: keep a key if all present values agree (unknown on one path ignored)
        m=dict(a)
        for k,v in b.items():
            if k in m and m[k]!=v: m[k]='?CONFLICT'
            elif k not in m: m[k]=v
        return {k:v for k,v in m.items() if v!='?CONFLICT'} if False else m
    it=0
    while work:
        it+=1
        o=work.pop(); st=dict(IN[o]); k=idx[o]; _,op,dst,src,off,imm,n=ins[k]
        cls=op&7; R=lambda r:st.get('r%d'%r)
        if cls==1:  # ldx
            bs=R(src); sz=(op>>3)&3
            if bs=='FP': v=st.get('S%d'%off)
            elif bs is not None and not bs.startswith('?'): v=f'{bs}.{off:x}' + ('' if sz==3 else ':'+'whb'[sz])
            else: v=None
            if v is None: st.pop('r%d'%dst,None)
            else: st['r%d'%dst]=v
        elif cls==3:  # stx
            if R(dst)=='FP':
                v=R(src) if ((op>>3)&3)==3 else None
                if v is None: st.pop('S%d'%off,None)
                else: st['S%d'%off]=v
        elif cls==2:
            if R(dst)=='FP': st.pop('S%d'%off,None)
        elif cls in (4,7):
            a=op>>4; regsrc=bool(op&8)
            if cls==7 and a==11:  # mov64
                if regsrc and R(src) is not None: st['r%d'%dst]=R(src)
                elif not regsrc: st['r%d'%dst]='#%d'%imm
                else: st.pop('r%d'%dst,None)
            elif cls==7 and a==0 and not regsrc and R(dst) is not None and not R(dst).startswith('#'):
                v=R(dst)
                if v=='FP' or v.startswith('FP'): st['r%d'%dst]='FP%+d'%(imm+(int(v[2:]) if len(v)>2 else 0))
                else: st['r%d'%dst]=v+'%+d'%imm
            else: st.pop('r%d'%dst,None)
        elif op==0x18: st.pop('r%d'%dst,None)
        elif op==0x85:
            for r in range(6): st.pop('r%d'%r,None)
        for t in succ[o]:
            if t not in IN: IN[t]=st; work.append(t)
            else:
                m=meet(IN[t],st)
                if m!=IN[t]: IN[t]=m; work.append(t)
    # second pass: record loads with converged IN states
    for (o,op,dst,src,off,imm,n) in ins:
        if (op&7)!=1 or o not in IN: continue
        # recompute state at o: IN[o] is state before instruction
        bs=IN[o].get('r%d'%src)
        if bs is None or bs.startswith('FP') or bs.startswith('#') or bs.startswith('?'): continue
        sz=(op>>3)&3
        e=f'{bs}.{off:x}'+('' if sz==3 else ':'+'whb'[sz])
        loads.setdefault(e,[]).append(o)
    return loads
if __name__=='__main__':
    p=sys.argv[1]; b=D.orig() if p=='orig' else open(p,'rb').read()
    L=analyze(b); print(json.dumps({k:v for k,v in sorted(L.items(),key=lambda x:x[1][0])}))
