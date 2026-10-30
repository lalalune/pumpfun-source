import re
C139='%"_ZN71_$LT$solana_account_info..AccountInfo$u20$as$u20$core..clone..Clone$GT$5clone17h759150bcde62cc00E.exit139"'
C204='%"_ZN71_$LT$solana_account_info..AccountInfo$u20$as$u20$core..clone..Clone$GT$5clone17h759150bcde62cc00E.exit204"'
import os
MODE=os.environ.get('MODE','all')
def rm(t,lines):
    for l in lines:
        assert l in t, l
        t=t.replace(l+'\n','',1)
    return t
def edit(t):
    qm = MODE in ('all','qm')
    base = MODE in ('all','base')
    if qm:
        t=rm(t,['  %158 = getelementptr inbounds i8, ptr %157, i64 48','  %159 = load i8, ptr %158, align 8','  %160 = getelementptr inbounds i8, ptr %157, i64 88','  %161 = load ptr, ptr %160, align 8',
                '  %203 = getelementptr inbounds i8, ptr %202, i64 48','  %204 = load i8, ptr %203, align 8','  %205 = getelementptr inbounds i8, ptr %202, i64 88','  %206 = load ptr, ptr %205, align 8'])
        t=re.sub(r'  %_95.sroa.0.1 = phi i8 .*\n', f'  %qmb = phi ptr [ %202, %bb36 ], [ %157, {C139} ], [ %202, {C204} ]\n',t)
        t=re.sub(r'  %_96.sroa.0.1 = phi ptr .*\n', '',t)
    if base:
        t=rm(t,['  %136 = getelementptr inbounds i8, ptr %135, i64 88','  %137 = load ptr, ptr %136, align 8','  %180 = getelementptr inbounds i8, ptr %179, i64 88','  %181 = load ptr, ptr %180, align 8'])
        t=re.sub(r'  %_90.sroa.0.1 = phi ptr .*\n', f'  %bmb = phi ptr [ %179, %bb36 ], [ %135, {C139} ], [ %179, {C204} ]\n',t)
    loads=''
    if base: loads+='  %bmg = getelementptr inbounds i8, ptr %bmb, i64 88\n  %_90.sroa.0.1 = load ptr, ptr %bmg, align 8\n'
    if qm: loads+='  %qmg = getelementptr inbounds i8, ptr %qmb, i64 48\n  %_95.sroa.0.1 = load i8, ptr %qmg, align 8\n  %qmg2 = getelementptr inbounds i8, ptr %qmb, i64 88\n  %_96.sroa.0.1 = load ptr, ptr %qmg2, align 8\n'
    t=t.replace('  %_94.sroa.0.1 = getelementptr inbounds i8, ptr %a, i64 32\n','  %_94.sroa.0.1 = getelementptr inbounds i8, ptr %a, i64 32\n'+loads,1)
    return t
