# extract.py module.ll out.ll SYM : keep only SYM's body; other functions become declarations
import sys,re
src,dst,sym=sys.argv[1:4]
L=open(src).read().split('\n'); out=[]; i=0
while i<len(L):
    l=L[i]
    if l.startswith('define '):
        k=i
        while not L[k].rstrip().endswith('{'): k+=1
        j=k
        while L[j]!='}': j+=1
        if sym in l: out+=L[i:j+1]
        else:
            h=' '.join(x.strip() for x in L[i:k+1]).rstrip(' {')
            h=re.sub(r'^define\s+((internal|private|linkonce_odr|weak_odr|hidden|dso_local|unnamed_addr|local_unnamed_addr)\s+)*','declare ',h)
            q=h.rfind(')'); t=h[q+1:]
            t=re.sub(r'\s+(personality|section|comdat|align|prefix)\b.*$','',t)
            h=h[:q+1]+t
            out.append(h)
        i=j+1; continue
    if not re.match(r'^@\S+ = .*\balias\b',l): out.append(l)
    i+=1
open(dst,'w').write('\n'.join(out))
