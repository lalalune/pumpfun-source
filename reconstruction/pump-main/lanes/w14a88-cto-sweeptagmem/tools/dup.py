# dup.py: helper for post-opt edits that thread the sweep join tag test into exit preds
import re
J='bb56.i'
LT='call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %dest.i), !noalias !8628\n  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_116.sroa.5.i)\n  '
def blockspan(t,label):
    i=t.index('\n'+label+':')+1
    j=t.index('\n\n',i)
    return i,j
def dup(t,site,ok='bb89',err_join='bb67',ne=False,w=None):
    S=site.strip('"')
    # site block
    lab=site
    i,j=blockspan(t,lab)
    blk=t[i:j]
    assert blk.count('br label %bb56.i')==1,blk[-200:]
    # bb56 phis
    a,b=blockspan(t,J)
    jb=t[a:b]
    ref='%'+site
    m0=re.search(r'%_426\.sroa\.0\.2 = phi i64 (.*)\n',jb); m1=re.search(r'%_426\.sroa\.18\.2 = phi i64 (.*)\n',jb)
    def pick(s):
        for x in re.finditer(r'\[ ([^,]+), ([^\]]+) \]',s):
            if x.group(2).strip()==ref: return x.group(1),x.group(0)
        raise KeyError(ref)
    T,e0=pick(m0.group(1)); P,e1=pick(m1.group(1))
    jb2=jb.replace(', '+e0,'').replace(e0+', ','').replace(', '+e1,'').replace(e1+', ','')
    n=re.sub(r'[^\w]','_',S)
    W=(', !prof !%s'%w) if w else ''
    if ne: blk2=blk.replace('br label %bb56.i',LT+'%%dupc.%s = icmp ne i64 %s, 2\n  br i1 %%dupc.%s, label %%dupE.%s, label %%%s%s'%(n,T,n,n,ok,W))
    else: blk2=blk.replace('br label %bb56.i',LT+'%%dupc.%s = icmp eq i64 %s, 2\n  br i1 %%dupc.%s, label %%%s, label %%dupE.%s%s'%(n,T,n,ok,n,W))
    blk2+='\n\ndupE.%s:\n  %%dupp.%s = inttoptr i64 %s to ptr\n  br label %%%s'%(n,n,P,err_join)
    t=t[:i]+blk2+t[j:]
    a,b=blockspan(t,J); t=t[:a]+jb2+t[b:]
    # ok phi
    a,b=blockspan(t,ok); ob=t[a:b]
    ob2=re.sub(r'(%_95\.sroa\.0\.0 = phi i64 [^\n]*)',lambda m:m.group(1)+', [ %s, %s ]'%(P,ref),ob,count=1)
    assert ob2!=ob
    t=t[:a]+ob2+t[b:]
    a,b=blockspan(t,err_join); eb=t[a:b]
    eb=re.sub(r'(%_0\.sroa\.11\.4 = phi ptr [^\n]*)',lambda m:m.group(1)+', [ %%dupp.%s, %%dupE.%s ]'%(n,n),eb,count=1)
    eb=re.sub(r'(%_0\.sroa\.0\.4 = phi i64 [^\n]*)',lambda m:m.group(1)+', [ %s, %%dupE.%s ]'%(T,n),eb,count=1)
    t=t[:a]+eb+t[b:]
    return t
_k=[99900]
def W(t,a,b):
    _k[0]+=1; k=_k[0]
    return t+'\n!%d = !{!"branch_weights", i32 %d, i32 %d}\n'%(k,a,b), k
def dupw(t,site,a,b,**kw):
    t,k=W(t,a,b); return dup(t,site,w=k,**kw)
