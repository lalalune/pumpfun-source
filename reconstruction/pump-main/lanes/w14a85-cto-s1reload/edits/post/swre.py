# swept re-read right after the post-sweep join (orig 0x3c40 ldxdw r9,[r10-0x828]): store the phi to a slot and load a
# fresh SSA value from it at once; the event store uses the fresh value (pricing only)
import os
def f(t):
    a='  call void @llvm.lifetime.start.p0(i64 16, ptr nonnull %_106)\n'
    k=t.index(a)
    t=t[:k]+'  store i64 %_95.sroa.0.0, ptr %swslot, align 8\n  %sw2 = load i64, ptr %swslot, align 8\n'+t[k:]
    s='  store i64 %_95.sroa.0.0, ptr %715, align 8\n'
    assert t.count(s)==1; t=t.replace(s,'  store i64 %sw2, ptr %715, align 8\n')
    k=t.index('start:\n')+len('start:\n'); t=t[:k]+'  %swslot = alloca i64, align 8\n'+t[k:]
    return t
EDITS=[f]
