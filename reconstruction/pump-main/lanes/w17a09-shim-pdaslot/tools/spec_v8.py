V={}
A='  %_275 = load ptr, ptr %18, align 8, !nonnull !2, !align !3, !noundef !2\n'
B='  %_279 = load ptr, ptr %35, align 8, !nonnull !2, !align !3, !noundef !2\n'
vol=lambda s: s.replace('load ptr','load volatile ptr')
V['cvA']=[(A,vol(A))]
V['cvB']=[(B,vol(B))]
V['cvAB']=[(A,vol(A)),(B,vol(B))]
S1='  %_20 = load ptr, ptr %24, align 8, !nonnull !2, !align !3, !noundef !2\n'
