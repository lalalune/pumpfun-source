import sys,re,hashlib; sys.path.insert(0,__file__.rsplit('/',1)[0])
import census as C
from pathlib import Path
def get(so,pat):
    p=Path(so); b=p.read_bytes(); s=C.sections(b)
    for a,sz,n in C.candidate_functions(p):
        if re.search(pat,n) and 'closure' not in n: return a,sz,hashlib.sha1(C.normalize(C.body(b,s,a,sz),a,s)).hexdigest()[:12],n[:70]
for pat in sys.argv[3:]:
    print(get(sys.argv[1],pat),'\n  ',get(sys.argv[2],pat))
