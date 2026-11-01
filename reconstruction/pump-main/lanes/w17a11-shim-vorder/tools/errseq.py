#!/usr/bin/env python3
"""errseq.py <fn.bin|so|orig> : validate/execute error-site order.
Prints (1) 'from' order: code stores stw [r10-0x238],0x17xx/0x1xxx by address (= line-imm order),
(2) 'name' order: position of the PumpError::name call heading each error (split name/fmt blocks followed via jeq r0,0)."""
import sys,os,struct,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import dis, oracle
CODE2LINE={6088:284,6083:289,6084:296,6090:298,6089:306,6030:307,6019:312,6091:326,6080:330,6077:334,6078:338,6095:410,6092:'wal',6093:'660/719',2006:'648'}
def load(p):
    if p=='orig': return dis.orig()
    if p.endswith('.so'): return oracle.elf_fn(p,oracle.KEEP)
    return open(p,'rb').read()
def analyze(b,lo=0,hi=None):
    ins=dis.d(b); pos=[o for o,_ in ins]; idx={o:i for i,(o,_) in enumerate(ins)}
    starts=set([0])
    for k,(o,s) in enumerate(ins):
        m=re.match(r'(j\w+) .*?([0-9a-f]+)$',s)
        if s.startswith('j'):
            t=int(s.split()[-1],16); starts.add(t)
            if k+1<len(ins): starts.add(ins[k+1][0])
        if s=='exit' and k+1<len(ins): starts.add(ins[k+1][0])
    jeq0={}  # target -> position of jeq r0,0
    for k,(o,s) in enumerate(ins):
        m=re.match(r'jeq r0, 0, ([0-9a-f]+)$',s)
        if m and k>0 and ins[k-1][1].startswith('call'): jeq0[int(m.group(1),16)]=o
    res=[]
    for k,(o,s) in enumerate(ins):
        m=re.match(r'stw \[r10-0x238\], (\d+)$',s)
        if not m: continue
        code=int(m.group(1))
        if code not in CODE2LINE: continue
        # block start
        j=k
        while j>0 and ins[j][0] not in starts: j-=1
        bs=ins[j][0]
        calls=[ins[q][0] for q in range(j,k) if ins[q][1].startswith('call')]
        if len(calls)>=2: npos=calls[0]
        elif bs in jeq0:
            jp=jeq0[bs]; q=idx[jp]-1; c=0; npos=None
            while q>=0:
                if ins[q][1].startswith('call'):
                    c+=1
                    if c==2: npos=ins[q][0]; break
                q-=1
        else: npos=None
        res.append(dict(code=code,line=CODE2LINE[code],frm=o,name=npos))
    return res
if __name__=='__main__':
    b=load(sys.argv[1]); r=analyze(b)
    v=[x for x in r if x['frm']<0x2000]
    print('from:', ' '.join(str(x['line']) for x in sorted(v,key=lambda x:x['frm'])))
    print('name:', ' '.join(str(x['line']) for x in sorted(v,key=lambda x:(x['name'] if x['name'] is not None else 1e9))))
    if '-v' in sys.argv:
        for x in r: print(x['line'], hex(x['frm']), hex(x['name']) if x['name'] is not None else None)
