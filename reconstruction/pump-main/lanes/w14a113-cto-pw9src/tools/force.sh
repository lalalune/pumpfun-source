#!/bin/bash
# force.sh <m.ll> <force-spec|-> : private llc with RAPRIO_FORCE, prints wr.py + regmap r9->r8
O=~/.cache/pumpfun-reconstruction/lanes/w14a113-cto-pw9src; cd $O; m=$1; f=$2; t=$(mktemp $O/pl/fXXXX)
A=(-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections)
if [ "$f" = "-" ]; then pl/llc "${A[@]}" $m -filetype=obj -o $t.o; else RAPRIO_FORCE="$f" pl/llc "${A[@]}" $m -filetype=obj -o $t.o; fi
python3 -c "
src=open('tools/rx.py').read();g={'__name__':'x'};exec(src.split('OUT=os.environ')[0],g);open('$t.bin','wb').write(g['elf_fn']('$t.o',g['KEEP']))"
bash tools/dis.sh $t.o > $t.dis
echo "[$f] $(python3 tools/wr.py $t.bin | cut -c$((${#t}+17))-110) $(python3 tools/regmap.py $t.dis | head -1 | grep -o 'r9->r8:[0-9]*') L=$(python3 tools93/regceil.py $t.bin | grep -o '\[.*\]')"
rm -f $t $t.o $t.bin $t.dis
