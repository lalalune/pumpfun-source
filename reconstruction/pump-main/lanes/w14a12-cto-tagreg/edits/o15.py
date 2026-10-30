H=("  %668 = load ptr, ptr %5, align 8, !nonnull !2, !align !3, !noundef !2\n  %669 = getelementptr inbounds i8, ptr %668, i64 165\n  %670 = load i8, ptr %669, align 1, !range !394, !noundef !2\n  %671 = icmp ne i8 %670, 0\n")
H2=H.replace('%668','%h668').replace('%669','%h669').replace('%670','%h670').replace('%671 =','%h671 =')
C="  %686 = call { i64, ptr } @_ZN14pump_recovered8pump_amm3cpi14admin_cto_pool17h6db7cfeb87b39219E(ptr noalias nocapture noundef nonnull align 8 dereferenceable(424) %_175, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(32) %target13, i1 noundef zeroext %671,"
def ren(t):
    import re
    # renumber: drop H, then shift later unnamed values down by 4
    i=t.index(H); j=t.index('\n}\n',i)
    body=t[i+len(H):j]
    body=re.sub(r'%(\d+)\b',lambda m:'%'+str(int(m.group(1))-4) if int(m.group(1))>671 else m.group(0),body)
    return t[:i]+body+t[j:]
EDITS=[(C,H2+C.replace('%671,','%h671,')),ren]

EDITS=[('  %nf = load i64, ptr %663, align 8, !noundef !2\n', ''), ('  store i64 %nf, ptr %702, align 8\n', '  %nfx = getelementptr inbounds i8, ptr %_319, i64 112\n  %nf = load i64, ptr %nfx, align 8\n  store i64 %nf, ptr %702, align 8\n')]+EDITS
