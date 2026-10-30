# IR probe (w13a36 e11 form): the skip path joins the sweep Result {tag 2, value 0} before the tag test at sweep.exit
# (original orig 0x26650-0x26670), instead of being threaded straight to bb82.
SW='_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
def edit(fn):
    a='  br i1 %_504.sroa.0.0.off0, label %bb77, label %bb82\n'; assert fn.count(a)==1
    fn=fn.replace(a,'  br i1 %_504.sroa.0.0.off0, label %bb77, label %'+SW+'\n')
    L=fn.split('\n')
    for k,l in enumerate(L):
        if l.startswith('  %_386.sroa.0.3 = phi i64 '): L[k]=l.replace('phi i64 ','phi i64 [ 2, %bb32 ], ')
        elif l.startswith('  %_386.sroa.19.3 = phi i64 '): L[k]=l.replace('phi i64 ','phi i64 [ 0, %bb32 ], ')
        elif l.startswith('  %_90.sroa.0.0 = phi i64 [ 0, %bb32 ], '): L[k]=l.replace('[ 0, %bb32 ], ','')
    return '\n'.join(L)
