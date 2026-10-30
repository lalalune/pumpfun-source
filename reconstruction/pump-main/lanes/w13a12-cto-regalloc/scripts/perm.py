import sys,itertools,difflib
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import ctoracle as co
otok,w=co.orig_tokens()
ctok,n=co.so_tokens(sys.argv[1])
def remap(tok,p):
    b=bytearray(tok); d=b[1]&15; s=b[1]>>4
    d=p.get(d,d); s=p.get(s,s); b[1]=(s<<4)|d; return bytes(b)
base=co.metrics(otok,ctok,n,27400)
print('base',base)
best=[]
for perm in itertools.permutations([6,7,8,9]):
    p=dict(zip([6,7,8,9],perm))
    m=co.metrics(otok,[remap(t,p) for t in ctok],n,27400)
    best.append((m['ratio'],perm))
best.sort(reverse=True); print(best[:6])
