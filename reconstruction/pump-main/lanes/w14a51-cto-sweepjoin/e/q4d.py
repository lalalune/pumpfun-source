import os,runpy
q4=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'q4.py'))['f']
LE='  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_114.sroa.5.i)\n'
def f(t):
    t=q4(t)
    MODE=os.environ.get('MODE','joins')
    assert t.count(LE)==1; t=t.replace(LE,'')
    if MODE=='joins':
        for b in ['  br label %bb57.i\n\nbb86.i:','  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %dest.i), !noalias !8627\n  br label %_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit\n\nbb53.i111:']:
            pass
        # insert into bb49 and bb57 right before their br to exit
        import re
        for X in ['bb49.i','bb57.i']:
            i=t.index('\n'+X+':')+1; j=t.index('\n\n',i); blk=t[i:j]
            k=blk.rindex('  br label')
            blk=blk[:k]+LE+blk[k:]; t=t[:i]+blk+t[j:]
    return t
EDITS=[f]
