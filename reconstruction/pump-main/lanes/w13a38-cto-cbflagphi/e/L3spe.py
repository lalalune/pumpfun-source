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
POOLH="  %_185 = icmp ne i8 %683, 0\n"
def POOLHJ(t):
    assert t.count(POOLH)==1; return t.replace(POOLH,"  %_185 = or i1 %hJ, false\n")
EVH="  store i8 %692, ptr %698, align 8\n"
def EVHJ(t):
    assert t.count(EVH)==1; return t.replace(EVH,"  %evh = zext i1 %hJ to i8\n  store i8 %evh, ptr %698, align 8\n")
EDITS=[(J54,J54+"  %hA = phi i1 [ false, %bb52.i ], [ true, %bb93.i ]\n"),(J69,J69+"  %hJ = phi i1 [ false, %bb45.i ], [ %hA, %bb58.i ], [ true, %bb44.i ]\n"),(HUSE1,"br i1 %hJ, label %bb23, label %bb18"),(HUSE2,"%571 = zext i1 %hJ to i8"),SWAPH,POOLHJ,EVHJ]
