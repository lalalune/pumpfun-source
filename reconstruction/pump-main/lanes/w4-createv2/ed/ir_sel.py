OLD='''  br i1 %284, label %bb65.sink.split, label %bb64

bb64:                                             ; preds = %bb59
  %switch40 = icmp eq i64 %_85.sroa.0.3159, 0
  br i1 %switch40, label %bb65.sink.split, label %bb65

bb65.sink.split:                                  ; preds = %bb64, %bb59
  %.sink203 = phi i64 [ 1008, %bb59 ], [ 1064, %bb64 ]
  %285 = getelementptr inbounds i8, ptr %_247.pre.pre, i64 %.sink203
  %_132 = load i64, ptr %285, align 8, !noundef !2
  br label %bb65

bb65:                                             ; preds = %bb65.sink.split, %bb64
  %virtual_quote_reserves.sroa.0.0 = phi i64 [ %_85.sroa.16.3158, %bb64 ], [ %_132, %bb65.sink.split ]
'''
NEW='''  br i1 %284, label %solblk, label %bb64

bb64:                                             ; preds = %bb59
  %ivq.p = getelementptr inbounds i8, ptr %_247.pre.pre, i64 1064
  %ivq = load i64, ptr %ivq.p, align 8, !noundef !2
  %switch40 = icmp eq i64 %_85.sroa.0.3159, 0
  %vsel = select i1 %switch40, i64 %ivq, i64 %_85.sroa.16.3158
  br label %bb65

solblk:
  %285 = getelementptr inbounds i8, ptr %_247.pre.pre, i64 1008
  %_132 = load i64, ptr %285, align 8, !noundef !2
  br label %bb65

bb65:                                             ; preds = %solblk, %bb64
  %virtual_quote_reserves.sroa.0.0 = phi i64 [ %vsel, %bb64 ], [ %_132, %solblk ]
'''
def edit(t):
    assert t.count(OLD)==1; return t.replace(OLD,NEW)
