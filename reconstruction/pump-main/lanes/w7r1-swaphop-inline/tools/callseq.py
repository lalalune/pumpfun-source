#!/usr/bin/env python3
# callseq.py X.ll [...]: llc each, map call relocations to census callee names (via base), compare with original call order
import sys,os,subprocess,json,difflib,tempfile,re,pickle
OB=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-swaphop-inline')
def llc_calls(ll):
    d=tempfile.mkdtemp(dir=O+'/tmp')
    r=subprocess.run([OB+'/llc','-O3','-mattr=+store-imm,+jmp-ext','-relocation-model=pic','-function-sections','-data-sections','-filetype=obj',ll,'-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: print(r.stderr[-1500:]); return None,None
    rel=subprocess.run([OB+'/llvm-readelf','-rW',d+'/m.o'],capture_output=True,text=True).stdout
    sec=None; out=[]
    for l in rel.splitlines():
        m=re.match(r"Relocation section '\.rel\.text\.(\S+)'",l)
        if m: sec=m.group(1); continue
        if sec and '8swap_hop17h' in sec:
            p=l.split()
            if len(p)>=5 and p[2]=='R_SBF_64_32' and p[4]!='abort': out.append((int(p[0],16),p[4]))
    hd=subprocess.run([OB+'/llvm-objdump','-h',d+'/m.o'],capture_output=True,text=True).stdout
    size=next(int(l.split()[2],16) for l in hd.splitlines() if '.text.' in l and '8swap_hop17h' in l and '.rel' not in l)
    subprocess.run(['rm','-rf',d])
    return out,size
cen=json.load(open(O+'/census_base.json'))['targets'][0]
orig=[x['callee'] for x in cen['orig_sequence']]; ours=[x['callee'] for x in cen['our_sequence']]
mp=O+'/symmap.json'
if not os.path.exists(mp):
    calls,_=llc_calls(O+'/ir/base/sh.ll')
    assert len(calls)==len(ours),(len(calls),len(ours))
    m={}
    for (off,sym),nm in zip(calls,ours):
        assert m.get(sym,nm)==nm,(sym,nm,m.get(sym)); m[sym]=nm
    json.dump(m,open(mp,'w'))
m=json.load(open(mp))
for ll in sys.argv[1:]:
    calls,size=llc_calls(ll)
    if calls is None: continue
    seq=[m.get(s,'?'+s[:40]) for _,s in calls]
    sm=difflib.SequenceMatcher(None,orig,seq,autojunk=False)
    bad=[(op,i1,i2,j1,j2) for op,i1,i2,j1,j2 in sm.get_opcodes() if op!='equal']
    print(f'{os.path.basename(ll)}: size {size} calls {len(seq)} aligned {sum(b-a for o,a,b,_,_ in sm.get_opcodes() if o=="equal")} diffs', [(op,i1,i2,j1,j2, [x[-25:] for x in orig[i1:i2]], [x[-25:] for x in seq[j1:j2]]) for op,i1,i2,j1,j2 in bad])
