import sys,re
t=open(sys.argv[1]).read()
i=t.index('\nbb76:'); j=t.index('\n\n',i)
blk=t[i+1:j]
lines=blk.split('\n')
body=[l for l in lines[1:] if ' = phi ' not in l]
s='\n'.join(['bb76s:                                             ; preds = %bb58.i']+body)
s=s.replace('%target.i.sroa.7.0','%target.i.sroa.7.1').replace('%target.i.sroa.8.0','%target.i.sroa.8.1')
s=s.replace('label %bb19, label %bb22','label %bb19, label %bb22')
# remove bb58.i entries from bb76 phis
nb=blk.replace(', [ %target.i.sroa.7.1, %bb58.i ]','').replace(', [ %target.i.sroa.8.1, %bb58.i ]','').replace('preds = %bb58.i, %bb44.i, %bb45.i','preds = %bb44.i, %bb45.i')
t=t[:i+1]+nb+'\n\n'+s+t[j:]
# bb58.i branch -> bb76s
k=t.index('\nbb58.i:'); e=t.index('\n\n',k)
b58=t[k:e]; b58n=b58.replace('label %bb76','label %bb76s'); assert b58n!=b58
t=t[:k]+b58n+t[e:]
# phis in bb19/bb22
for b in ('bb19','bb22'):
    k=t.index('\n%s:'%b); e=t.index('\n',k+1)
    ph='\n  %%t7.%s = phi i64 [ %%target.i.sroa.7.0, %%bb76 ], [ %%target.i.sroa.7.1, %%bb76s ]\n  %%t8.%s = phi ptr [ %%target.i.sroa.8.0, %%bb76 ], [ %%target.i.sroa.8.1, %%bb76s ]'%(b,b)
    t=t[:e]+ph+t[e:]
# bb26 phis
k=t.index('\nbb26:'); e=t.index('\n\n',k); b26=t[k:e]
b26=b26.replace('[ %target.i.sroa.8.0, %bb22 ]','[ %t8.bb22, %bb22 ]').replace('[ %target.i.sroa.8.0, %bb23 ]','[ %t8.bb22, %bb23 ]').replace('[ %target.i.sroa.8.0, %bb19 ]','[ %t8.bb19, %bb19 ]')
b26=b26.replace('[ %target.i.sroa.7.0, %bb22 ]','[ %t7.bb22, %bb22 ]').replace('[ %target.i.sroa.7.0, %bb23 ]','[ %t7.bb22, %bb23 ]').replace('[ %target.i.sroa.7.0, %bb19 ]','[ %t7.bb19, %bb19 ]')
t=t[:k]+b26+t[e:]
open(sys.argv[2],'w').write(t)
