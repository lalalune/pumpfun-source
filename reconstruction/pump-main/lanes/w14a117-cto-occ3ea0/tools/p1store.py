import re,sys
t=open('rx/main/m.ll').read()
anchor='  %596 = getelementptr inbounds i8, ptr %_270, i64 104\n'
lines=['  %669 = getelementptr inbounds i8, ptr %_120, i64 24\n','  store ptr %_2.i, ptr %669, align 8\n',
'  %_121.sroa.4.0..sroa_idx = getelementptr inbounds i8, ptr %_120, i64 32\n','  store ptr %_12.i153, ptr %_121.sroa.4.0..sroa_idx, align 8\n',
'  %_121.sroa.5.0..sroa_idx = getelementptr inbounds i8, ptr %_120, i64 40\n','  store ptr %_16.i, ptr %_121.sroa.5.0..sroa_idx, align 8\n',
'  %_121.sroa.6.0..sroa_idx = getelementptr inbounds i8, ptr %_120, i64 48\n','  store ptr %_5.i160, ptr %_121.sroa.6.0..sroa_idx, align 8\n',
'  %_121.sroa.7.0..sroa_idx = getelementptr inbounds i8, ptr %_120, i64 56\n','  store i64 %_6.i, ptr %_121.sroa.7.0..sroa_idx, align 8\n',
'  %_121.sroa.8.0..sroa_idx = getelementptr inbounds i8, ptr %_120, i64 64\n','  store i8 %591, ptr %_121.sroa.8.0..sroa_idx, align 8\n',
'  %_121.sroa.9.0..sroa_idx = getelementptr inbounds i8, ptr %_120, i64 65\n','  store i8 %593, ptr %_121.sroa.9.0..sroa_idx, align 1\n',
'  %_121.sroa.10.0..sroa_idx = getelementptr inbounds i8, ptr %_120, i64 66\n','  store i8 %595, ptr %_121.sroa.10.0..sroa_idx, align 2\n']
sel=sys.argv[1]  # which pairs to move: e.g. "01" key+lamports
mv=[]
for k in sel:
    i=int(k); mv+=lines[2*i:2*i+2]
for l in mv:
    assert t.count(l)==1,l; t=t.replace(l,'')
assert t.count(anchor)==1
t=t.replace(anchor,''.join(mv)+anchor)
open(sys.argv[2],'w').write(t)
