import re,os
K=os.environ['SEM']
def edit(f):
    if K=='hicheck1':
        f=f.replace('  %_15.i17 = icmp ugt i128 %1, 184467440737095516159999','  %hi1 = lshr i128 %1, 64\n  %hi1t = trunc i128 %hi1 to i64\n  %_15.i17 = icmp ugt i64 %hi1t, 9999')
    elif K=='hicheck2':
        f=f.replace('  %_15.i = icmp ugt i128 %4, 184467440737095516159999','  %hi2 = lshr i128 %4, 64\n  %hi2t = trunc i128 %hi2 to i64\n  %_15.i = icmp ugt i64 %hi2t, 9999')
    elif K=='hicheckboth':
        os.environ['SEM']='hicheck1'; f=edit(f); os.environ['SEM']='hicheck2'; f=edit(f); os.environ['SEM']=K
    elif K=='orsplit':
        f=f.replace('  %or.cond = or i1 %_74.1, %_77.not\n  br i1 %or.cond, label %bb29, label %bb27','  br i1 %_74.1, label %bb29, label %orb\n\norb:\n  br i1 %_77.not, label %bb29, label %bb27')
    elif K=='orsplit2':
        f=f.replace('  %or.cond = or i1 %_74.1, %_77.not\n  br i1 %or.cond, label %bb29, label %bb27','  br i1 %_77.not, label %bb29, label %orb\n\norb:\n  br i1 %_74.1, label %bb29, label %bb27')
    elif K=='orswap':
        f=f.replace('%or.cond = or i1 %_74.1, %_77.not','%or.cond = or i1 %_77.not, %_74.1')
    elif K.startswith('noov'):
        # replace uadd.with.overflow with add + icmp ult
        n=K[4:]  # '6' or '33'
        a,b=('_54','%_0.sroa.0.0.i2543') if n=='6' else ('_74','%_62')
        m=re.search(r'  %'+n+r' = tail call \{ i64, i1 \} @llvm.uadd.with.overflow.i64\(i64 (\S+), i64 (\S+)\)\n  %'+a+r'.0 = extractvalue \{ i64, i1 \} %'+n+r', 0\n  %'+a+r'.1 = extractvalue \{ i64, i1 \} %'+n+r', 1\n',f)
        x,y=m.group(1),m.group(2)
        f=f[:m.start()]+'  %%%s.0 = add i64 %s, %s\n  %%%s.1 = icmp ult i64 %%%s.0, %s\n'%(a,x,y,a,a,x)+f[m.end():]
    elif K=='usub77':
        f=f.replace('  %_77.not = icmp ult i64 %_74.0, %_54.0','  %us = tail call { i64, i1 } @llvm.usub.with.overflow.i64(i64 %_74.0, i64 %_54.0)\n  %_77.not = extractvalue { i64, i1 } %us, 1')
        f=f.replace('  %_78 = sub nuw i64 %_74.0, %_54.0','  %_78 = extractvalue { i64, i1 } %us, 0')
    elif K=='usub91':
        f=f.replace('  %_91.not = icmp ult i64 %_85, %_78','  %us9 = tail call { i64, i1 } @llvm.usub.with.overflow.i64(i64 %_85, i64 %_78)\n  %_91.not = extractvalue { i64, i1 } %us9, 1')
        f=f.replace('  %_92 = sub nuw i64 %_85, %_78','  %_92 = extractvalue { i64, i1 } %us9, 0')
    elif K=='div1sh':
        f=f.replace('  %_16.i20 = trunc i128 %scaled.i19 to i64','  %_16.i20 = trunc i128 %scaled.i19 to i64')
    return f
