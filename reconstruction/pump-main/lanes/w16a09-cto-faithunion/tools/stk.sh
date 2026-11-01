#!/bin/bash
# stk.sh <rxname> [FORCE] [TAG]: stacked bound on one raw-IR capture (experiment only).
#   (1) RA: optional RAPRIO_FORCE set (sticky patched llc), else the SDK llc;
#   (2) layout: llc -stop-after=block-placement, blkrestore.py re-sorts the execute blocks into main's layout, resume;
#   (3) frame: fnorm.py rebases allocas to main's frame objects, then spill-colour bestperm + swap climb.
# Prints one JSON line: M_plain, M_restored (layout), Mfn / Mfnperm / Mfnhc on the restored code, true LCS, head rfj.
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a09-cto-faithunion; cd $O; n=$1; F=${2:-}; TAG=${3:-${F:+ra}}
A="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
if [ -n "$F" ]; then LLC=$O/llvmb/bin/llc; export RAPRIO_STICKY=1 RAPRIO_FORCE=$F; else LLC=~/.cache/solana/v1.44/platform-tools/llvm/bin/llc; fi
D=$O/stk/${n}${TAG:+_$TAG}; mkdir -p $D
REF=$O/stk/ref; if [ ! -f $REF/bp.mir ]; then mkdir -p $REF; S=~/.cache/solana/v1.44/platform-tools/llvm/bin/llc
  $S $A $O/rx/m0/m.ll -stop-after=block-placement -o $REF/bp.mir; $S $A $O/rx/m0/m.ll -stop-after=prologepilog -o $REF/pei.mir; fi
$LLC $A rx/$n/m.ll -stop-after=block-placement -o $D/bp.mir || exit 1
$LLC $A rx/$n/m.ll -stop-after=prologepilog -o $D/pei.mir || exit 1
$LLC $A rx/$n/m.ll -filetype=obj -o $D/p.o || exit 1
python3 t2/blkrestore.py $D/bp.mir $REF/bp.mir $D/r.mir 2> $D/restore.txt
~/.cache/solana/v1.44/platform-tools/llvm/bin/llc $A $D/r.mir -start-after=block-placement -filetype=obj -o $D/r.o || exit 1
python3 - $D <<'PY'
import sys; sys.path.insert(0,'t2'); import oracle
d=sys.argv[1]
for a,b in (('p.o','plain.bin'),('r.o','restored.bin')): open(f'{d}/{b}','wb').write(oracle.elf_fn(f'{d}/{a}',oracle.KEEP))
PY
rm -f $D/p.o $D/r.o $D/bp.mir $D/r.mir
python3 t2/fnorm.py $D/restored.bin $D/pei.mir $REF/pei.mir --out $D/stacked.bin > $D/fnorm.json
python3 t2/fnorm.py $D/plain.bin $D/pei.mir $REF/pei.mir > $D/fnorm_plain.json
python3 tools/fuev.py $D/plain.bin $D/restored.bin $D/stacked.bin > $D/fuev.jsonl
python3 - $D "$n" "$F" <<'PY'
import sys,json; d,n,F=sys.argv[1:4]
fn=json.load(open(d+'/fnorm.json')); fp=json.load(open(d+'/fnorm_plain.json')); ev=[json.loads(l) for l in open(d+'/fuev.jsonl')]
r={'n':n,'force':F,'nforce':len([x for x in F.split(',') if x]),'bytes':fn['bytes'],'M_plain':fp['M'],'Mfn_plain':fp['Mfn'],'Mfnhc_plain':fp['Mfnhc'],'M_restored':fn['M'],'Mfn':fn['Mfn'],'Mfnperm':fn['Mfnperm'],'Mfnhc':fn['Mfnhc'],'stacked':max(fn['Mfnhc'],fp['Mfnhc']),
   'restore':open(d+'/restore.txt').read().strip(),'nextra':fn['nextra'],'extra':fn['extra'],
   'Lrfj_plain':ev[0]['Lrfj'],'Lrfj_restored':ev[1]['Lrfj'],'L---_stacked':ev[2]['L---'],'op_restored':ev[1]['lcs_op'],'head_rfj':ev[0]['head_rfj'],'swap_plain':ev[0]['swap'],'swap_restored':ev[1]['swap']}
print(json.dumps(r)); open(d+'/stk.json','w').write(json.dumps(r))
PY
