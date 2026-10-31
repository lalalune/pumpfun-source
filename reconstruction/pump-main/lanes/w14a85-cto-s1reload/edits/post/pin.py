import os
# pin swept to a register R (env PR, default r9) at its join def and at the event store (inline asm, pricing only)
R=os.environ.get('PR','r9'); M=os.environ.get('PM','both')
def f(t):
    a='  call void @llvm.lifetime.start.p0(i64 16, ptr nonnull %_106)\n'
    if M in ('both','def'):
        t=t.replace(a,'  %swp = call i64 asm "", "={'+R+'},0"(i64 %_95.sroa.0.0)\n'+a,1); v='%swp'
    else: v='%_95.sroa.0.0'
    s='  store i64 %_95.sroa.0.0, ptr %715, align 8\n'
    if M in ('both','use'):
        t=t.replace(s,'  %swq = call i64 asm "", "={'+R+'},0"(i64 '+v+')\n  store i64 %swq, ptr %715, align 8\n',1)
    else: t=t.replace(s,s.replace('%_95.sroa.0.0',v),1)
    return t
EDITS=[f]
