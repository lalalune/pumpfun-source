import sys,re,collections,subprocess,os
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a05-cto-feethread/reconstruction/harness')
from elf_symbols import function_symbols
so=sys.argv[1]; b=open(so,'rb').read()
syms={a:n for a,z,n in function_symbols(b)}
fn=[(a,z) for a,z,n in function_symbols(b) if 'admin_cto7execute17h' in n][0]
od=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump')
t=subprocess.check_output([od,'-d','--no-show-raw-insn',f'--start-address={fn[0]:#x}',f'--stop-address={fn[0]+fn[1]:#x}',so],text=True)
c=collections.Counter()
for l in t.splitlines():
    m=re.match(r'^\s*([0-9a-f]+):\s+call (-?0x[0-9a-f]+|-?\d+)$',l.strip()) or re.match(r'^\s*(\d+):\s+call (\S+)',l)
    if not m: continue
    pc=int(m.group(1))*8; 
    try: tgt=pc+8+int(m.group(2),0)*8
    except: c[m.group(2)]+=1; continue
    n=syms.get(tgt,hex(tgt)); n=re.sub(r'17h[0-9a-f]{16}E$','',n); c[n[-70:]]+=1
for k,v in sorted(c.items(),key=lambda x:-x[1]): print(v,k)
