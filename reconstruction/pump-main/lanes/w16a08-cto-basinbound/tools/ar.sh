#!/bin/bash
# ar.sh <name> [llc]: auto join-restore of rx/<name>/m.ll -> rx/<name>__r (fn.bin, m.o, pei.mir copy, res.json, ares.json)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound; SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
N=$1; LLC=${2:-$SDK/llc}; A="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
S=$O/rx/$N; D=$O/rx/${N}__r; mkdir -p $D
[ -f $S/sbf.mir ] || $LLC $A $S/m.ll -stop-before=branch-folder -o $S/sbf.mir || exit 1
[ -f $S/pei.mir ] || $LLC $A $S/m.ll -stop-after=prologepilog -o $S/pei.mir || exit 1
cp -f $S/pei.mir $D/pei.mir
python3 $O/t2/ares.py $S/sbf.mir $D/r.mir > $D/ares.json || exit 1
$LLC $A $D/r.mir -start-before=branch-folder -filetype=obj -o $D/m.o || exit 1
python3 - $D <<'PY'
import sys,os,json; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound/t2'); import oracle,subprocess,relab as R
d=sys.argv[1]; c=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(c); rr,sd=oracle.metric(c,oracle.orig_window())
o=subprocess.run([os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump'),'-dr','--no-show-raw-insn',d+'/m.o'],capture_output=True,text=True).stdout
pos=None
for l in o.split('\n'):
    if 'admin_cto_sharing_config' in l: pos=l.split(':')[0].strip(); break
r={'name':os.path.basename(d),'ratio':round(rr,5),'bytes':len(c),'slots_diff':sd,'M':R.M(c),'share_call':pos,'ares':json.load(open(d+'/ares.json'))}
print(json.dumps(r)); open(d+'/res.json','w').write(json.dumps(r))
PY
