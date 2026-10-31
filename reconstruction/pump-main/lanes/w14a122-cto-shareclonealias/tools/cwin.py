#!/usr/bin/env python3
"""cwin.py <cand|orig> <lo> <hi> <acc_slot_hex>: per-clone window map of an AccountInfo clone run.
Tracks the accounts pointer (reloads from [r10-acc_slot]), account pointers [acc+off], their Rc pointers
([X+8] lamports, [X+16] data) through registers and spill slots, and prints one line per Rc window
(from Rc ptr load to its count store) with the account-field loads that fall inside it."""
import sys,os,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import dis as D, xled, oracle
p=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16); slot=int(sys.argv[4],16)
b=oracle.orig_window() if p=='orig' else xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
NAME={0x68:'PA',0x0:'AU',0x8:'GL',0x10:'MI',0x90:'SC',0xa0:'EA',0x98:'PR'}
FLD={0x0:'key',0x18:'own',0x20:'rent',0x28:'sig',0x29:'wr',0x2a:'ex'}
reg={}; stk={}; ev=[]
for o,s in D.d(b):
    if not(lo<=o<hi): continue
    m=re.match(r'(ldx\w+) r(\d+), \[r(\d+)([+-]0x[0-9a-f]+)\]',s)
    st=re.match(r'(stx\w+) \[r(\d+)([+-]0x[0-9a-f]+)\], r(\d+)',s)
    mv=re.match(r'mov64 r(\d+), r(\d+)$',s)
    if m:
        d=int(m.group(2)); a=int(m.group(3)); off=int(m.group(4),16); t=reg.get(a)
        if a==10:
            reg[d]=('ACC',) if -off==slot else stk.get(off)
            continue
        if t==('ACC',) and off in NAME: reg[d]=('A',NAME[off]); continue
        if t and t[0]=='A':
            if off==8: reg[d]=('L',t[1]); ev.append((o,t[1],'L<')); continue
            if off==16: reg[d]=('D',t[1]); ev.append((o,t[1],'D<')); continue
            if off in FLD: ev.append((o,t[1],FLD[off])); reg[d]=None; continue
        reg[d]=None; continue
    if st:
        a=int(st.group(2)); off=int(st.group(3),16); sr=int(st.group(4))
        if a==10: stk[off]=reg.get(sr); continue
        t=reg.get(a)
        if t and t[0] in 'LD' and off==0: ev.append((o,t[1],t[0]+'>'))
        continue
    if mv: reg[int(mv.group(1))]=reg.get(int(mv.group(2))); continue
    mm=re.match(r'\w+ r(\d+),',s)
    if mm and not s.startswith(('j','st')): reg[int(mm.group(1))]=None
# windows
open_={}; out=[]
cur=None
for o,acc,k in ev:
    if k in('L<','D<'):
        cur=[o,acc+k[0],[]]; out.append(cur)
    elif k in('L>','D>'):
        if cur: cur.append(o); cur=None
    else:
        (cur[2] if cur else out.append([o,'--',[]]) or out[-1][2]).append(f'{acc}.{k}')
for w in out: print(f'{w[0]:05x} {w[1]:4s} ' + ' '.join(w[2]))
