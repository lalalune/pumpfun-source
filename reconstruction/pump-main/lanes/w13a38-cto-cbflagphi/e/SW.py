J69="bb69:                                             ; preds = %bb58.i, %bb44.i, %bb45.i\n"
J54="bb54.i:                                           ; preds = %bb93.i, %bb52.i\n"
CBDEF="  %43 = xor i1 %_0.sroa.0.0.off0.i45, true\n  %cashback.sroa.0.0.off0 = and i1 %_40.not, %43\n"
CBUSE="%167 = zext i1 %cashback.sroa.0.0.off0 to i8"
HUSE1="br i1 %_0.sroa.0.0.off0.i45, label %bb23, label %bb18"
HUSE2="%571 = zext i1 %_0.sroa.0.0.off0.i45 to i8"
B45="  %switch12.i = icmp eq i64 %0, 0\n  br i1 %switch12.i, label %bb69, label %bb47.i\n"
ST_CB="  %_301 = load ptr, ptr %4, align 8, !nonnull !2, !align !3, !noundef !2\n  %569 = getelementptr inbounds i8, ptr %_301, i64 163\n  store i8 %167, ptr %569, align 1\n"
ST_H="  %_302 = load ptr, ptr %4, align 8, !nonnull !2, !align !3, !noundef !2\n  %570 = getelementptr inbounds i8, ptr %_302, i64 165\n  %571 = zext i1 %_0.sroa.0.0.off0.i45 to i8\n  store i8 %571, ptr %570, align 1\n"
def _ren(x): return x.replace('%569','%cbgep').replace('%570','%hgep').replace('%571','%hz')
def SWAP(t):
    a=ST_CB+ST_H; assert t.count(a)==1; return t.replace(a,_ren(ST_H+ST_CB))
def SWAPH(t):
    a=ST_CB+ST_H.replace('%_0.sroa.0.0.off0.i45','%hJ'); assert t.count(a)==1; return t.replace(a,_ren(ST_H.replace('%_0.sroa.0.0.off0.i45','%hJ')+ST_CB))
EDITS=[SWAP]
