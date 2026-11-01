V={}
A='  %_20 = load ptr, ptr %24, align 8, !nonnull !2, !align !3, !noundef !2\n'
B='  %_22 = load ptr, ptr %31, align 8, !nonnull !2, !align !3, !noundef !2\n'
C='  %_395 = load ptr, ptr %16, align 8, !nonnull !2, !align !3, !noundef !2\n'
D='  %_273 = load ptr, ptr %18, align 8, !nonnull !2, !align !3, !noundef !2\n'
vol=lambda s: s.replace('load ptr','load volatile ptr')
V['volA']=[(A,vol(A))]
V['volB']=[(B,vol(B))]
V['volAB']=[(A,vol(A)),(B,vol(B))]
V['volC']=[(C,vol(C))]
V['volABC']=[(A,vol(A)),(B,vol(B)),(C,vol(C))]
V['volD']=[(D,vol(D))]
V['volAD']=[(A,vol(A)),(D,vol(D))]
V['volABD']=[(A,vol(A)),(B,vol(B)),(D,vol(D))]
