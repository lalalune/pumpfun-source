#!/usr/bin/env python3
"""chunk.py <m.o|so>...: per-0x200 orig chunk rm/fm matched counts over 0x0-0x1800 plus totals, and abs ratios."""
import sys,os,difflib,json
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from abs import n1,n2
o=orig_dis(); W=0x200; NC=12
for p in sys.argv[1:]:
    c=cand_dis(p); out={'name':p.split('/')[-2],'bytes':sum(16 if t.startswith('lddw') else 8 for _,t in c)}
    for nm,f in (('rm',n2),('fm',n1)):
        sm=difflib.SequenceMatcher(None,[f(t) for _,t in o],[f(t) for _,t in c],autojunk=False)
        cnt=[0]*(o[-1][0]//W+1)
        for a,b,n in sm.get_matching_blocks():
            for k in range(n): cnt[o[a+k][0]//W]+=1
        out[nm]=round(sm.ratio(),5); out[nm+'V']=sum(cnt[:NC]); out[nm+'T']=sum(cnt); out[nm+'C']=cnt[:NC]
    # local validate-region skeleton: orig [0,0x1a88) vs cand [0, call before first 'jeq r7, 0x2')
    out['calls']=sum(1 for _,t in c if t.startswith('call'))
    oe=[t for a,t in o if a<0x1a88]
    import re
    k=next((i for i,(a,t) in enumerate(c) if re.match(r'j(eq|ne) r\d, 0x2, ',t)),len(c)-1)+1
    ce=[t for a,t in c[:k-2]]
    for nm,f in (('Lrm',n2),('Lfm',n1)):
        sm=difflib.SequenceMatcher(None,[f(t) for t in oe],[f(t) for t in ce],autojunk=False)
        out[nm]=sum(n for _,_,n in sm.get_matching_blocks())
    out['Ln']=(len(oe),len(ce))
    print(json.dumps(out))
