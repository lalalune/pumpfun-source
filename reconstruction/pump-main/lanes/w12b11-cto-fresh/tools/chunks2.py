#!/usr/bin/env python3
"""chunks2.py orig_annot cand_annot... : like chunks.py but also abstracts register names (structure only)."""
import sys,re,difflib,collections
def ab(ins):
    ins=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',ins)
    ins=re.sub(r'r10 - 0x[0-9a-f]+','FP',ins)
    ins=re.sub(r'^add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -A',ins)
    ins=re.sub(r'^(j\w+ .*)[+-]0x[0-9a-f]+$',r'\1J',ins)
    ins=re.sub(r'\br[0-9]\b','R',ins)
    return ins
def load(p):
    ch=[];cur=[]
    for l in open(p):
        l=l.rstrip('\n')
        if not l.strip(): continue
        a,rest=l.split(None,1)
        if ' call ' in ' '+rest:
            lab=rest.split(';')[-1].strip()[:45] if ';' in rest else 'X'
            lab=re.sub(r'_\$LT\$|\$u20\$|\$GT\$|\$LT\$',' ',lab)
            cur.append('call '+lab); ch.append((lab,int(a,16),cur)); cur=[]
        elif rest.strip()=='exit':
            cur.append('exit'); ch.append(('exit',int(a,16),cur)); cur=[]
        else: cur.append(ab(rest.strip()))
    if cur: ch.append(('end',0,cur))
    occ=collections.Counter(); out=[]
    for lab,a,c in ch:
        occ[lab]+=1; out.append(((lab,occ[lab]),a,c))
    return out
o=load(sys.argv[1]); cands=[load(p) for p in sys.argv[2:]]
tot=[0]*len(cands); n=0
for key,a,c in o:
    n+=len(c); row=[]
    for i,cd in enumerate(cands):
        m=[x for x in cd if x[0]==key]
        r=difflib.SequenceMatcher(None,c,m[0][2],autojunk=False).ratio() if m else 0.0
        tot[i]+=r*len(c); row.append(r)
    flag='' if len(row)<2 else (' <<' if row[1]>row[0]+0.05 else (' >>' if row[0]>row[1]+0.05 else ''))
    if '-q' not in sys.argv[0:1]: print(f'{a-0x22a10:#06x} {len(c):4d} {key[0][:40]:40s}#{key[1]:<2d} '+' '.join(f'{r:.2f}' for r in row)+flag)
print('weighted', ' '.join(f'{t/n:.4f}' for t in tot))
