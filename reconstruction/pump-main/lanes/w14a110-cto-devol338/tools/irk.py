#!/usr/bin/env python3
"""irk.py <kind>...: post-opt IR instruction-kind screen for the line-338 fee-Some exit block (bb65.i) of main 963d1ee.
Writes rx/<kind>/m.ll from rx/m/m.ll. Oracle only, never a source proposal."""
import sys,os,re
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M=open(O+'/rx/m/m.ll').read()
VOL='  %167 = load volatile i8, ptr %holder_key, align 1, !alias.scope !8547, !noalias !8582\n'
B76='bb76:                                             ; preds = %bb65.i, %bb44.i, %bb45.i\n'
SW='  %switch54 = icmp eq i64 %1, 1\n'
CPI='i1 noundef zeroext %685, i64 noundef %1, i64 %2) #27'
C7='  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %target.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %target.i.sroa.0, i64 7, i1 false)\n'
C9a='  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(9) %_48.sroa.11, ptr noundef nonnull align 1 dereferenceable(9) %target.i.sroa.9, i64 9, i1 false)\n'
def rep(t,a,b,n=1):
    assert t.count(a)==n,(t.count(a),a[:80]); return t.replace(a,b)
def phi(t,ty='i64',v=('0','1','0'),name='%feet'):
    return rep(t,B76,B76+f'  {name} = phi {ty} [ {v[0]}, %bb45.i ], [ {v[1]}, %bb65.i ], [ {v[2]}, %bb44.i ]\n')
def split(t,pred,cond_lbl_old,body,nm):
    """split edge pred->bb76 into new block nm holding body"""
    # find pred block's terminator br to bb76
    i=t.index('\n'+pred+':'); j=t.index('\n\n',i)
    blk=t[i:j]; nb=blk.replace('label %bb76,','label %'+nm+',').replace('label %bb76\n','label %'+nm+'\n')
    assert nb!=blk; t=t[:i]+nb+t[j:]
    t=rep(t,B76,f'{nm}:\n{body}  br label %bb76\n\n'+B76)
    return t.replace('%bb45.i ]','%'+nm+' ]',100) if False else t
K={}
K['e0']=lambda t: rep(t,VOL,'')
K['f1']=lambda t: rep(phi(rep(t,VOL,'')),SW,'  %switch54 = icmp eq i64 %feet, 1\n')
K['f1b']=lambda t: rep(K['f1'](t),CPI,'i1 noundef zeroext %685, i64 noundef %feet, i64 %2) #27')
K['f1i']=lambda t: rep(phi(rep(t,VOL,''),'i1',('false','true','false'),'%feeb'),SW,'  %switch54 = or i1 %feeb, false\n')
K['f1v']=lambda t: rep(K['f1'](t),VOL,'') if False else rep(phi(t),SW,'  %switch54 = icmp eq i64 %feet, 1\n')  # keep volatile + phi
K['s_st']=lambda t: rep(t,VOL,'  store i64 %2, ptr %37, align 8\n')
K['s_st1']=lambda t: rep(t,VOL,'  store i64 1, ptr %37, align 8\n')
K['s_stb']=lambda t: rep(t,VOL,'  store i8 1, ptr %38, align 8\n')
def c7(t,piece=C7):
    t=rep(t,VOL,piece); t=rep(t,B76+'  %target.i.sroa.7.0',B76+'  %target.i.sroa.7.0')
    # remove from bb76 (first occurrence after B76) and add to the other two preds on split edges
    i=t.index(B76); j=t.index(piece,i); t=t[:j]+t[j+len(piece):]
    for p,nm in (('bb45.i','e45'),('bb44.i','e44')):
        i=t.index('\n'+p+':'); j=t.index('\n\n',i); blk=t[i:j]
        nb=re.sub(r'label %bb76\b','label %'+nm,blk,count=1); t=t[:i]+nb+t[j:]
        t=rep(t,B76,f'{nm}:\n{piece}  br label %bb76\n\n'+B76)
        t=t.replace(f'[ %target.i.sroa.7.0.copyload{"295" if p=="bb45.i" else ""}, %{p} ]',f'[ %target.i.sroa.7.0.copyload{"295" if p=="bb45.i" else ""}, %{nm} ]')
        t=t.replace(f'[ %target.i.sroa.8.0.copyload{"296" if p=="bb45.i" else ""}, %{p} ]',f'[ %target.i.sroa.8.0.copyload{"296" if p=="bb45.i" else ""}, %{nm} ]')
    t=t.replace(B76,'bb76:                                             ; preds = %bb65.i, %e44, %e45\n')
    return t
K['c7']=c7
K['c9']=lambda t: c7(t,C9a)
K['c7only']=lambda t: rep(t,VOL,C7)   # extra redundant copy in bb65.i (dup)
K['l_hk']=lambda t: rep(t,VOL,'  %167 = load i8, ptr %holder_key, align 1\n  store i8 %167, ptr %38, align 8\n')
for k in sys.argv[1:]:
    t=K[k](M); d=f'{O}/rx/{k}'; os.makedirs(d,exist_ok=True)
    for f in ('m.s','m.o','B.s','Br.s'):
        if os.path.exists(f'{d}/{f}'): os.remove(f'{d}/{f}')
    open(d+'/m.ll','w').write(t); print('wrote',k)
