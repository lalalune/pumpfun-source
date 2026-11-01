# IR oracle: branch weights on one br (emulates core::intrinsics::likely/unlikely); env BW_BR='<exact br line w/o newline>' BW='a,b'
import os,re
BR=os.environ['BW_BR']; A,B=os.environ['BW'].split(',')
def f(t):
    assert t.count(BR+'\n')==1,(BR,t.count(BR+'\n'))
    t=t.replace(BR+'\n',BR+', !prof !987654\n')
    return t.rstrip('\n')+'\n!987654 = !{!"branch_weights", i32 %s, i32 %s}\n'%(A,B)
EDITS=[f]
