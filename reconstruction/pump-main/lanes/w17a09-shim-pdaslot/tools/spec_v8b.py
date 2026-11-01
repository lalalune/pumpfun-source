V={}
S0='  store i8 0, ptr %shared, align 1\n'
S1='  store i8 %33, ptr %shared, align 1\n'
LD='  %112 = load i8, ptr %shared, align 1, !range !4, !noundef !2\n'
vs=lambda s: s.replace('store i8','store volatile i8')
vl=lambda s: s.replace('load i8','load volatile i8')
V['vsS']=[(S0,vs(S0)),(S1,vs(S1))]
V['vsL']=[(LD,vl(LD))]
V['vsSL']=[(S0,vs(S0)),(S1,vs(S1)),(LD,vl(LD))]
V['vsS0']=[(S0,vs(S0))]
V['vsS1']=[(S1,vs(S1))]
