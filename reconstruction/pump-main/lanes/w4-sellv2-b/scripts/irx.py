#!/usr/bin/env python3
"""irx.py <name> [edit.py|-] [llc args]: apply edit(text)->text to base IR (IRBASE), llc it, diff sell_v2 vs original window."""
import sys,subprocess,re,os,runpy,difflib
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-sellv2-b')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
ORIG='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w4-sellv2-b/reconstruction/base/original.so'
SYM=os.environ.get('SYM','_ZN14pump_recovered14pump_recovered7sell_v217hfaf9221fd7330570E')
def norm(s):
    s=re.sub(r'call -?0x[0-9a-f]+','call X',s); s=re.sub(r'lddw (r\d+), -?0x[0-9a-f]+',r'lddw \1, X',s); return s
def objfn(path,start,size):
    r=subprocess.run([SDK+'/llvm/bin/llvm-objdump','-d','--no-show-raw-insn','--no-leading-addr',f'--start-address={start:#x}',f'--stop-address={start+size:#x}',path],capture_output=True,text=True).stdout
    L=[]
    for l in r.splitlines():
        l=l.strip()
        if not l or l.endswith(':') or 'file format' in l or 'Disassembly' in l: continue
        l=re.sub(r' <[^>]*>','',l); L.append(norm(l))
    return L
def symfn(path,sym):
    r=subprocess.run([SDK+'/llvm/bin/llvm-readelf','-sW',path],capture_output=True,text=True).stdout
    for l in r.splitlines():
        p=l.split()
        if len(p)>=8 and p[7]==sym: return int(p[1],16),int(p[2])
    raise SystemExit('sym not found')
if __name__=='__main__':
    name=sys.argv[1]; edit=sys.argv[2] if len(sys.argv)>2 else '-'
    base=os.environ.get('IRBASE',OUT+'/out/base/pump_recovered.ll')
    t=open(base).read()
    if edit!='-':
        ns=runpy.run_path(edit); t2=ns['edit'](t); assert t2!=t,'edit changed nothing'
    else: t2=t
    d=OUT+'/irexp/'+name; os.makedirs(d,exist_ok=True)
    open(d+'/m.ll','w').write(t2)
    r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/m.ll','-filetype=obj','-o',d+'/m.o']+sys.argv[3:],capture_output=True,text=True)
    if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
    a,sz=symfn(d+'/m.o',SYM); c=objfn(d+'/m.o',a,sz)
    o=objfn(ORIG,0x144508,13976)
    open(d+'/fn.txt','w').write('\n'.join(c)+'\n')
    if os.environ.get('RAWOFF')!='1':
        mb=lambda L:[re.sub(r'([+-]0x[0-9a-f]+)$','OFF',x) if re.match(r'(j|ja)',x) else x for x in L]
        o,c=mb(o),mb(c)
    diff=list(difflib.unified_diff(o,c,'orig','cand',n=1,lineterm=''))
    nd=sum(1 for l in diff if l[:1] in '+-' and l[:3] not in('+++','---'))
    print(f'{name}: insns orig={len(o)} cand={len(c)} difflines={nd}')
    if os.environ.get('Q')!='1': print('\n'.join(diff[:int(os.environ.get('N','80'))]))
