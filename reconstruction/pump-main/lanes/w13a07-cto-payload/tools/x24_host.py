#!/usr/bin/env python3
"""x24_host.py in.ll out.ll POS START SIZE: add a SIZE-byte alloca %x24 before alloca %POS, lifetime from START
('st' = at the CtoState lifetime.start, 'entry' = function entry, 'join' = top of bb22) to just before
prepare_bonding_curve, written (volatile) at the join so it cannot be removed."""
import sys,re
s=open(sys.argv[1]).read(); pos,start,size=sys.argv[3],sys.argv[4],int(sys.argv[5])
def rep(o,n):
    global s
    assert s.count(o)==1,(o,s.count(o)); s=s.replace(o,n)
m=re.search(r'\n  %'+re.escape(pos)+r' = alloca',s); i=m.start()+1
s=s[:i]+f'  %x24 = alloca [{size} x i8], align 8\n'+s[i:]
LS=f'  call void @llvm.lifetime.start.p0(i64 {size}, ptr nonnull %x24)\n'
if start=='st': rep('  call void @llvm.lifetime.start.p0(i64 48, ptr nonnull %st)\n','  call void @llvm.lifetime.start.p0(i64 48, ptr nonnull %st)\n'+LS)
m=re.search(r'\nbb22:[^\n]*\n((?:  %[^\n]*= phi [^\n]*\n)+)',s); j=m.end()
ins=(LS if start=='join' else '')+'  store volatile i64 0, ptr %x24, align 8\n'
s=s[:j]+ins+s[j:]
rep('; call pump_recovered::extend::prepare_bonding_curve\n',f'  call void @llvm.lifetime.end.p0(i64 {size}, ptr nonnull %x24)\n; call pump_recovered::extend::prepare_bonding_curve\n')
open(sys.argv[2],'w').write(s)
