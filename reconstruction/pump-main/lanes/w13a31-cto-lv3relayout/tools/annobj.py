#!/usr/bin/env python3
"""annobj.py <m.o> : admin_cto::execute listing from an llc object, 'off text ; label' like annot.py (labels from call relocs)."""
import sys,re,subprocess,os
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
o=sys.argv[1]
h=subprocess.run([SDK+'/llvm-objdump','-h',o],capture_output=True,text=True).stdout
sec=re.search(r'\.text\.\S*admin_cto7execute\S*',h).group(0)
d=subprocess.run([SDK+'/llvm-objdump','-dr','--no-show-raw-insn','--section='+sec,o],capture_output=True,text=True).stdout
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a31-cto-lv3relayout/reconstruction/harness'); from win import demangle as dm
def short(n):
    n=re.sub(r'::h[0-9a-f]{16}$','',n)
    for _ in range(4): n=re.sub(r'<[^<>]*>','',n)
    n=re.sub(r'\$LT\$.*?\$GT\$','',n)
    return '::'.join(n.split('::')[-2:])
rows=[];cache={}
for l in d.split('\n'):
    m=re.search(r'R_\w+\s+(\S+)',l)
    if m and rows:
        s=m.group(1)
        if s not in cache: cache[s]=short(dm(s))
        rows[-1][2]='' if re.match(r'^(sol_|abort)',s) else cache[s]; continue
    m=re.match(r'^\s*([0-9a-f]+):\s+(.*)$',l)
    if m: rows.append([int(m.group(1))*8,m.group(2).strip(),'']); continue
    if False:
        s=m.group(1)
        if s not in cache: cache[s]=short(dm(s))
        rows[-1][2]=cache[s]
for a,t,lab in rows:
    print(f'{a:05x} {t}'+(f' ; {lab}' if lab and t.startswith('call') else ''))
