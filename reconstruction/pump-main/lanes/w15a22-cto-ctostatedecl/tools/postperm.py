#!/usr/bin/env python3
"""postperm.py <m0 post-opt m.ll> <outdir> <workers>: sweep all 720 CtoState bool declaration orders by permuting which
value is stored at st+40..45 in main's post-opt execute IR, then llc + masked metric (experiment only).
Declaration order only changes that mapping (verified: real capture of dl_mayhem == raw-IR declperm == this edit)."""
import sys,os,itertools,subprocess,json,difflib,re
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read().split('OUT=os.environ')[0]; exec(src)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
BOOLS=['mayhem','holder_reward','cashback','quote_locked','holder_enabled','fee_configurable']
VAL={'mayhem':'%30','holder_reward':'%32','cashback':'%34','quote_locked':'%qlz','holder_enabled':'%36','fee_configurable':'%26'}
GEP={40:'%38',41:'%39',42:'%40',43:'%41',44:'%43',45:'%44'}
base=open(sys.argv[1]).read()
Z='  %42 = zext i1 %quote_locked.sroa.0.0.off0 to i8\n'; assert base.count(Z)==1
base=base.replace(Z,'  %42 = getelementptr inbounds i8, ptr %st, i64 43\n').replace('store i8 %42, ptr %41','store i8 %qlz, ptr %41').replace('  store i64 %_34, ptr %37, align 8\n','  store i64 %_34, ptr %37, align 8\n  %qlz = zext i1 %quote_locked.sroa.0.0.off0 to i8\n'); outd=sys.argv[2]; nw=int(sys.argv[3]); os.makedirs(outd,exist_ok=True)
def al(o):
    a=1
    while a<8 and o%(a*2)==0: a*=2
    return a
for off,g in GEP.items():
    v=VAL[BOOLS[off-40]]; s=f'  store i8 {v}, ptr {g}, align {al(off)}\n'; assert base.count(s)==1,s
O=mask(orig_window()); MAIN=mask(elf_fn(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'),KEEP))
only=sys.argv[4].split(';') if len(sys.argv)>4 else None
def run(order):
    name=''.join(str(BOOLS.index(b)) for b in order)
    t=base
    for off,g in GEP.items():
        v=VAL[BOOLS[off-40]]; t=t.replace(f'  store i8 {v}, ptr {g}, align {al(off)}\n',f'  store i8 @@{order[off-40]}@@, ptr {g}, align {al(off)}\n')
    for b in BOOLS: t=t.replace(f'@@{b}@@',VAL[b])
    d=f'{outd}/{name}'; os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(t)
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    os.remove(d+'/m.ll')
    if r.returncode: return {'name':name,'error':r.stderr[-300:]}
    c=elf_fn(d+'/m.o',KEEP); os.remove(d+'/m.o'); open(d+'/fn.bin','wb').write(c)
    cm=mask(c); M=sum(b.size for b in difflib.SequenceMatcher(None,O,cm,autojunk=False).get_matching_blocks())
    rr,sd=metric(c,orig_window())
    return {'name':name,'order':order,'bytes':len(c),'M':M,'ratio':round(rr,5),'slots_diff':sd,'eq_main':cm==MAIN}
perms=[list(p) for p in itertools.permutations(BOOLS)]
if only: perms=[[BOOLS[int(ch)] for ch in o] for o in only]
res=open(outd+'/res.jsonl','a')
with ThreadPoolExecutor(nw) as ex:
    for r in ex.map(run,perms):
        res.write(json.dumps(r)+'\n'); res.flush(); print(r.get('name'),r.get('bytes'),r.get('M'),r.get('ratio'),r.get('slots_diff'),r.get('eq_main'),r.get('error','')[:80],flush=True)
