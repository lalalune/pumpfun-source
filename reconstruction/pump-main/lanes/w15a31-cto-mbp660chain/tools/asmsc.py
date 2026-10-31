#!/usr/bin/env python3
"""asmsc.py <file.s> <outdir>: assemble an llc asm (cc1as sbf +store-imm,+jmp-ext), write fn.bin, score like mirx (ratio, bytes, M)."""
import sys,os,subprocess,json,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
s,d=sys.argv[1:3]; os.makedirs(d,exist_ok=True); o=d+'/m.o'
r=subprocess.run([SDK+'/clang','-cc1as','-triple','sbf','-target-feature','+store-imm','-target-feature','+jmp-ext','-filetype','obj',s,'-o',o],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=oracle.elf_fn(o,oracle.KEEP); open(d+'/fn.bin','wb').write(cand)
O=oracle.orig_window(); M=sum(b.size for b in difflib.SequenceMatcher(None,oracle.mask(O),oracle.mask(cand),autojunk=False).get_matching_blocks())
rr,sd=oracle.metric(cand,O); print(json.dumps({'s':os.path.basename(s),'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd,'M':M}))
