import os
OLD='''  %_99.not = icmp ne i64 %creator_fee_bps, 0
  %258 = and i8 %_84.sroa.41.2154, -2
  %switch = icmp eq i8 %258, 2
  %or.cond = and i1 %_99.not, %switch
  br i1 %or.cond, label %bb47, label %bb59
'''
M=os.environ.get('FM','a')
NEW={'a':'''  %_99.not = icmp ne i64 %creator_fee_bps, 0
  br i1 %_99.not, label %feetag, label %bb59

feetag:
  %258 = and i8 %_84.sroa.41.2154, -2
  %switch = icmp eq i8 %258, 2
  br i1 %switch, label %bb47, label %bb59
''','b':'''  %_99.not = icmp eq i64 %creator_fee_bps, 0
  br i1 %_99.not, label %bb59, label %feetag

feetag:
  %258 = and i8 %_84.sroa.41.2154, -2
  %switch = icmp ne i8 %258, 2
  br i1 %switch, label %bb59, label %bb47
'''}[M]
def edit(t):
    assert t.count(OLD)==1; t=t.replace(OLD,NEW)
    # bb59 preds phi: bb44 -> also feetag
    a='  %fee.sroa.0.0 = phi i64 [ 0, %bb44 ], [ %creator_fee_bps, %bb52 ]'
    assert t.count(a)==1
    return t.replace(a,'  %fee.sroa.0.0 = phi i64 [ 0, %bb44 ], [ 0, %feetag ], [ %creator_fee_bps, %bb52 ]')
