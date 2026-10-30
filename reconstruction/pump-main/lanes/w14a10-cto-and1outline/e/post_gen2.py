import sys,os
G={}
G['a1']=[('%43 = and i8 %holder, -3\n  %_0.sroa.0.0.off0.i56 = icmp ne i8 %43, 0','%43 = and i8 %holder, 1\n  %_0.sroa.0.0.off0.i56 = icmp ne i8 %43, 0')]
G['t306']=[('%trunc.not.not.i = icmp eq i8 %_39.sroa.0.0.copyload, 0','%tg306 = and i8 %_39.sroa.0.0.copyload, 1\n  %trunc.not.not.i = icmp eq i8 %tg306, 0')]
G['t298']=[('%trunc9.not.not.i = icmp eq i8 %_39.sroa.0.0.copyload, 0','%tg298 = and i8 %_39.sroa.0.0.copyload, 1\n  %trunc9.not.not.i = icmp eq i8 %tg298, 0')]
EDITS=[]
for n in os.environ['GENES'].split('_'): EDITS+=G[n]
