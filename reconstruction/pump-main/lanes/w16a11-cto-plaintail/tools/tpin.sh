#!/bin/bash
# tpin.sh <name> <m.ll> : pre-coalescer physreg pins at the sweep-exit join bb88 (w15a06 swr9 method; ORACLE ONLY):
#   sw = swept (the bb88 COPY that feeds the event +184 store) -> r9 ; tag = sharing tag (COPY feeding AND_ri 255) -> r6
# prints M / ratio for rt (round trip), sw, tag, both, and regideal rewrite counts over orig 0x3c00-0x5040
O=~/.cache/pumpfun-reconstruction/lanes/w16a11-cto-plaintail; cd $O; N=$1; I=$2; D=g/$N/pin; mkdir -p $D
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin; A=(-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections)
$SDK/llc "${A[@]}" $I -stop-before=register-coalescer -o $D/pre.mir || exit 1
read J SW TG < <(python3 - $D/pre.mir <<'PY'
import sys,re
L=open(sys.argv[1]).read().split('\n')
j=next(i for i,l in enumerate(L) if re.match(r'^  bb\.\d+\.bb88:',l)); J=re.match(r'^  bb\.(\d+)',L[j]).group(1)
sw=tg=None
for i in range(j+1,j+80):
    if L[i].startswith('  bb.'): break
    m=re.match(r'^\s+(%\d+):gpr = COPY killed (%\d+)',L[i])
    if m and sw is None: sw=m.group(1)
    m=re.match(r'^\s+(%\d+):gpr = COPY (%\d+)\s*$',L[i])
    if m and re.match(r'^\s+'+m.group(1)+r':gpr = AND_ri '+m.group(1)+', 255',L[i+1]): tg=m.group(2)
print(J,sw,tg)
PY
)
echo "J=bb.$J swept=$SW tag=$TG"
run(){ # $1 tag, $2 input mir
  $SDK/llc "${A[@]}" $2 -start-before=register-coalescer -filetype=obj -o $D/$1.o 2>$D/$1.err || { echo "$1 FAIL $(tail -2 $D/$1.err)"; return; }
  s=$(python3 t6/objsc.py $D/$1.o | awk '{print $3, $5, $7}')
  n=$(python3 t85/tools/regideal.py $D/$1.bin $D/$1.ri.bin 0x3c00 0x5040 | awk '{print $2}')
  n9=$(RF=9 python3 t85/tools/regideal.py $D/$1.bin $D/$1.ri9.bin 0x3c00 0x5040 | awk '{print $2}')
  ra=$(python3 t6/objsc.py $D/$1.ri.bin | awk '{print $5}')
  echo "{\"name\":\"$N\",\"cell\":\"$1\",\"ratio_M_bytes\":\"$s\",\"ri_rewrites\":$n,\"ri9_rewrites\":$n9,\"ria_M\":$ra}"
}
run rt $D/pre.mir
python3 t6/swr9.py $D/pre.mir $D/sw.mir $SW $J r9 2>$D/sw.log && run sw $D/sw.mir
python3 t6/swr9.py $D/pre.mir $D/tag.mir $TG $J r6 2>$D/tag.log && run tag $D/tag.mir || cat $D/tag.log
python3 t6/swr9.py $D/sw.mir $D/both.mir $TG $J r6 2>$D/both.log && run both $D/both.mir || cat $D/both.log
