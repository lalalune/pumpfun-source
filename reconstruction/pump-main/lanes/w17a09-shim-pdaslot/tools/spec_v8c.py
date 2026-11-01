V={}
K='  %_399 = load ptr, ptr %16, align 8, !nonnull !2, !align !3, !noundef !2\n'
A='  %_22 = load ptr, ptr %24, align 8, !nonnull !2, !align !3, !noundef !2\n'
B='  %_24 = load ptr, ptr %31, align 8, !nonnull !2, !align !3, !noundef !2\n'
vol=lambda s: s.replace('load ptr','load volatile ptr')
V['scA']=[(A,vol(A))]
V['scB']=[(B,vol(B))]
V['scAB']=[(A,vol(A)),(B,vol(B))]
V['scK']=[(K,vol(K))]
V['scKAB']=[(K,vol(K)),(A,vol(A)),(B,vol(B))]
