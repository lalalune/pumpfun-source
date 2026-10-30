#!/usr/bin/env python3
"""blkmv.py <m.ll> <block> <after-block|BEFORE:blk> : move an IR block of execute in the post-opt module, llc, score."""
import sys,os,re,tempfile

sys.path.insert(0,os.path.dirname(__file__))
import irre_lib as irre

def blocks(fn):
    L=fn.split('\n'); head=[];bl=[];cur=None
    # first line define, then entry block w/o label (start-1)
    starts=[]
    for i,l in enumerate(L):
        m=re.match(r'^([\w.$"-]+):',l)
        if m: starts.append((i,m.group(1)))
    return L,starts
def move(fn,b,dst):
    L,st=blocks(fn)
    idx={n:i for i,n in st}
    order=[n for _,n in st]
    ends={}
    for k,(i,n) in enumerate(st):
        j=st[k+1][0] if k+1<len(st) else len(L)-1
        # trim trailing blank lines into block
        ends[n]=(i,j)
    pre=L[:st[0][0]]; post=L[len(L)-1:]
    body={n:L[ends[n][0]:ends[n][1]] for n in order}
    order.remove(b)
    if dst.startswith('BEFORE:'):
        order.insert(order.index(dst[7:]),b)
    else:
        order.insert(order.index(dst)+1,b)
    out=pre[:]
    for n in order:
        blk=body[n]
        while blk and blk[-1]=='': blk=blk[:-1]
        out+=blk+['']
    out+=post
    return '\n'.join(out)
if __name__=='__main__':
    m,b,dst=sys.argv[1:4]
    t=open(m).read(); pre,fn,post=irre.split_fn(t); O=irre.orig()
    fn=re.sub(r'%(\d+)(?![\w.$])',r'%v\1',fn)
    nf=move(fn,b,dst)
    print(irre.run(pre,nf,post,O,tempfile.mkdtemp(prefix='bm')))
