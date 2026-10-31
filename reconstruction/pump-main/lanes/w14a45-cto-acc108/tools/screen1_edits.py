import sys; sys.path.insert(0,'tools'); from ed import *
BR = ("  store i8 %ctx.val57, ptr %_111.i, align 1, !noalias !8627", "  %bre = getelementptr inbounds i8, ptr %ctx, i64 35\n  %brl = load i8, ptr %bre, align 1\n  store i8 %brl, ptr %_111.i, align 1, !noalias !8627")
L84 = 'bb84:                                             ; preds = %bb35'
A = {'b1': [BR], 'g1': [remat('%327')], 'g2': [remat('%327', keep=2)], 'g3': [remat('%327', keep=3)],
     's1': [via_slot('%327')], 'sb': [via_slot('%ctx.val57', keep=0, tag='b', ty='i8')],
     'fu84': [lambda t: t.replace(L84 + '\n', L84 + '\n  call void asm sideeffect "", "r"(i8 %_539.sroa.0.0)\n', 1)]}
def get(c): return [e for k in c for e in A[k]]
def _nslot(t):
    t = t.replace("  %323 = icmp eq i32 %322, 0\n", "  store i32 %322, ptr %nslot, align 8\n", 1)
    t = t.replace("  br i1 %323, label %bb26.i118, label %bb34.i", "  %nl = load i32, ptr %nslot, align 8\n  %natv = icmp eq i32 %nl, 0\n  br i1 %natv, label %bb26.i118, label %bb34.i", 1)
    return t.replace("  %_11.i269 = alloca [0 x i8], align 1", "  %nslot = alloca [8 x i8], align 8\n  %_11.i269 = alloca [0 x i8], align 1", 1)
def _nlate(t):  # recompute native at the use: icmp sunk to bb25.i (keeps i32 live)
    t = t.replace("  %323 = icmp eq i32 %322, 0\n", "", 1)
    return t.replace("  br i1 %323, label %bb26.i118, label %bb34.i", "  %natv = icmp eq i32 %322, 0\n  br i1 %natv, label %bb26.i118, label %bb34.i", 1)
A['ns'] = [_nslot]; A['nl'] = [_nlate]
