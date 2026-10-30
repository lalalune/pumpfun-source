import sys,difflib,struct
sys.path.insert(0,'.'); import ctoracle as C
O,w=C.orig_tokens(); K,n=C.so_tokens(sys.argv[1])
def regmask(t):
    b=bytearray(C.abstract(t)); b[1]=0; return bytes(b)
off=[];p=0
for t in O: off.append(p); p+=len(t)
NB=16; cut=[27400*i//NB for i in range(NB+1)]
for name,f in (('plain',lambda t:t),('frame',C.abstract),('skel',regmask)):
    sm=difflib.SequenceMatcher(None,[f(t) for t in O],[f(t) for t in K],autojunk=False)
    M=[0]*NB; N=[0]*NB
    for x in range(len(O)): N[next(r for r in range(NB) if off[x]<cut[r+1])]+=1
    for a,_,k in sm.get_matching_blocks():
        for x in range(a,a+k): M[next(r for r in range(NB) if off[x]<cut[r+1])]+=1
    print(f'{name:6s} {sm.ratio():.4f} ', ' '.join(f'{M[r]/N[r]:.2f}' for r in range(NB)))
print('chunks orig:',' '.join(hex(c) for c in cut[:-1]))
