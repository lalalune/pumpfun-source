import sys,os,difflib
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','tools12'))
import mmask
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read(); mn=int(sys.argv[3]) if len(sys.argv)>3 else 3
ta=mmask.toks(a,frame=True,regs=True,jumps=True); tb=mmask.toks(b,frame=True,regs=True,jumps=True)
def offs(raw):
    o=[];i=0
    while i<len(raw):
        o.append(i); i+=16 if raw[i]==0x18 else 8
    return o
oa=offs(a); ob=offs(b)
sm=difflib.SequenceMatcher(None,ta,tb,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    if max(i2-i1,j2-j1)<mn: continue
    print(tag, 'a[%#x..%#x) n=%d'%(oa[i1] if i1<len(oa) else len(a), oa[i2] if i2<len(oa) else len(a), i2-i1), 'b[%#x..%#x) n=%d'%(ob[j1] if j1<len(ob) else len(b), ob[j2] if j2<len(ob) else len(b), j2-j1))
