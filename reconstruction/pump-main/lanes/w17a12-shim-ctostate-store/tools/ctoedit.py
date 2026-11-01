#!/usr/bin/env python3
"""ctoedit.py: post-opt IR edits of execute's CtoState block (bb5/bb11) on a named (instnamer) post-opt m.ll. Experiment only."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import pscore
BASE=open(os.environ.get('PBASE',os.environ['LANE_OUT']+'/ir/q0n.ll')).read()
L=dict(
 g24='  %i23 = getelementptr inbounds i8, ptr %_275, i64 8\n',
 g286='  %_286 = load ptr, ptr %i23, align 8, !nonnull !2, !align !3, !noundef !2\n',
 fcg='  %i24 = getelementptr inbounds i8, ptr %_286, i64 1086\n',
 fcl='  %i25 = load i8, ptr %i24, align 2, !range !15, !noundef !2\n',
 crg='  %i26 = getelementptr inbounds i8, ptr %_282, i64 8\n',
 crm='  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(32) %st, ptr noundef nonnull align 8 dereferenceable(32) %i26, i64 32, i1 false)\n',
 mfg='  %i27 = getelementptr inbounds i8, ptr %_286, i64 1072\n',
 mfl='  %_34 = load i64, ptr %i27, align 8, !noundef !2\n',
 myg='  %i28 = getelementptr inbounds i8, ptr %_282, i64 162\n',
 myl='  %i29 = load i8, ptr %i28, align 2, !range !15, !noundef !2\n',
 hrg='  %i30 = getelementptr inbounds i8, ptr %_282, i64 165\n',
 hrl='  %i31 = load i8, ptr %i30, align 1, !range !15, !noundef !2\n',
 cbg='  %i32 = getelementptr inbounds i8, ptr %_282, i64 163\n',
 cbl='  %i33 = load i8, ptr %i32, align 1, !range !15, !noundef !2\n',
 heg='  %i34 = getelementptr inbounds i8, ptr %_286, i64 1087\n',
 hel='  %i35 = load i8, ptr %i34, align 1, !range !15, !noundef !2\n',
 s_mf='  %i36 = getelementptr inbounds i8, ptr %st, i64 32\n  store i64 %_34, ptr %i36, align 8\n',
 s_my='  %i37 = getelementptr inbounds i8, ptr %st, i64 40\n  store i8 %i29, ptr %i37, align 8\n',
 s_hr='  %i38 = getelementptr inbounds i8, ptr %st, i64 41\n  store i8 %i31, ptr %i38, align 1\n',
 s_cb='  %i39 = getelementptr inbounds i8, ptr %st, i64 42\n  store i8 %i33, ptr %i39, align 2\n',
 s_ql='  %i40 = getelementptr inbounds i8, ptr %st, i64 43\n  %i41 = zext i1 %quote_locked.sroa.0.0.off0 to i8\n  store i8 %i41, ptr %i40, align 1\n',
 s_he='  %i42 = getelementptr inbounds i8, ptr %st, i64 44\n  store i8 %i35, ptr %i42, align 4\n',
 s_fc='  %i43 = getelementptr inbounds i8, ptr %st, i64 45\n  store i8 %i25, ptr %i43, align 1\n',
)
HEAD='  call void @llvm.lifetime.start.p0(i64 48, ptr nonnull %st)\n'
TAIL='  %i44 = and i8 %arg, -3\n'
QLOAD='  %_282 = load ptr, ptr %i5, align 8, !nonnull !2, !align !3, !noundef !2\n'
G284='  %i20 = getelementptr inbounds i8, ptr %_275, i64 8\n  %_284 = load ptr, ptr %i20, align 8, !nonnull !2, !align !3, !noundef !2\n'
def vol(s):
    return s.replace('store i8 ','store volatile i8 ').replace('store i64 ','store volatile i64 ').replace('i64 32, i1 false)','i64 32, i1 true)')
def vload(s): return s.replace('= load i8,','= load volatile i8,').replace('= load i64,','= load volatile i64,')
def build(early=None, block=None, gearly=False, volst=False, volld=False, base=None, ins_at=QLOAD, extra=()):
    t=base or BASE
    i=t.index(HEAD)+len(HEAD); j=t.index(TAIL,i)
    body=t[i:j]
    for k,v in L.items(): assert body.count(v)==1,(k)
    early=early or []
    ins=''
    if gearly: ins+=L['g24']+L['g286']
    for k in early:
        if len(k)==2: g=L[k+'g']; l=L[k+'l']
        else: g='';l=L[k]
        if volld: l=vload(l)
        ins+=g+l
    nb=''
    for k in block:
        s=L[k]
        if (k.startswith('s_') or k=='crm') and volst: s=vol(s)
        nb+=s
    used=set(block)|set(x+'g' for x in early if len(x)==2)|set(x+'l' for x in early if len(x)==2)|set(x for x in early if len(x)>2)|({'g24','g286'} if gearly else set())
    assert used==set(L),(set(L)-used,used-set(L))
    t=t[:i]+nb+t[j:]
    if ins:
        q=t.index(ins_at)+len(ins_at); t=t[:q]+ins+t[q:]
    if gearly:
        assert t.count(G284)==1
        t=t.replace(G284,'',1); t=t.replace('ptr %_284, i64 936','ptr %_286, i64 936',1)
    for a,b in extra:
        assert t.count(a)==1,a; t=t.replace(a,b)
    return t
MAIN=['g24','g286','fcg','fcl','crg','crm','mfg','mfl','myg','myl','hrg','hrl','cbg','cbl','heg','hel','s_mf','s_my','s_hr','s_cb','s_ql','s_he','s_fc']
if __name__=='__main__':
    print(json.dumps(pscore.score_text(build(block=MAIN),'chk_main')))
