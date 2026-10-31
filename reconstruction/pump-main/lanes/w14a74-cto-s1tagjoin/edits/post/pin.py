import re,sys
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a74-cto-s1tagjoin/reconstruction/pump-main/lanes/w14a74-cto-s1tagjoin/edits/post')
from common import *
def pin_sw(t,end=True):
    d=info(t); sw=d['sw']; j=joinlab(t)
    # define pinned copy after join phis, replace the event store use
    t=t.replace('  store i64 '+sw+', ptr ','  store i64 %swp, ptr ',1)
    t=at_block(t,j,'  %swp = call i64 asm sideeffect "", "={r9},0"(i64 '+sw+')\n')
    if end:
        t=t.replace('  store i64 %swp, ptr ','  call void asm sideeffect "", "{r9}"(i64 %swp)\n  store i64 %swp, ptr ',1)
    return t
def pin_tag(t):
    d=info(t); tag=d['tag']; j=joinlab(t)
    t=t.replace('  '+d['tst']+' = icmp ne i8 '+tag+', 2','  '+d['tst']+' = icmp ne i8 %tgp, 2',1)
    t=re.sub(r'(\n'+re.escape(d['yes'])+r':[^\n]*\n  store i8 )'+re.escape(tag),r'\1%tgp',t,1)
    t=t.replace('%evtag_dummy','')
    t=at_block(t,j,'  %tgp = call i8 asm sideeffect "", "={r6},0"(i8 '+tag+')\n')
    return t
def pin_sw2(t,usepin=True):
    d=info(t); sw=d['sw']; j=joinlab(t)
    if usepin:
        t=t.replace('  store i64 '+sw+', ptr ','  %swq = call i64 asm "", "=r,{r9}"(i64 %swp)\n  store i64 %swq, ptr ',1)
    else:
        t=t.replace('  store i64 '+sw+', ptr ','  store i64 %swp, ptr ',1)
    t=at_block(t,j,'  %swp = call i64 asm "", "={r9},0"(i64 '+sw+')\n')
    return t
def pin_tag2(t):
    d=info(t); tag=d['tag']; j=joinlab(t)
    t=t.replace('  '+d['tst']+' = icmp ne i8 '+tag+', 2','  '+d['tst']+' = icmp ne i8 %tgp, 2',1)
    t=re.sub(r'(\n'+re.escape(d['yes'])+r':[^\n]*\n  store i8 )'+re.escape(tag),r'\1%tgp',t,1)
    t=at_block(t,j,'  %tgp = call i8 asm "", "={r6},0"(i8 '+tag+')\n')
    return t
