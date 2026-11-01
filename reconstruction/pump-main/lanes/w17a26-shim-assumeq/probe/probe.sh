#!/bin/bash
# zfprobe.sh: compile $1 (a probe file (assumeprobe.rs: llvm.assume equality/range facts; ppprobe.rs: llvm.pseudoprobe/llvm.sideeffect)) with the identity rustc for
# sbpf-solana-solana at opt-level 3 and print each probe function's asm. No build slot; about 1 s.
# Note: llvm.ssa.copy crashes IPSCCP (SIGSEGV in SCCPInstVisitor::handleCallResult), so it is not in the probe.
R=~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/bin/rustc
D=$(mktemp -d); cp "$1" $D/a.rs; cd $D
$R --target sbpf-solana-solana --crate-type=lib -C opt-level=3 --emit=llvm-ir,asm -o a a.rs 2>/dev/null
python3 - <<'PY'
import re
s=open('a.s').read(); cur=None; out={}
for line in s.splitlines():
    m=re.match(r'^(\w+):',line)
    if m: cur=m.group(1); out[cur]=[]; continue
    if cur and re.match(r'^\s',line) and line.strip() and not line.strip().startswith(('.','#')): out[cur].append(line.strip())
for f,v in out.items():
    if not f.startswith('LBB'): print(f,' ; '.join(v))
PY
rm -rf $D
