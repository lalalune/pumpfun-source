import re
X='_ZN14pump_recovered18protocol_fee_split17hf6474d0ddc81b131E'
def edit(f):
    f=f.replace('  br i1 %2, label %bb6, label %bb4\n','  br label %bb6\n',1)
    f=re.sub(r'\nbb4:[^\n]*\n  call void @llvm.lifetime.start.p0\(i64 0, ptr nonnull %_11.i.i29\)\n  br label %'+X+r'.exit\n','\n',f)
    f=f.replace('[ 0, %bb4 ], ','')
    f=f.replace('[ true, %'+X+'.exit28 ]','[ %2, %'+X+'.exit28 ]')
    return f
