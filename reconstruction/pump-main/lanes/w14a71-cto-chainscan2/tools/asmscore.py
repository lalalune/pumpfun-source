#!/usr/bin/env python3
"""asmscore.py <file.s>: assemble an llc asm (cc1as, sbf, +store-imm,+jmp-ext), score admin_cto execute vs orig (rx metric)."""
import sys,os,subprocess,json
sys.argv_save=sys.argv[:]
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import importlib.util
src=open(T+'/rx.py').read(); head=src[:src.index("OUT=os.environ")]
g={}; exec(compile(head,'rxhead','exec'),g)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
s=sys.argv[1]; o=s[:-2]+'.o'
r=subprocess.run([SDK+'/clang','-cc1as','-triple','sbf','-target-feature','+store-imm','-target-feature','+jmp-ext','-filetype','obj',s,'-o',o],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=g['elf_fn'](o,g['KEEP']); orig=g['orig_window'](); rr,sd=g['metric'](cand,orig)
bs=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
print(json.dumps({'s':os.path.basename(s),'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd,'eq_main':g['mask'](g['elf_fn'](bs,g['KEEP']))==g['mask'](cand)}))
