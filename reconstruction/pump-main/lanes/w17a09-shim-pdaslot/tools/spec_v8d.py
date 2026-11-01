V={}
PDA='; call solana_pubkey::Pubkey::find_program_address\n'
SCV='  %scg = getelementptr inbounds i8, ptr %_272, i64 144\n  %scv = load volatile ptr, ptr %scg, align 8, !nonnull !2, !align !3, !noundef !2\n'
K='  %_399 = load ptr, ptr %16, align 8, !nonnull !2, !align !3, !noundef !2\n  %_400 = load ptr, ptr %_399, align 8'
K2='  %_400 = load ptr, ptr %scv, align 8'
A='  %_22 = load ptr, ptr %24, align 8, !nonnull !2, !align !3, !noundef !2\n'
B='  %_24 = load ptr, ptr %31, align 8, !nonnull !2, !align !3, !noundef !2\n'
CB='  %_279 = load ptr, ptr %35, align 8, !nonnull !2, !align !3, !noundef !2\n'
vol=lambda s: s.replace('load ptr','load volatile ptr')
early=[(PDA,SCV+PDA),(K,K2)]
V['e1']=early
V['e1cb']=early+[(CB,vol(CB))]
V['e1ab']=early+[(A,'  %_22 = bitcast ptr %scv to ptr\n'),(B,'  %_24 = bitcast ptr %scv to ptr\n')]
V['e1abcb']=V['e1ab']+[(CB,vol(CB))]
