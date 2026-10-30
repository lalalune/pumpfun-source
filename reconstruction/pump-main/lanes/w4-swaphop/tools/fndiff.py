import sys; sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness'); A=sys.argv[1:]; sys.argv=sys.argv[:1]
import score
from pathlib import Path
a=score.candidate_functions(Path(A[0])); b=score.candidate_functions(Path(A[1]))
na=[n for s,l,n in sorted(a)]; nb=[n for s,l,n in sorted(b)]
print(len(na),len(nb), 'only-a',[n[:80] for n in set(na)-set(nb)][:6],'only-b',[n[:80] for n in set(nb)-set(na)][:6])
import difflib
sm=difflib.SequenceMatcher(None,na,nb,autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op!='equal': print(op,na[i1:i2][:3],nb[j1:j2][:3])
