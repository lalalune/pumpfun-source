def edit(t):
    a = t.index('define internal fastcc') if False else 0
    old = "br i1 %_210, label %bb62, label %bb75.thread\n"
    assert t.count(old) == 1
    t = t.replace(old, "br i1 %_210, label %bb62, label %bbELSE\n\nbbELSE:\n  br label %bb75.thread\n")
    import re
    # phi incoming from bb61 -> bbELSE inside bb75.thread phis
    s = t.index('bb75.thread:'); e = t.index('call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %_1131', s)
    blk = t[s:e].replace('%bb61 ]', '%bbELSE ]').replace('preds = %bb278, %bb61, %bb75', 'preds = %bb278, %bbELSE, %bb75')
    return t[:s] + blk + t[e:]
