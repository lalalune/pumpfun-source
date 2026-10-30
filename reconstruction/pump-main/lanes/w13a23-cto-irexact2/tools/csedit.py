# csedit: EDITS for rx.py from env CS_FN (regex of the define), CS_K (k-th call to a defined non-intrinsic fn), CS_ATTR (noinline|alwaysinline)
import os,re
FN=os.environ['CS_FN']; K=int(os.environ['CS_K']); A=os.environ['CS_ATTR']
def ed(t):
    defs=set(m.group(1) for m in re.finditer(r'\ndefine [^\n]*?@("[^"]+"|[\w.$]+)\(',t))
    m=re.search(r'\ndefine [^\n]*@"?[^\n(]*'+FN+r'[^\n(]*"?\(',t); s=m.start()+1; e=t.index('\n}\n',s)
    L=t[s:e].split('\n'); k=-1
    for i,l in enumerate(L):
        mm=re.search(r'(?:call|invoke) [^@\n]*@("[^"]+"|[\w.$]+)\(',l)
        if mm and mm.group(1) in defs and not mm.group(1).startswith('llvm.'):
            k+=1
            if k==K:
                if l.lstrip().startswith('invoke'):
                    L[i]=re.sub(r'\)( #\d+)?(\s+to label)',r') #9990\2',l,count=1)
                else:
                    L[i]=re.sub(r'\)( #\d+)?((, !.*)?)$',r') #9990\2',l)
                assert L[i]!=l,l[:200]
                break
    else: raise SystemExit('no call')
    return t[:s]+'\n'.join(L)+t[e:]+'\nattributes #9990 = { %s }\n'%A
EDITS=[ed]
