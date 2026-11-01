#!/usr/bin/env python3
"""pmv.py: pre-opt validate block moves. move(text, 'A>B;...') moves validate block A to just after block B (pre-opt IR)."""
import sys,os,re,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
def vblocks(text):
    m=re.search(r'^define [^\n]*admin_cto8validate[^\n]*\{\n',text,re.M); st=m.end(); en=text.index('\n}\n',st)
    body=text[st:en]; L=body.split('\n')
    S=[i for i,l in enumerate(L) if re.match(r'^[\w.$-]+:',l)]
    return st,en,L,S
def denum(L):
    return [re.sub(r'%(\d+)\b',r'%n\1',l) for l in L]
def move(text,moves):
    st,en,L,S=vblocks(text)
    # entry block (no label) stays first: lines before S[0]
    L=denum(L)
    head=L[:S[0]]
    B=[L[S[k]:(S[k+1] if k+1<len(S) else len(L))] for k in range(len(S))]
    names=[re.match(r'^([\w.$-]+):',b[0]).group(1) for b in B]
    for mv in [m for m in moves.split(';') if m]:
        a,b=mv.split('>')
        ia=names.index(a); blk=B.pop(ia); nm=names.pop(ia)
        if b=='^': ib=-1
        else: ib=names.index(b)
        B.insert(ib+1,blk); names.insert(ib+1,nm)
    body='\n'.join(head+[l for b in B for l in b])
    # define line numbered args: the define line is outside body; args %0,%1,%2 are referenced in body -> rename in define too
    pre=text[:st]; dl_start=pre.rfind('\ndefine ')+1
    dl=pre[dl_start:]; dl=re.sub(r'%(\d+)\b',r'%n\1',dl)
    return pre[:dl_start]+dl+body+text[en:]
def names(text):
    st,en,L,S=vblocks(text); return [re.match(r'^([\w.$-]+):',L[s]).group(1) for s in S]
