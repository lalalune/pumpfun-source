import re,sys
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness')
from score import sections
def ro(p):
    b=open(p,'rb').read(); s=sections(b)['.rodata']; return b[s['offset']:s['offset']+s['size']]
O=ro('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/base/original.so'); C=ro(sys.argv[1])
f=lambda X: [(m.start(),m.group().decode()) for m in re.finditer(rb'programs/pump/src/[a-z_/0-9]+\.rs',X)]
o=f(O); c=f(C)
bad=[(hex(a),x[18:],hex(b),y[18:]) for (a,x),(b,y) in zip(o,c) if x!=y or a!=b]
print('paths',len(o),len(c),'set-equal',sorted(x for _,x in o)==sorted(y for _,y in c),'order/offset mismatches',len(bad))
for r in bad[:int(sys.argv[2]) if len(sys.argv)>2 else 8]: print('  ',*r)
import difflib
sm=difflib.SequenceMatcher(None,O,C,autojunk=False); print('rodata aligned bytes',sum(t[2]-t[1] for t in sm.get_opcodes() if t[0]=='equal'))
