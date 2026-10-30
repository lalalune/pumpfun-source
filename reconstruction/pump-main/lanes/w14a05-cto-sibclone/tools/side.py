#!/usr/bin/env python3
"""side.py <orig.dis> <cand.dis> <lo> <hi>: side-by-side alignment (frame offsets+jumps masked) for orig range."""
import sys,re,difflib
def rd(p): return [(int(l[:4],16) if not l.startswith('-') else -1,re.sub(r' <[^>]*>$','',l[5:].strip())) for l in open(p) if l.strip()]
def n1(s):
    if s.startswith('call'): return 'call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    if s.startswith('j'): s=re.sub(r'([+-]0x[0-9a-f]+|[+-]\d+)$','J',s)
    return re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s)
def n2(s): return re.sub(r'\br\d\b','r',n1(s))
o=rd(sys.argv[1]); c=rd(sys.argv[2]); lo=int(sys.argv[3],16); hi=int(sys.argv[4],16)
sm=difflib.SequenceMatcher(None,[n2(t) for _,t in o],[n2(t) for _,t in c],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    for k in range(max(i2-i1,j2-j1)):
        a=o[i1+k] if i1+k<i2 else None; b=c[j1+k] if j1+k<j2 else None
        oa=a[0] if a else (o[i1-1][0] if i1>0 else 0)
        if not(lo<=oa<hi): continue
        mk=' ' if (a and b and a[1]==b[1]) else ('~' if tag=='equal' else '!')
        print('%s %-40s | %s'%(mk,('%04x %s'%a) if a else '', ('%04x %s'%b) if b else ''))
