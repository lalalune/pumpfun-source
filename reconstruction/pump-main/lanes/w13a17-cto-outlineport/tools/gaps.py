#!/usr/bin/env python3
# gaps.py orig_fn cand_fn [min] : abstracted alignment; list orig-only / cand-only runs (len>=min)
import sys,re,difflib
def ab(l):
    p=l.split(None,1); s=p[1].split(';')[0].strip()
    s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw R',s)
    s=re.sub(r'r10 - 0x[0-9a-f]+','FP',s); s=re.sub(r'^add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -A',s)
    s=re.sub(r'^(j\w+ .*)[+-]0x[0-9a-f]+$',r'\1J',s); s=re.sub(r'^ja .*','ja',s); s=re.sub(r'\br[0-9]\b','R',s)
    return s
O=[l for l in open(sys.argv[1]) if l.strip()]; C=[l for l in open(sys.argv[2]) if l.strip()]; mn=int(sys.argv[3]) if len(sys.argv)>3 else 6
sm=difflib.SequenceMatcher(None,[ab(x) for x in O],[ab(x) for x in C],autojunk=False)
to=tc=0
for t,i1,i2,j1,j2 in sm.get_opcodes():
    if t=='equal': continue
    d=(i2-i1)-(j2-j1); to+=i2-i1; tc+=j2-j1
    if max(i2-i1,j2-j1)>=mn: print(f'{t:7s} orig {O[i1].split()[0] if i1<len(O) else "end"} +{i2-i1:<4d} cand {C[j1].split()[0] if j1<len(C) else "end"} +{j2-j1:<4d} net {d:+d}')
print('ratio',round(sm.ratio(),5),'orig-only',to,'cand-only',tc)
