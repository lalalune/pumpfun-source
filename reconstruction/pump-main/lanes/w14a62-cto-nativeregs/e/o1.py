a='  %554 = call i64 @llvm.usub.sat.i64(i64 %_121.i, i64 %min.i)\n'
b='  %_124.not.not.i = icmp ugt i64 %_121.i, %min.i\n'
c='  %_122.i = getelementptr inbounds i8, ptr %_268, i64 216\n'
import os
M=os.environ.get('M','1')
def f(t):
    if M=='1': return t.replace(a+b,b+a)
    if M=='2': # sub(non-sat) + select
        return t.replace(a+b,b+'  %s554 = sub i64 %_121.i, %min.i\n  %554 = select i1 %_124.not.not.i, i64 %s554, i64 0\n')
    if M=='3': return t.replace(a+b,'  %s554 = sub i64 %_121.i, %min.i\n'+b+'  %554 = select i1 %_124.not.not.i, i64 %s554, i64 0\n')
    if M=='4': # select on ult
        return t.replace(a+b,b+'  %s554 = sub nuw i64 %_121.i, %min.i\n  %554 = select i1 %_124.not.not.i, i64 %s554, i64 0\n')
    if M=='5': # gep before minimum_balance
        t=t.replace(c,''); k='  %min.i = call noundef i64 @_ZN11solana_rent4Rent15minimum_balance'; return t.replace(k,c+k)
EDITS=[f]
