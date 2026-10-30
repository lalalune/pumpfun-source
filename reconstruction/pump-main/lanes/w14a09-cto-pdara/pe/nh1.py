A='''  %target.i.sroa.7.0..sroa_idx = getelementptr inbounds i8, ptr %new, i64 8
  %target.i.sroa.7.0.copyload269 = load i64, ptr %target.i.sroa.7.0..sroa_idx, align 1, !noalias !8575
  %target.i.sroa.8.0..sroa_idx = getelementptr inbounds i8, ptr %new, i64 16
  %target.i.sroa.8.0.copyload270 = load ptr, ptr %target.i.sroa.8.0..sroa_idx, align 1, !noalias !8575
'''
T='''  %_39.sroa.0.0.copyload = load i8, ptr %new, align 1
'''
EDITS=[(A,''),(T,T+A.replace(', !noalias !8575',''))]
