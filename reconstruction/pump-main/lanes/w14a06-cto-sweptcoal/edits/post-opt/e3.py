SE='%_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
EDITS=[('  %507 = extractvalue { i64, ptr } %504, 1\n  br label %bb60.i','  %507 = extractvalue { i64, ptr } %504, 1\n  br label %bb80'),
('bb80:                                             ; preds = '+SE+'\n  %565 = inttoptr i64 %_384.sroa.18.4 to ptr',
 'bb80:                                             ; preds = '+SE+'\n  %565 = phi ptr [ %p565x, '+SE+' ], [ %507, %bb83.i124 ]\n  %t80 = phi i64 [ %_384.sroa.0.4, '+SE+' ], [ %505, %bb83.i124 ]'),
('br i1 %556, label %bb81, label %bb80','%p565x = inttoptr i64 %_384.sroa.18.4 to ptr\n  br i1 %556, label %bb81, label %bb80'),
('[ %_384.sroa.0.4, %bb80 ]','[ %t80, %bb80 ]'),
('[ %505, %bb83.i124 ], ',''),('[ %507, %bb83.i124 ], ','')]
