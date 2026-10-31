# mkord.py <base_edits.py|-> <comma order of sharing fields> <out.py>: reorder the AdminCtoSharingConfig literal fields (on top of base edits)
import sys,re
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a30-cto-shareauthport'
s=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
E=[]
if sys.argv[1]!='-':
    g={};exec(open(sys.argv[1]).read(),g);E=list(g['EDITS'])
    for a,b in E: s=s.replace(a,b)
tag='crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{'
i=s.index(tag)+len(tag); d=1; j=i; parts=[]; st=i
while d:
    c=s[j]
    if c in '{([': d+=1
    elif c in '})]': d-=1
    if (c==',' and d==1) or d==0: parts.append(s[st:j]); st=j+1
    j+=1
body=s[i:j-1]
F={p.split(':',1)[0]:p for p in parts}
new=','.join(F[k] for k in sys.argv[2].split(','))
assert sorted(F)==sorted(sys.argv[2].split(',')),(sorted(F))
# express as edit on the original file: apply base edits first then this replacement
E.append((body,new))
open(sys.argv[3],'w').write('EDITS=%r\n'%E)
