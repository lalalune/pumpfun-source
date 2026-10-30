import sys
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a37-cto-skelregress/reconstruction/harness')
import win
from score import original_windows
w=next(w for w in original_windows() if w['start']==0x22a10)
if sys.argv[1]=='orig':
    t=win.objdump_text(win.resolve_original(win.BASE/'original.so'),w['start'],w['start']+w['bytes']); base=w['start']
else:
    c=win.Cand(sys.argv[1]); s,n,nm=next((s,n,nm) for s,n,nm in c.funcs if win.demangle(nm).endswith('admin_cto::execute')); t=c.disassembly(s,n); base=s
for a in sorted(t): print(f'{a-base:#06x} {t[a]}')
