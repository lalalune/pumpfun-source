#!/usr/bin/env python3
"""ce3.py: w17a12 ce2.py (ve1n) ported to main 8330455eb named post-opt module (ir/m0n.ll). Experiment only."""
import sys,os,json,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); sys.path.insert(0,os.path.join(os.path.dirname(T),'tools12'))
import pscore
BASEF=os.environ.get('CE3BASE',os.environ['LANE_OUT']+'/ir/m0n.ll')
BASE=open(BASEF).read()
CURVE='  %_312 = load ptr, ptr %i5, align 8, !nonnull !2, !align !3, !noundef !2\n'
L=dict(
 g='  %i23 = getelementptr inbounds i8, ptr %_305, i64 8\n  %_316 = load ptr, ptr %i23, align 8, !nonnull !2, !align !3, !noundef !2\n',
 fc='  %i24 = getelementptr inbounds i8, ptr %_316, i64 1086\n  %i25 = load i8, ptr %i24, align 2, !range !16, !noundef !2\n',
 cr='  %i26 = getelementptr inbounds i8, ptr %_312, i64 8\n  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(32) %st, ptr noundef nonnull align 8 dereferenceable(32) %i26, i64 32, i1 false)\n',
 mf='  %i27 = getelementptr inbounds i8, ptr %_316, i64 1072\n  %_37 = load i64, ptr %i27, align 8, !noundef !2\n',
 my='  %i28 = getelementptr inbounds i8, ptr %_312, i64 162\n  %i29 = load i8, ptr %i28, align 2, !range !16, !noundef !2\n',
 hr='  %i30 = getelementptr inbounds i8, ptr %_312, i64 165\n  %i31 = load i8, ptr %i30, align 1, !range !16, !noundef !2\n',
 cb='  %i32 = getelementptr inbounds i8, ptr %_312, i64 163\n  %i33 = load i8, ptr %i32, align 1, !range !16, !noundef !2\n',
 he='  %i34 = getelementptr inbounds i8, ptr %_316, i64 1087\n  %i35 = load i8, ptr %i34, align 1, !range !16, !noundef !2\n',
 s_mf='  %i36 = getelementptr inbounds i8, ptr %st, i64 32\n  store i64 %_37, ptr %i36, align 8\n',
 s_my='  %i37 = getelementptr inbounds i8, ptr %st, i64 40\n  store i8 %i29, ptr %i37, align 8\n',
 s_hr='  %i38 = getelementptr inbounds i8, ptr %st, i64 41\n  store i8 %i31, ptr %i38, align 1\n',
 s_cb='  %i39 = getelementptr inbounds i8, ptr %st, i64 42\n  store i8 %i33, ptr %i39, align 2\n',
 s_ql='  %i40 = getelementptr inbounds i8, ptr %st, i64 43\n  %i41 = zext i1 %quote_locked.sroa.0.0.off0 to i8\n  store i8 %i41, ptr %i40, align 1\n',
 s_he='  %i42 = getelementptr inbounds i8, ptr %st, i64 44\n  store i8 %i35, ptr %i42, align 4\n',
 s_fc='  %i43 = getelementptr inbounds i8, ptr %st, i64 45\n  store i8 %i25, ptr %i43, align 1\n',
)
HEAD='  call void @llvm.lifetime.start.p0(i64 48, ptr nonnull %st)\n'
TAIL='  %i44 = and i8 %arg, -3\n'
G291='  %i20 = getelementptr inbounds i8, ptr %_305, i64 8\n  %_314 = load ptr, ptr %i20, align 8, !nonnull !2, !align !3, !noundef !2\n'
MAIN=['g','fc','cr','mf','my','hr','cb','he','s_mf','s_my','s_hr','s_cb','s_ql','s_he','s_fc']
VE1N=dict(early=('cb','hr','my'),G=True,block=['mf','he','fc','s_cb','s_hr','s_my','cr','s_ql','s_fc','s_he','s_mf'],volst=True)
def vol(s): return s.replace('store i8 ','store volatile i8 ').replace('store i64 ','store volatile i64 ')
def build(early=(),G=False,block=None,volst=False,base=None):
    t=base or BASE
    i=t.index(HEAD)+len(HEAD); j=t.index(TAIL,i); body=t[i:j]
    for k,v in L.items(): assert body.count(v)==1,k
    block=block or MAIN
    used=set(block)|set(early)|({'g'} if G else set())
    assert used==set(L),(set(L)-used,used-set(L))
    nb=''.join(vol(L[k]) if (volst and k.startswith('s_')) else L[k] for k in block)
    t=t[:i]+nb+t[j:]
    ins=(L['g'] if G else '')+''.join(L[k] for k in early)
    if ins:
        q=t.index(CURVE)+len(CURVE); t=t[:q]+ins+t[q:]
    if G:
        assert t.count(G291)==1; t=t.replace(G291,''); assert t.count('ptr %_314, i64 936')==1; t=t.replace('ptr %_314, i64 936','ptr %_316, i64 936')
    return t
def ve1n(base=None): return build(base=base,**VE1N)
if __name__=='__main__':
    print(json.dumps(pscore.score_text(build(),'ce3_main')))
    t=ve1n(); open(os.environ['LANE_OUT']+'/ir/ve1n.ll','w').write(t)
    print(json.dumps(pscore.score_text(t,'ve1n',keepobj=True)))
