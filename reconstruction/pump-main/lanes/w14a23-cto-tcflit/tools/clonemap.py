#!/usr/bin/env python3
"""clonemap.py <listing> <lo> <hi> : per AccountInfo clone (pointer with an Rc load at +8 and +0x10), which block each
field is loaded in. B0 = before the lamports overflow check, B1 = between lamports and data checks, B2 = after.
Letters: K key+0 O owner+0x18 R rent_epoch+0x20 S is_signer+0x28 W is_writable+0x29 E executable+0x2a.
Output per clone: start, def insn, 'B0|B1|B2' letter strings (in load order)."""
import sys,re
F={0:'K',0x18:'O',0x20:'R',0x28:'S',0x29:'W',0x2a:'E'}
lst=[]
for l in open(sys.argv[1]):
    a,ins=l.rstrip('\n').split(' ',1); lst.append((int(a,16),ins))
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
lst=[x for x in lst if lo<=x[0]<hi]
reg={}; stk={}; defs={}  # reg -> def id; stack slot -> def id
uses={}   # def id -> list of (idx, off)
checks=[]  # idx of overflow-check branches
for i,(a,ins) in enumerate(lst):
    m=re.match(r'(ldx[bhwd]w?|ldxb|ldxdw|ldxw|ldxh) (r\d+), \[(r\d+) ([+-]) (0x[0-9a-f]+)\]',ins)
    if re.match(r'jne r\d+, 0x1, \+0x1',ins): checks.append(i)
    if m:
        op,d,b,sg,off=m.groups(); off=int(off,16)*(1 if sg=='+' else -1)
        if b=='r10':
            reg[d]=stk.get(off,('L',i)); continue
        if b not in reg: reg[b]=('IN',i); defs[('IN',i)]=(a,'live-in '+b)
        if b in reg:
            uses.setdefault(reg[b],[]).append((i,off,op))
        reg[d]=('L',i); defs[('L',i)]=(a,ins); continue
    m=re.match(r'stxdw \[r10 - (0x[0-9a-f]+)\], (r\d+)',ins)
    if m:
        s=-int(m.group(1),16)
        if m.group(2) in reg: stk[s]=reg[m.group(2)]
        continue
    m=re.match(r'mov64 (r\d+), (r\d+)$',ins)
    if m:
        if m.group(2) in reg: reg[m.group(1)]=reg[m.group(2)]
        else: reg.pop(m.group(1),None)
        continue
    m=re.match(r'\w+ (r\d+),',ins)
    if m and not ins.startswith(('stx','st','j')): reg[m.group(1)]=('X',i)
    if ins.startswith('call') and ins!='call -0x1':
        for r in ('r0','r1','r2','r3','r4','r5'): reg.pop(r,None)
out=[]
for d,us in uses.items():
    offs=set(o for _,o,_ in us)
    for b in sorted(set(o-8 for o in offs)):
        if b+8 not in offs or b+0x10 not in offs or b<0 or 0<b<0x30: continue
        il=[i for i,o,_ in us if o==b+8][0]; idt=[i for i,o,_ in us if o==b+0x10][0]
        c1=next((c for c in checks if c>il),10**9); c2=next((c for c in checks if c>idt),10**9)
        B=['','','']
        for i,o,op in us:
            r=o-b
            if r in F and ((r<0x28)==(op=='ldxdw')):
                B[0 if i<c1 else 1 if i<c2 else 2]+=F[r]
        a,ins=defs.get(d,(lst[d[1]][0],lst[d[1]][1]))
        out.append((lst[il][0],a,ins+('' if b==0 else ' +%#x'%b),'|'.join(B)))
for x in sorted(out): print('%05x def@%05x %-28s %s'%x)
