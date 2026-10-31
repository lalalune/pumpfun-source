X='%_ZN5alloc2rc10RcInnerPtr10inc_strong17hbf2f50dabd5a1ea9E.exit234'
EDITS=[('br i1 %660, label %bb34, label %bb61','br i1 %660, label %bb34, label %bb59'),
('%.pn = phi { i64, ptr } [ %725, %bb112 ],','%.pn = phi { i64, ptr } [ %658, '+X+' ], [ %725, %bb112 ],'),
('[ %658, '+X+' ], [ %.pn, %bb59 ]','[ %.pn, %bb59 ]'),('[ %659, '+X+' ], [ %_0.sroa.0.2, %bb59 ]','[ %_0.sroa.0.2, %bb59 ]')]
