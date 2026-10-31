import sys,os,difflib,re
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
A=sys.argv; sys.argv=['x','n']
exec(open(D+'tools/rx.py').read().split('OUT=os.environ')[0])
O=mask(orig_window()); C=mask(open(A[1],'rb').read())
def offs(t):
    o=[0]
    for x in t: o.append(o[-1]+len(x))
    return o
oo=offs(O); co=offs(C)
OD={}
for l in open(D+'t/orig.win'):
    m=re.match(r'0x([0-9a-f]+)\s+(.*)',l)
    if m: OD[int(m.group(1),16)-0x22a10]=m.group(2)
CD={}
for l in open(A[2]):
    m=re.match(r'\s+(\d+):\s+(.*)',l)
    if m: CD[int(m.group(1))*8]=m.group(2).split('<')[0].strip()
lo,hi=int(A[3],16),int(A[4],16)
sm=difflib.SequenceMatcher(None,O,C,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if lo<=oo[i1]<hi and tag!='equal':
        print(tag,'O:',' ; '.join('%#x %s'%(oo[i],OD.get(oo[i])) for i in range(i1,i2)),' || C:',' ; '.join('%#x %s'%(co[j],CD.get(co[j])) for j in range(j1,j2)))
