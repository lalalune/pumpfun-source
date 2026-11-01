#!/usr/bin/env python3
"""semgen.py <slim.ll> <out.jsonl>: hand-written semantic llvm.assume cells on execute (facts that hold after
validate returned Ok). Anchors are found by block label inside execute."""
import sys,re,json
src,dst=sys.argv[1:3]
L=open(src).read().split('\n')
s=next(i for i,l in enumerate(L) if l.startswith('define') and re.search(r'admin_cto7execute17h',l.split('(')[0]))
e=s
while L[e]!='}': e+=1
def lab(name):
    for i in range(s,e):
        if L[i].startswith(name+':'): return i
    raise SystemExit('no label '+name)
A='  call void @llvm.assume(i1 noundef zeroext %s)'
cells={}
def cell(cid,block,lines):
    i=lab(block); cells[cid]={'id':cid,'kind':'sem','cls':block,'fn':'execute','rep':{i:[L[i]]+lines},'extra':[],'src':cid}
tag='  %%s%d_t = load i8, ptr %%new, align 1'
n=0
def T(k): return '%%s%d_t'%k
# F12: new tag == !holder
for blk in ('bb82',):
    n+=1; cell('F12:'+blk,blk,[tag%n,'  %%s%d_a = xor i1 %%_holder, true'%n,'  %%s%d_b = zext i1 %%s%d_a to i8'%(n,n),'  %%s%d_c = icmp eq i8 %s, %%s%d_b'%(n,T(n),n),A%('%%s%d_c'%n)])
    n+=1; cell('F1:'+blk,blk,[tag%n,'  %%s%d_z = icmp eq i8 %s, 0'%(n,T(n)),'  %%s%d_a = xor i1 %%_holder, true'%n,'  %%s%d_c = or i1 %%s%d_a, %%s%d_z'%(n,n,n),A%('%%s%d_c'%n)])
    n+=1; cell('F2:'+blk,blk,[tag%n,'  %%s%d_z = icmp ne i8 %s, 0'%(n,T(n)),'  %%s%d_c = or i1 %%_holder, %%s%d_z'%(n,n),A%('%%s%d_c'%n)])
    n+=1; cell('F3:'+blk,blk,['  %%s%d_c = xor i1 %%_49, true'%n,A%('%%s%d_c'%n)])
    n+=1; cell('F4:'+blk,blk,['  %%s%d_a = xor i1 %%_50, true'%n,'  %%s%d_c = or i1 %%s%d_a, %%_holder'%(n,n),A%('%%s%d_c'%n)])
    n+=1; cell('F5:'+blk,blk,['  %%s%d_a = xor i1 %%_holder, true'%n,'  %%s%d_b = or i1 %%_50, %%_53'%n,'  %%s%d_c = or i1 %%s%d_a, %%s%d_b'%(n,n,n),A%('%%s%d_c'%n)])
    n+=1; cell('F6a:'+blk,blk,['  %%s%d_a = icmp eq i64 %%1, 0'%n,'  %%s%d_b = xor i1 %%_52, true'%n,'  %%s%d_c = or i1 %%s%d_a, %%s%d_b'%(n,n,n),A%('%%s%d_c'%n)])
    n+=1; cell('F6b:'+blk,blk,['  %%s%d_a = icmp eq i64 %%1, 0'%n,'  %%s%d_c = or i1 %%s%d_a, %%_40'%(n,n),A%('%%s%d_c'%n)])
    n+=1; cell('F6c:'+blk,blk,['  %%s%d_a = icmp eq i64 %%1, 0'%n,'  %%s%d_b = icmp ne i64 %%2, 0'%n,'  %%s%d_c = or i1 %%s%d_a, %%s%d_b'%(n,n,n),A%('%%s%d_c'%n)])
    n+=1; cell('F6d:'+blk,blk,['  %%s%d_a = icmp eq i64 %%1, 0'%n,'  %%s%d_b = icmp ule i64 %%2, %%_44'%n,'  %%s%d_c = or i1 %%s%d_a, %%s%d_b'%(n,n,n),A%('%%s%d_c'%n)])
    n+=1; cell('F6e:'+blk,blk,['  %%s%d_a = icmp eq i64 %%1, 0'%n,'  %%s%d_l = load i8, ptr %%cashback, align 1'%n,'  %%s%d_b = icmp eq i8 %%s%d_l, 0'%(n,n),'  %%s%d_c = or i1 %%s%d_a, %%s%d_b'%(n,n,n),A%('%%s%d_c'%n)])
    n+=1; cell('F7:'+blk,blk,['  %%s%d_c = icmp ule i64 %%1, 1'%n,A%('%%s%d_c'%n)])
    n+=1; cell('F8:'+blk,blk,['  %%s%d_l = load i8, ptr %%holder, align 1'%n,'  %%s%d_c = icmp ule i8 %%s%d_l, 2'%(n,n),A%('%%s%d_c'%n)])
n+=1; cell('A23tag0','bb23',[tag%n,'  %%s%d_c = icmp eq i8 %s, 0'%(n,T(n)),A%('%%s%d_c'%n)])
n+=1; cell('A24tag1','bb24',[tag%n,'  %%s%d_c = icmp eq i8 %s, 1'%(n,T(n)),A%('%%s%d_c'%n)])
n+=1; cell('A24hr0','bb24',['  %%s%d_c = xor i1 %%_50, true'%n,A%('%%s%d_c'%n)])
n+=1; cell('A26tag','bb26',[tag%n,'  %%s%d_z = icmp ne i8 %s, 0'%(n,T(n)),'  %%s%d_c = or i1 %%_holder, %%s%d_z'%(n,n),A%('%%s%d_c'%n)])
n+=1; cell('A26hr','bb26',['  %%s%d_a = xor i1 %%_50, true'%n,'  %%s%d_c = or i1 %%s%d_a, %%_holder'%(n,n),A%('%%s%d_c'%n)])
with open(dst,'w') as f:
    for c in cells.values(): f.write(json.dumps(c)+'\n')
print(len(cells))
