#!/usr/bin/env python3
"""irf.py: parse one function of an IR module into blocks; helpers to print/edit (experiment only)."""
import re,sys
FN=r'admin_cto7execute17h'
def fnspan(t,fn=FN):
    m=re.search(r'^define [^\n]*@[^\n]*'+fn+r'[^\n]*\{\n',t,re.M)
    i=m.start(); j=t.index('\n}\n',i)+3
    return i,j
def blocks(body):
    """body: function text. returns list of (label, start, end) offsets within body (block text without trailing blank)."""
    lines=body.split('\n'); out=[]; cur=None; off=0; starts=[]
    for k,l in enumerate(lines):
        m=re.match(r'^("[^"]+"|[\w.$-]+):',l)
        if m: starts.append((m.group(1),k))
    return lines,starts
def parse(t,fn=FN):
    i,j=fnspan(t,fn); body=t[i:j]
    lines=body.split('\n')
    B={}; order=[]; cur='%entry'; buf=[]
    for l in lines[1:]:
        m=re.match(r'^("[^"]+"|[\w.$-]+):',l)
        if m:
            if buf or cur!='%entry': B[cur]=buf; order.append(cur)
            cur=m.group(1); buf=[l]; continue
        if l=='}': break
        buf.append(l)
    B[cur]=buf; order.append(cur)
    return i,j,lines[0],B,order
def succs(blk):
    s=[]
    for l in blk:
        if re.match(r'\s+(br|switch|invoke|callbr) ',l) or re.match(r'\s+i\d+ -?\d+, label ',l):
            s+=re.findall(r'label %("[^"]+"|[\w.$-]+)',l)
    return s
def preds(B):
    P={k:[] for k in B}
    for k,b in B.items():
        for s in succs(b):
            if s in P: P[s].append(k)
    return P
def show(t,names,fn=FN):
    i,j,h,B,order=parse(t,fn)
    for n in names:
        print('\n'.join(B[n])); print()
if __name__=='__main__':
    t=open(sys.argv[1]).read()
    if sys.argv[2]=='find':
        i,j,h,B,order=parse(t)
        for n in order:
            if re.search(sys.argv[3],n): print(n, 'succs',succs(B[n]))
    else: show(t,sys.argv[2:])
