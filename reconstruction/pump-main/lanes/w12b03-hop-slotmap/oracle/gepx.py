import os
POS=os.environ['POS']
A='  %_218 = getelementptr inbounds i8, ptr %_618, i64 8\n'
def edit(t):
    assert t.count(A)==1
    t=t.replace(A,'',1)
    anchors={
     'b57top':'  %_618 = load ptr, ptr %ctx.8.val, align 8, !nonnull !2, !align !3, !noundef !2\n',
     'b57end':'  %_205.not = icmp eq i8 %293, 0\n',
     'b58top':'bb58:                                             ; preds = %bb57\n',
     'b58end':'  %.not = icmp eq i32 %298, 0\n',
    }
    if POS=='b56':
        # need _618 available: move load of _618 to bb56 too
        L=anchors['b57top']; t=t.replace(L,'',1)
        b='  %reserves = load i64, ptr %284, align 8, !noundef !2\n'
        t=t.replace(b,b+L+A,1); return t
    if POS=='b56gep_only_after_load':
        L=anchors['b57top']; t=t.replace(L,'',1)
        b='  %reserves = load i64, ptr %284, align 8, !noundef !2\n'
        t=t.replace(b,b+L,1)
        t=t.replace('  %_870 = getelementptr inbounds i8, ptr %_618, i64 648\n','  %_870 = getelementptr inbounds i8, ptr %_618, i64 648\n'+A,1); return t
    a=anchors[POS]; assert t.count(a)==1
    t=t.replace(a,a+A,1)
    return t
