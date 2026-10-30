# w14a06 e3 ported to 06967d3: sweep AMM transfer Err threaded straight into the sweep Err edge block bb88
SE='%_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
EDITS=[('  %508 = extractvalue { i64, ptr } %505, 1\n  br label %bb59.i105','  %508 = extractvalue { i64, ptr } %505, 1\n  br label %bb88'),
('bb88:                                             ; preds = '+SE+'\n  %566 = inttoptr i64 %_415.sroa.18.4 to ptr',
 'bb88:                                             ; preds = '+SE+'\n  %566 = phi ptr [ %p566x, '+SE+' ], [ %508, %bb85.i ]\n  %t88 = phi i64 [ %_415.sroa.0.4, '+SE+' ], [ %506, %bb85.i ]'),
('  %557 = icmp eq i64 %_415.sroa.0.4, 2\n  br i1 %557, label %bb89, label %bb88','  %557 = icmp eq i64 %_415.sroa.0.4, 2\n  %p566x = inttoptr i64 %_415.sroa.18.4 to ptr\n  br i1 %557, label %bb89, label %bb88'),
('[ %_415.sroa.0.4, %bb88 ]','[ %t88, %bb88 ]'),
('[ %506, %bb85.i ], ',''),('[ %508, %bb85.i ], ','')]
