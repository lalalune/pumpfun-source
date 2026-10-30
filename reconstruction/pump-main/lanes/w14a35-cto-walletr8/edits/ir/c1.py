# (c) wallet Err edges return on their own (do not join the shared Err-return phi in bb67)
import re
W='_ZN14pump_recovered9admin_cto7execute6wallet17h67aeb09bf4f58cf9E'
def T(t):
    a=t.index(W+'.exit.thread289:'); b=t.index('  br label %bb67\n',a)
    t=t[:b]+'  %wr1 = insertvalue { i64, ptr } poison, i64 %_0.sroa.0.4.i.ph, 0\n  %wr2 = insertvalue { i64, ptr } %wr1, ptr %_0.sroa.11.4.i.ph, 1\n  ret { i64, ptr } %wr2\n'+t[b+len('  br label %bb67\n'):]
    x='  %318 = icmp eq i64 %_0.sroa.0.4.i, 2\n  br i1 %318, label %bb35, label %bb67\n'
    assert t.count(x)==1
    t=t.replace(x,'  %318 = icmp eq i64 %_0.sroa.0.4.i, 2\n  br i1 %318, label %bb35, label %wret\n\nwret:\n  %wr3 = insertvalue { i64, ptr } poison, i64 %_0.sroa.0.4.i, 0\n  %wr4 = insertvalue { i64, ptr } %wr3, ptr %_0.sroa.11.4.i, 1\n  ret { i64, ptr } %wr4\n')
    for s in ['[ %_0.sroa.11.4.i.ph, %'+W+'.exit.thread289 ]','[ %_0.sroa.11.4.i, %'+W+'.exit ]','[ %_0.sroa.0.4.i.ph, %'+W+'.exit.thread289 ]','[ %_0.sroa.0.4.i, %'+W+'.exit ]']:
        assert t.count(', '+s)==1, s; t=t.replace(', '+s,'')
    t=re.sub(r'(bb67:\s+; preds = )([^\n]*)',lambda m:m.group(1)+', '.join(p for p in m.group(2).split(', ') if W not in p),t)
    return t
EDITS=[T]
