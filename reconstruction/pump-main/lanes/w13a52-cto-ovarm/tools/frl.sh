#!/bin/bash
# frl.sh <m.ll|m.o-dir name>: named frame layout of execute (offset size type name), sorted
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
$SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $1 -stop-after=prologepilog -o /tmp/frl$$.mir 2>/dev/null
python3 - /tmp/frl$$.mir <<'PY'
import re,sys
t=open(sys.argv[1]).read()
i=t.index('admin_cto7execute'); i=t.index('stack:',i); j=t.index('\ncallSites',i)
r=[]
for m in re.finditer(r"- \{ id: (\d+), name: '?([^,']*)'?, type: ([\w-]+), offset: (-?\d+), size: (\d+)",t[i:j]):
    r.append((int(m.group(4)),int(m.group(5)),m.group(3),m.group(2) or '#'+m.group(1)))
for x in sorted(r): print(*x)
PY
rm -f /tmp/frl$$.mir
