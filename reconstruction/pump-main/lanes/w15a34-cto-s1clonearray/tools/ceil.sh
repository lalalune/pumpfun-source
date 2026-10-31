#!/bin/bash
# ceil.sh <name> [procs]: sharing-arm family singles (top/bot/casc/w3/w03) + forward climb (M, 6 rounds) on rx/<name>/m.ll
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a34-cto-s1clonearray; N=$1; P=${2:-4}
L=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a18-cto-s1greedy/llvmb/bin/llc
cd $OUT; mkdir -p ceil
$L -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections rx/$N/m.ll -stop-before=greedy -o tmp/$N.pregreedy.mir 2>/dev/null
python3 tools/famvregs.py tmp/$N.pregreedy.mir > tmp/$N.fam 2>/dev/null
python3 - $N <<'PY'
import sys,json
n=sys.argv[1]; V=[int(x) for x in open(f'tmp/{n}.fam').read().split()]
with open(f'ceil/{n}.jobs','w') as f:
    for v in V:
        for nm,k,val in (('top','prio','0xfffffff0'),('bot','prio','1'),('casc','casc','0x7ffffff0'),('w3','weight','*3'),('w03','weight','*0.3')):
            f.write(json.dumps({'name':f'{nm}_{v}','v':v,k:f'{v}={val}'})+'\n')
PY
rm -f ceil/$N.singles; python3 tools/scr.py rx/$N/m.ll ceil/$N.jobs ceil/$N.singles $P
python3 tools/climb.py rx/$N/m.ll ceil/$N.singles ceil/$N.climb.log M 6 40 > ceil/$N.climb.out 2>&1
grep -E "^start|^step|FINAL" ceil/$N.climb.out | cut -c1-200
