import sys,re,difflib
def rd(f): return [re.sub(r'^add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -A',re.sub(r'r10 - 0x[0-9a-f]+','r10-X',re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',re.sub(r'call -?0x[0-9a-f]+','call X',l.split(None,1)[1].strip())))) for l in open(f)]
def rdj(f): return [re.sub(r'^(j\w+ .*)[+-]0x[0-9a-f]+$',r'\1J',x) for x in rd(f)]
o=rdj(sys.argv[1]); c=rdj(sys.argv[2]); seg=int(sys.argv[3]) if len(sys.argv)>3 else 256
sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
m=[0]*len(o)
for t,i1,i2,j1,j2 in sm.get_opcodes():
    if t=='equal':
        for i in range(i1,i2): m[i]=1
print('abs ratio',round(sm.ratio(),4))
print(' '.join(f'{i*8:#x}:{sum(m[i:i+seg])*100//len(m[i:i+seg])}' for i in range(0,len(o),seg)))
