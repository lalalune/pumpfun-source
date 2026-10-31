import sys,re,difflib
def load(f,lo,hi):
    out=[]
    for l in open(f):
        a,t=l.strip().split(' ',1)
        if lo<=int(a,16)<hi: out.append((a,t))
    return out
def sk(t): return re.sub(r'r\d','r',re.sub(r'[-+]0x[0-9a-f]+','#',t))
A=load(sys.argv[1],int(sys.argv[3],16),int(sys.argv[4],16)); B=load(sys.argv[2],int(sys.argv[5],16),int(sys.argv[6],16))
sm=difflib.SequenceMatcher(None,[sk(t) for _,t in A],[sk(t) for _,t in B],autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': continue
    print(op, '|', '; '.join(f'{a} {t}' for a,t in A[i1:i2]),' ==> ', '; '.join(f'{a} {t}' for a,t in B[j1:j2]))
