# mv.py a.bin b.bin: difflib opcodes between two fn windows (offset-stripped text, jumps masked)
import sys,os,re,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bdis import decode
def T(f):
    L=decode(open(f,'rb').read()); return [re.sub(r'[+-]\d+$','J',d['txt']) if d['txt'].startswith('j') else d['txt'] for d in L],L
a,A=T(sys.argv[1]); b,B=T(sys.argv[2])
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op!='equal' and (i2-i1>3 or j2-j1>3): print(op,'a[%d:%d] %04x-%04x'%(i1,i2,A[i1]['off'] if i1<len(A) else 0,A[i2-1]['off'] if i2>i1 else 0),'b[%d:%d] %04x-%04x'%(j1,j2,B[j1]['off'] if j1<len(B) else 0,B[j2-1]['off'] if j2>j1 else 0))
    elif op!='equal': print(' ',op,i1,i2,j1,j2)
