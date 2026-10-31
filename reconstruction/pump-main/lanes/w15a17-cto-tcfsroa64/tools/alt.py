#!/usr/bin/env python3
"""alt.py <m.ll> [<call-regex>]: alloca/lifetime table for one CPI (experiment only).
Prints the [5 x i8] padding allocas of the function and the event sequence inside the CPI window
(from the 664/other CpiContext lifetime.start to the CPI call): lifetime.start (name,size), loads at
AccountInfo offsets 32 (R), 40 (S), 41 (W), 42 (E), and Rc inc (C)."""
import sys,re
f=sys.argv[1]; callre=sys.argv[2] if len(sys.argv)>2 else 'transfer_creator_fees_to_pump_v2'
L=open(f).read().split('\n')
# function body of execute
st=[i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l][0]
en=st+[i for i,l in enumerate(L[st:]) if l=='}'][0]
B=L[st:en]
pad=[re.match(r'\s*(%\S+) = alloca \[(\d+) x i8\]',l) for l in B]
pad=[(m.group(1),int(m.group(2))) for m in pad if m and int(m.group(2))<8]
print('small allocas:',' '.join(f'{n}[{s}]' for n,s in pad))
ci=[i for i,l in enumerate(B) if re.search(r'call .*'+callre,l)]
if not ci: print('no call'); sys.exit()
import os; c=ci[int(os.environ.get("NTH","0"))]
# window start: last lifetime.start of a >=500 B alloca before the call
w=max(i for i in range(c) if re.search(r'lifetime.start.p0\(i64 (\d{3,})',B[i]) and int(re.search(r'i64 (\d+)',B[i]).group(1))>=int(sys.argv[3] if len(sys.argv)>3 else 500))
ev=[]; gepv={}
for l in B[w:c]:
    m=re.match(r'\s*(%\S+) = getelementptr inbounds i8, ptr (%\S+), i64 (\d+)',l)
    if m: gepv[m.group(1)]=(m.group(2),int(m.group(3)))
    m=re.search(r'lifetime.start.p0\(i64 (\d+), ptr nonnull (%\S+)\)',l)
    if m: ev.append(f'L{m.group(1)}:{m.group(2)}'); continue
    m=re.match(r'\s*%\S+ = load (i8|i64), ptr (%\S+),',l)
    if m and m.group(2) in gepv:
        o=gepv[m.group(2)][1]; t={32:'R',40:'S',41:'W',42:'E'}.get(o)
        if t and ((t=='R')==(m.group(1)=='i64')): ev.append(t)
        continue
    if re.search(r'%strong1\S* = add i64',l): ev.append('C')
s=' '.join(ev)
s=re.sub(r'(C )+','C* ',s+' ').strip()
print('events:',s)
