import re,subprocess,sys,os
TOOLS='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction'
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
cand_so=sys.argv[1]
W=[l.split() for l in subprocess.run(['python3',TOOLS+'/harness/win.py','list','--cand',cand_so],capture_output=True,text=True).stdout.splitlines() if l.startswith('0x')]
def orig(w):
    o=subprocess.run(['python3',TOOLS+'/harness/win.py','orig',w],capture_output=True,text=True).stdout
    return [l.split(None,1)[1].strip() for l in o.splitlines() if re.match(r'\s*0x[0-9a-f]+\s',l)]
def cand(a,size):
    a=int(a,16); o=subprocess.run([SDK+'/llvm/bin/llvm-objdump','-d','--no-show-raw-insn','--no-leading-addr',f'--start-address={a:#x}',f'--stop-address={a+size:#x}',cand_so],capture_output=True,text=True).stdout
    return [re.sub(r' <[^>]*>','',l.strip()) for l in o.splitlines() if l.strip() and not l.strip().endswith(':') and 'file format' not in l and 'Disassembly' not in l]
LD=re.compile(r'ldxdw (r\d+), \[r10 - (0x[0-9a-f]+)\]')
def pairs(L):
    res=[]
    for i,x in enumerate(L):
        if not x.startswith('call'): continue
        a=LD.match(L[i+1]) if i+1<len(L) else None; b=LD.match(L[i+2]) if i+2<len(L) else None
        if a and b and abs(int(a.group(2),16)-int(b.group(2),16))==8:
            res.append('T' if int(a.group(2),16)>int(b.group(2),16) else 'P')  # T: lower addr (tag, offset0) loaded first
    return res
for w in W:
    ow=w[0]; ca=w[3].split('@')[1]; cs=int(w[4][:-1])
    o=pairs(orig(ow)); c=pairs(cand(ca,cs))
    print(f'{ow} {w[-1][:45]:45} orig T={o.count("T")} P={o.count("P")} | cand T={c.count("T")} P={c.count("P")}')
