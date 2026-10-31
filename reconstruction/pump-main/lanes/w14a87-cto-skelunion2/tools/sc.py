#!/usr/bin/env python3
"""sc.py [--chunks] [--ref name] <x.o|x.s|rxname>...: ratio, bytes, M, jM (jump offsets masked) and per-0x800 orig chunk M/jM.
.s files are assembled with cc1as (sbf +store-imm +jmp-ext). rxname -> rx/<name>/m.o"""
import sys,os,subprocess,difflib,json,tempfile
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle
O=os.path.dirname(T); SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
def fn(p):
    if p.endswith('.s'):
        o=p[:-2]+'.o'
        r=subprocess.run([SDK+'/clang','-cc1as','-triple','sbf','-target-feature','+store-imm','-target-feature','+jmp-ext','-filetype','obj',p,'-o',o],capture_output=True,text=True)
        if r.returncode: raise SystemExit(r.stderr[-1500:])
        p=o
    elif not p.endswith('.o') and not p.endswith('.so'): p=f'{O}/rx/{p}/m.o'
    return oracle.elf_fn(p,oracle.KEEP)
def jmask(t):
    out=[]
    for x in t:
        op=x[0]
        if (op&7) in (5,6) and op not in (0x85,0x95): x=x[:2]+b'\0\0'+x[4:]
        out.append(x)
    return out
def fmask(t,regs=False):
    out=[]
    for x in t:
        x=bytearray(x); op=x[0]; cl=op&7; d=x[1]&15; sr=x[1]>>4
        if (cl==1 and sr==10) or (cl in (2,3) and d==10): x[2:4]=b'\0\0'
        if regs:
            x[1]=0
            if cl in (5,6) and op not in (0x85,0x95): x[2:4]=b'\0\0'
            if op in (0x07,0x87) : x[4:8]=b'\0\0\0\0'  # add64 imm (frame lea offsets)
        out.append(bytes(x))
    return out
OW=oracle.orig_window(); OT=oracle.mask(OW); OJ=jmask(OT); OF=fmask(OT); OS=fmask(OT,True)
offs=[];a=0
for x in OT: offs.append(a); a+=len(x)
def hits(A,B):
    sm=difflib.SequenceMatcher(None,A,B,autojunk=False); h=[0]*len(A)
    for b in sm.get_matching_blocks():
        for k in range(b.size): h[b.a+k]=1
    return h
def score(p):
    c=fn(p); ct=oracle.mask(c); cj=jmask(ct)
    h=hits(OT,ct); hj=hits(OJ,cj); M=sum(h); JM=sum(hj); FM=sum(hits(OF,fmask(ct))); SK=sum(hits(OS,fmask(ct,True)))
    ch={}
    for i,o in enumerate(offs):
        k=o//0x800*0x800; v=ch.setdefault(k,[0,0]); v[0]+=h[i]; v[1]+=hj[i]
    return {'ratio':round(2*M/(len(OT)+len(ct)),5),'bytes':len(c),'M':M,'jM':JM,'jm':round(2*JM/(len(OT)+len(ct)),5),'fM':FM,'skM':SK,'ch':ch}
if __name__=='__main__':
    a=sys.argv[1:]; chunks='--chunks' in a; a=[x for x in a if x!='--chunks']; ref=None
    if '--ref' in a: i=a.index('--ref'); ref=a[i+1]; del a[i:i+2]
    R=score(ref) if ref else None
    for p in a:
        s=score(p); ch=s.pop('ch'); print(os.path.basename(p), json.dumps(s))
        if chunks:
            print('  chunk M/jM' + (' (delta vs ref)' if R else ''))
            print('  '+' '.join(f'{k:#06x}:{v[0]-(R["ch"][k][0] if R else 0):+d}/{v[1]-(R["ch"][k][1] if R else 0):+d}' for k,v in sorted(ch.items())))
