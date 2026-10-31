# usage: calls.py TOOLS_HARNESS so [symregex]   (default swap_hop$)  or  calls.py TOOLS_HARNESS orig
import sys,re,subprocess
H=sys.argv[1]; sys.path.insert(0,H); args=sys.argv[2:]; sys.argv=sys.argv[:1]
import win, coords, score
from pathlib import Path
if args[0]=='orig':
    W={x['start']:x for x in coords.original_windows()}
    st=0x5b3b0; n=W[st]['bytes']; path=coords.BASE/'original.so'
    d=win.objdump_text(path,st,st+n)
    def lines(t): return [s['line'] for s in coords.orig_sites(t)] if t in W else '?'
    def name(t): return ''
else:
    path=Path(args[0]); rx=re.compile(args[1] if len(args)>1 else r'8swap_hop17h')
    fns=score.candidate_functions(path)
    st,n,_=next(f for f in fns if rx.search(f[2]))
    d=win.objdump_text(path,st,st+n)
    blob=path.read_bytes(); cs=coords.sections(blob)
    F={s:(n2,nm) for s,n2,nm in fns}
    def lines(t): return [s['line'] for s in coords.cand_sites(blob,cs,t,F[t][0])] if t in F else '?'
    def name(t): return re.sub(r'17h[0-9a-f]{16}E$','',F[t][1])[-40:] if t in F else '?'
for a in sorted(d):
    m=re.match(r'call (-?0x[0-9a-f]+)$',d[a])
    if not m: continue
    i=int(m.group(1),16)
    if i==-1: print(hex(a-st),'syscall'); continue
    t=a+8+i*8
    print(hex(a-st),hex(t),name(t),lines(t))
