#!/bin/bash
# zaprobe.sh: compile zaprobe.rs with the identity rustc for sbpf-solana-solana at -O3 and print each probe's asm (~1 s, no slot)
R=~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/bin/rustc
D=$(mktemp -d); cp "$(dirname "$0")/zaprobe.rs" $D/a.rs; cd $D
$R --target sbpf-solana-solana --crate-type=lib -C opt-level=3 --emit=llvm-ir,asm -o a a.rs 2>&1 | head -20
python3 - <<'PY'
import re
s=open('a.s').read(); cur=None; out={}
for line in s.splitlines():
    m=re.match(r'^(\w+):',line)
    if m and not m.group(1).startswith('LBB'): cur=m.group(1); out[cur]=[]; continue
    if m: out[cur].append(m.group(1)+':'); continue
    if cur and re.match(r'^\s',line) and line.strip() and not line.strip().startswith(('.','#')): out[cur].append(line.strip())
for f,v in out.items():
    if not f.startswith('LBB'): print(f,' ; '.join(v))
PY
rm -rf $D
