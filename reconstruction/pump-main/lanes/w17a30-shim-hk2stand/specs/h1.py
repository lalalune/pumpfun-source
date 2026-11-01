import re
SKS=r'call void @llvm.lifetime.start.p0\(i64 32, ptr nonnull %skm\)$'
EOK=r'call void @llvm.lifetime.end.p0\(i64 32, ptr nonnull %skm\)'
X=[('S',SKS,0,'>'),('V',SKS,0,'>'),('E',EOK,0,'>'),('E',EOK,1,'>')]
AL=(r'^\s+%skm = alloca','<',32,8)
C1='bb14.i bb7.i bb10.i bb3.i30.i TS.exit31.i bb23.i bb30.i bb3.i37.i TS.exit38.i bb31.i bb16.i bb22.i bb17.i bb3.i23.i TS.exit24.i'
S0=r'^  call void @llvm.lifetime.start.p0\(i64 7, ptr nonnull %target.i.sroa.0\)$'
S9=r'^  call void @llvm.lifetime.start.p0\(i64 9, ptr nonnull %target.i.sroa.9\)$'
W0=r'dereferenceable\(7\) %target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable\(7\) %_59.sroa.5.0.new.sroa_idx'
E0='  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %target.i.sroa.0)'
E9='  call void @llvm.lifetime.end.p0(i64 9, ptr nonnull %target.i.sroa.9)'
ST0='  call void @llvm.lifetime.start.p0(i64 7, ptr nonnull %target.i.sroa.0)'
ST9='  call void @llvm.lifetime.start.p0(i64 9, ptr nonnull %target.i.sroa.9)'
SPECS=[]
for o,ow in [('C1',{'order':C1,'w':'bb14.i:51:49'}),('main',{})]:
    SPECS.append((f'h_del09_{o}',dict(alloc=AL,ops=X+[('D',S0,0),('D',S9,0)],**ow)))
    # explicit END at the non-holder arm head (after its STARTs) + START before the bb52.i writes
    SPECS.append((f'h_es_{o}',dict(alloc=AL,ops=X+[('RAW',S9,0,'>',E9),('RAW',S9,0,'>',E0),('RAW',W0,0,'<',ST0),('RAW',W0,0,'<',ST9)],**ow)))
    SPECS.append((f'h_es_noX_{o}',dict(ops=[('RAW',S9,0,'>',E9),('RAW',S9,0,'>',E0),('RAW',W0,0,'<',ST0),('RAW',W0,0,'<',ST9)],**ow)))
